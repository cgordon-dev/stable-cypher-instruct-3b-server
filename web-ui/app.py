from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import requests
import json
import time
import uuid
from datetime import datetime
import threading
import os
from prometheus_client.parser import text_string_to_metric_families

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

class Config:
    API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000')
    PROMETHEUS_URL = os.environ.get('PROMETHEUS_URL', 'http://localhost:9090')
    METRICS_URL = os.environ.get('METRICS_URL', 'http://localhost:8000/metrics')
    UPDATE_INTERVAL = int(os.environ.get('UPDATE_INTERVAL', '5'))

config = Config()

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
    
    def health_check(self):
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def chat_completion(self, prompt, max_tokens=512, temperature=0.7, top_p=0.9):
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

class MetricsCollector:
    def __init__(self, metrics_url, prometheus_url):
        self.metrics_url = metrics_url
        self.prometheus_url = prometheus_url
        self.session = requests.Session()
        self.session.timeout = 10
    
    def get_prometheus_metrics(self):
        try:
            response = self.session.get(self.metrics_url)
            response.raise_for_status()
            
            metrics = {}
            for family in text_string_to_metric_families(response.text):
                for sample in family.samples:
                    metric_name = sample.name
                    labels = sample.labels
                    value = sample.value
                    
                    if metric_name not in metrics:
                        metrics[metric_name] = []
                    
                    metrics[metric_name].append({
                        'labels': labels,
                        'value': value,
                        'timestamp': time.time()
                    })
            
            return metrics
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def get_summary_metrics(self):
        raw_metrics = self.get_prometheus_metrics()
        
        if "error" in raw_metrics:
            return raw_metrics
        
        summary = {
            'requests_total': 0,
            'active_requests': 0,
            'avg_response_time': 0,
            'tokens_generated_total': 0,
            'avg_tokens_per_second': 0,
            'generation_duration_avg': 0,
            'health_status': 'unknown',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Extract key metrics
        if 'api_requests_total' in raw_metrics:
            summary['requests_total'] = sum(m['value'] for m in raw_metrics['api_requests_total'])
        
        if 'api_active_requests' in raw_metrics:
            values = [m['value'] for m in raw_metrics['api_active_requests']]
            summary['active_requests'] = values[0] if values else 0
        
        if 'llama_tokens_generated_total' in raw_metrics:
            summary['tokens_generated_total'] = sum(m['value'] for m in raw_metrics['llama_tokens_generated_total'])
        
        if 'llama_tokens_per_second' in raw_metrics:
            values = [m['value'] for m in raw_metrics['llama_tokens_per_second'] if m['labels'].get('le') == '+Inf']
            summary['avg_tokens_per_second'] = values[0] if values else 0
        
        # Check API health
        try:
            health_response = self.session.get(f"{config.API_BASE_URL}/health")
            summary['health_status'] = 'healthy' if health_response.status_code == 200 else 'unhealthy'
        except:
            summary['health_status'] = 'unhealthy'
        
        return summary

api_client = APIClient(config.API_BASE_URL)
metrics_collector = MetricsCollector(config.METRICS_URL, config.PROMETHEUS_URL)

def background_metrics_updater():
    while True:
        try:
            metrics = metrics_collector.get_summary_metrics()
            socketio.emit('metrics_update', metrics)
            time.sleep(config.UPDATE_INTERVAL)
        except Exception as e:
            print(f"Error updating metrics: {e}")
            time.sleep(config.UPDATE_INTERVAL)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify(api_client.health_check())

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    prompt = data.get('prompt', '')
    max_tokens = data.get('max_tokens', 512)
    temperature = data.get('temperature', 0.7)
    top_p = data.get('top_p', 0.9)
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    # Store chat in session
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    chat_id = str(uuid.uuid4())
    start_time = time.time()
    
    result = api_client.chat_completion(prompt, max_tokens, temperature, top_p)
    
    if "error" in result:
        return jsonify(result), 500
    
    end_time = time.time()
    
    chat_entry = {
        'id': chat_id,
        'prompt': prompt,
        'response': result.get('choices', [{}])[0].get('message', {}).get('content', ''),
        'timestamp': datetime.utcnow().isoformat(),
        'duration': end_time - start_time,
        'usage': result.get('usage', {}),
        'max_tokens': max_tokens,
        'temperature': temperature,
        'top_p': top_p
    }
    
    session['chat_history'].append(chat_entry)
    
    return jsonify(chat_entry)

@app.route('/api/chat/history')
def chat_history():
    return jsonify(session.get('chat_history', []))

@app.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    session['chat_history'] = []
    return jsonify({"status": "cleared"})

@app.route('/api/metrics')
def get_metrics():
    return jsonify(metrics_collector.get_summary_metrics())

@app.route('/api/examples')
def get_examples():
    examples = [
        {
            "title": "Find Person by Name",
            "prompt": "Generate a Cypher query to find all Person nodes with name 'John'",
            "category": "Basic"
        },
        {
            "title": "Actor Movies",
            "prompt": "Create a Cypher query to find all movies that an actor named 'Tom Hanks' has acted in",
            "category": "Relationships"
        },
        {
            "title": "User Preferences",
            "prompt": "Write a Cypher query to find users who have similar preferences to a given user",
            "category": "Complex"
        },
        {
            "title": "Movie Recommendations",
            "prompt": "Generate a Cypher query to recommend movies based on user ratings and genres",
            "category": "Complex"
        },
        {
            "title": "Social Network",
            "prompt": "Create a query to find friends of friends in a social network",
            "category": "Relationships"
        },
        {
            "title": "Product Categories",
            "prompt": "Write a Cypher query to find all products in a specific category with their prices",
            "category": "Basic"
        }
    ]
    return jsonify(examples)

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    # Send initial metrics
    metrics = metrics_collector.get_summary_metrics()
    emit('metrics_update', metrics)

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('request_metrics')
def handle_metrics_request():
    metrics = metrics_collector.get_summary_metrics()
    emit('metrics_update', metrics)

if __name__ == '__main__':
    # Start background metrics updater
    metrics_thread = threading.Thread(target=background_metrics_updater, daemon=True)
    metrics_thread.start()
    
    # Run the app
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)