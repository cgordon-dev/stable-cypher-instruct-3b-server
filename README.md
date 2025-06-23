# Stable Cypher Instruct 3B - Offline LLama.cpp Deployment

A production-ready containerized deployment solution for the **stable-cypher-instruct-3b** model using llama.cpp, designed for offline, air-gapped environments with comprehensive monitoring and automation.

## 🎯 Overview

This solution provides:
- **Interactive Web UI** for generating Cypher queries with real-time metrics
- **Offline deployment** with no external dependencies or telemetry
- **CPU and GPU** inference configurations
- **Full observability** with Prometheus and Grafana
- **Production-ready** Docker Compose and Swarm orchestration
- **Automated deployment** with comprehensive validation

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web UI        │───▶│   API Server     │───▶│   Llama Server  │───▶│   Model File    │
│   (Flask+JS)    │    │   (FastAPI)      │    │   (llama.cpp)   │    │   (.gguf)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Prometheus    │    │     Grafana      │    │  Metrics/Health  │
│   (Metrics)     │    │   (Dashboard)    │    │   (Real-time)    │
└─────────────────┘    └──────────────────┘    └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Ubuntu 22.04** (or compatible Linux distribution)
- **Docker** and **Docker Compose** installed
- **NVIDIA Docker runtime** (for GPU deployment)
- **8GB+ RAM** recommended
- **50GB+ disk space** for models and containers

### 1. Initial Setup

```bash
# Clone and navigate to the project
git clone <repository-url>
cd llm-server

# Copy and configure environment
cp .env.example .env
# Edit .env with your preferred settings

# Make scripts executable
chmod +x scripts/*.sh scripts/*.py
```

### 2. CPU Deployment (Default)

```bash
# Complete CPU setup and deployment
make all

# Or step by step:
make setup-cpu    # Download model and build images
make start        # Start services
make health       # Verify deployment
```

### 3. GPU Deployment

```bash
# Set deployment mode and deploy
DEPLOYMENT_MODE=gpu make all

# Or with environment file:
echo "DEPLOYMENT_MODE=gpu" >> .env
make all
```

### 4. Verify Deployment

```bash
# Run health checks
make health

# Run memory replay tests
make test

# Open service dashboards
make open
```

## 📊 Service URLs

After successful deployment:

- **🎨 Web UI**: http://localhost:5001 (Interactive Cypher query generator)
- **🔗 API Server**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/docs
- **📈 Prometheus**: http://localhost:9090
- **📊 Grafana**: http://localhost:3000 (admin/admin)

## 🔧 Configuration

### Environment Variables

Key configurations in `.env`:

```bash
# Model and deployment
MODEL_FILENAME=stable-cypher-instruct-3b.Q4_K_M.gguf
DEPLOYMENT_MODE=cpu  # or 'gpu'

# Performance tuning
CPU_THREADS=8        # CPU threads for inference
GPU_LAYERS=32        # GPU layers (GPU mode only)
CONTEXT_SIZE=4096    # Model context window
MAX_TOKENS=512       # Maximum response tokens

# API settings
API_PORT=8000
API_KEY=             # Optional API key
LOG_LEVEL=INFO

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

### Model Parameters

Fine-tune generation behavior:

```bash
TEMPERATURE=0.7      # Creativity (0.0-2.0)
TOP_P=0.9           # Nucleus sampling (0.0-1.0)
```

## 🐳 Docker Compose Services

### Development (docker-compose.yml)

- **llama-server-cpu**: CPU-only llama.cpp server
- **llama-server-gpu**: GPU-enabled llama.cpp server
- **api-server**: FastAPI wrapper with validation
- **web-ui**: Interactive Flask web interface with real-time metrics
- **prometheus**: Metrics collection
- **grafana**: Monitoring dashboards

### Production (docker-compose.swarm.yml)

- **High availability** with service replication
- **Rolling updates** and health checks
- **Resource constraints** and placement rules
- **Overlay networking** for multi-node deployment

## 📈 Monitoring & Observability

### Prometheus Metrics

- **API performance**: Request rates, response times, error rates
- **Model performance**: Token generation rates, inference time
- **System metrics**: Memory, CPU, GPU utilization
- **Health checks**: Service availability and connectivity

### Grafana Dashboards

Pre-configured dashboards for:
- API server performance
- Model inference metrics
- Token generation statistics
- System resource utilization

## 🔒 Security Features

- **Air-gapped deployment** with no external dependencies
- **Container isolation** with minimal attack surface
- **Optional API key authentication**
- **No telemetry or data leakage**
- **Auditable model artifacts** (.gguf files)

## 🎨 Web UI Features

The included web interface provides:

- **🤖 Interactive Chat**: Generate Cypher queries using natural language
- **📊 Real-time Metrics**: Live performance and health monitoring
- **💾 Query Examples**: Pre-built examples for common Cypher patterns
- **⚡ WebSocket Updates**: Live metrics updates without page refresh
- **📱 Responsive Design**: Works on desktop and mobile devices

### Using the Web UI

1. **Navigate to**: http://localhost:5001
2. **Enter your query**: "Find all movies directed by Christopher Nolan"
3. **Get Cypher**: Receive optimized Cypher query instantly
4. **Monitor Performance**: View real-time generation metrics

### Example Prompts

- "Generate a Cypher query to find all Person nodes with name John"
- "Create a query to find movies acted by Tom Hanks"
- "Write a Cypher query to find users who have similar preferences"
- "Find all products in a specific category with their prices"

## 📝 API Usage

### Health Check

```bash
curl http://localhost:8000/health
```

### Generate Cypher Query

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Generate a Cypher query to find all Person nodes with name John",
    "max_tokens": 256,
    "temperature": 0.1
  }'
```

