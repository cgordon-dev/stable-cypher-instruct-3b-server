# Stable Cypher Instruct 3B - Offline LLama.cpp Deployment

A production-ready containerized deployment solution for the **stable-cypher-instruct-3b** model using llama.cpp, designed for offline, air-gapped environments with comprehensive monitoring and automation.

## 🎯 Overview

This solution provides:
- **Offline deployment** with no external dependencies or telemetry
- **CPU and GPU** inference configurations
- **Full observability** with Prometheus and Grafana
- **Production-ready** Docker Compose and Swarm orchestration
- **Automated deployment** with comprehensive validation

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Server    │───▶│   Llama Server   │───▶│   Model File    │
│   (FastAPI)     │    │   (llama.cpp)    │    │   (.gguf)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌──────────────────┐
│   Prometheus    │    │     Grafana      │
│   (Metrics)     │    │   (Dashboard)    │
└─────────────────┘    └──────────────────┘
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

- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

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

### Log Analysis

```bash
# API server logs
docker-compose logs api-server

# Llama server logs
docker-compose logs llama-server-cpu

# All logs with timestamps
docker-compose logs -t -f
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