### Using Messages Format

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Create a query to find movies acted by Tom Hanks"}
    ],
    "max_tokens": 256
  }'
```

## 🛠️ Management Commands

### Service Management

```bash
make start          # Start all services
make stop           # Stop all services
make restart        # Restart all services
make logs           # View all logs
make logs-api       # View API logs only
make logs-llama     # View llama server logs only
```

### Health & Testing

```bash
make health         # Check service health
make test           # Run memory replay tests
make metrics        # Show current metrics
make status         # Show service status
```

### Docker Swarm

```bash
make deploy-swarm   # Deploy to Swarm mode
make swarm-status   # Show stack status
make swarm-logs     # View stack logs
make remove-swarm   # Remove stack
```

### Cleanup

```bash
make clean          # Clean containers and volumes
make clean-all      # Clean everything including images
```

## 🔄 Docker Swarm Production Deployment

For high-availability production deployments:

```bash
# Initialize Swarm (if not already done)
docker swarm init

# Deploy to Swarm
make deploy-swarm

# Monitor deployment
make swarm-status
```

### Swarm Features

- **Service replication** for high availability
- **Rolling updates** with zero downtime
- **Health-based routing** and failover
- **Resource management** and placement constraints
- **Overlay networking** for multi-node clusters

## 🔍 Troubleshooting

### Common Issues

**Model download fails:**
```bash
# Manual download
./scripts/download_model.sh
```

**GPU not detected:**
```bash
# Verify NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

**Services won't start:**
```bash
# Check environment
./scripts/validate_env.sh

# Check logs
make logs
```

**Memory issues:**
```bash
# Reduce context size
echo "CONTEXT_SIZE=2048" >> .env
make restart
```

**Port conflicts (5000 already in use):**
```bash
# Web UI port changed to 5001 to avoid conflicts
# Update .env file if needed:
echo "WEB_UI_PORT=5001" >> .env
make restart
```

**Docker not running:**
```bash
# Start Docker Desktop or service
sudo systemctl start docker  # Linux
# or start Docker Desktop on macOS/Windows
```

**llama.cpp build errors:**
```bash
# Modern llama.cpp uses CMake instead of Makefile
# Dockerfile automatically handles this
# If manual build needed:
cd llama.cpp
mkdir build && cd build
cmake ..
make -j$(nproc)
```

**Missing shared libraries:**
```bash
# Fixed in Dockerfile by copying .so files and setting LD_LIBRARY_PATH
# For manual debugging:
ldd /usr/local/bin/llama-server
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
```

**Web UI 500 errors:**
```bash
# Check API server status
curl http://localhost:8000/health

# Check API server logs
docker-compose logs api-server

# Common fixes:
# 1. Ensure API server is running and healthy
# 2. Check middleware configuration
# 3. Verify response format matches expected structure
```

**API 422 validation errors:**
```bash
# Fixed by bypassing Pydantic validation for responses
# If still occurring, check request format:
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", "max_tokens": 50}'
```

**SocketIO connection errors:**
```bash
# Check web UI logs
docker-compose logs web-ui

# Verify SocketIO parameters - broadcast=True was removed
# Connection should work on http://localhost:5001
```

### Log Analysis

```bash
# API server logs
docker-compose logs api-server

# Llama server logs
docker-compose logs llama-server-cpu

# Web UI logs
docker-compose logs web-ui

# All logs with timestamps
docker-compose logs -t -f

# Follow specific service logs
docker-compose logs -f api-server
```

### Performance Tuning

**CPU Optimization:**
- Increase `CPU_THREADS` for faster inference
- Reduce `CONTEXT_SIZE` to lower memory usage
- Use `TEMPERATURE=0.1` for deterministic output

**GPU Optimization:**
- Adjust `GPU_LAYERS` based on VRAM
- Monitor GPU utilization in Grafana
- Use larger batch sizes for throughput

### Known Working Configuration

**Tested Environment:**
- macOS with Docker Desktop
- Ubuntu 22.04 with Docker CE
- Model: stable-cypher-instruct-3b.Q4_K_M.gguf (1.6GB)
- Web UI Port: 5001 (changed from 5000 to avoid conflicts)
- All services healthy and operational

**Service Health Check:**
```bash
# Quick health verification
curl http://localhost:8000/health
curl http://localhost:5001/api/health
curl http://localhost:9090/-/healthy
```

## 📦 Model Information

**Model**: stable-cypher-instruct-3b.Q4_K_M.gguf
- **Size**: ~2.0GB (quantized)
- **Parameters**: 3 billion
- **Specialization**: Cypher query generation for Neo4j
- **Quantization**: Q4_K_M for balanced performance/quality

The model excels at generating Cypher queries from natural language descriptions and beats SOTA models like GPT-4 at Cypher generation tasks.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [llama.cpp](https://github.com/ggerganov/llama.cpp) for the inference engine
- [Stability AI](https://huggingface.co/stabilityai/stable-code-instruct-3b) for the base model
- [Neo4j Labs](https://github.com/neo4j-labs/text2cypher) for the training dataset