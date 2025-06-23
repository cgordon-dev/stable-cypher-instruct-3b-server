.PHONY: help build-cpu build-gpu build-api download-model validate setup-cpu setup-gpu deploy-swarm clean logs test open stop restart health

SHELL := /bin/bash
DEPLOYMENT_MODE ?= cpu
COMPOSE_FILE := docker-compose.yml
SWARM_FILE := docker-compose.swarm.yml

help: ## Show this help message
	@echo "Stable Cypher Instruct 3B - LLama.cpp Deployment"
	@echo "=================================================="
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Environment variables:"
	@echo "  DEPLOYMENT_MODE  - Set to 'cpu' or 'gpu' (default: cpu)"
	@echo ""
	@echo "Examples:"
	@echo "  make setup-cpu          # Setup for CPU-only deployment"
	@echo "  make setup-gpu          # Setup for GPU-enabled deployment"
	@echo "  make all               # Complete setup and deployment"
	@echo "  make deploy-swarm      # Deploy to Docker Swarm"

download-model: ## Download the stable-cypher-instruct-3b model
	@echo "🔄 Downloading model..."
	./scripts/download_model.sh

validate: ## Validate environment configuration
	@echo "🔍 Validating environment..."
	./scripts/validate_env.sh

build-cpu: ## Build CPU-only llama.cpp server image
	@echo "🏗️  Building CPU server image..."
	docker build --target cpu-runtime -t llama-server:cpu .

build-gpu: ## Build GPU-enabled llama.cpp server image
	@echo "🏗️  Building GPU server image..."
	docker build --target gpu-runtime -t llama-server:gpu .

build-api: ## Build API server image
	@echo "🏗️  Building API server image..."
	docker build -f Dockerfile.api -t llama-api:latest .

build-all: build-cpu build-gpu build-api ## Build all Docker images

setup-cpu: download-model build-cpu build-api ## Complete CPU setup
	@echo "✅ CPU setup complete"

setup-gpu: download-model build-gpu build-api ## Complete GPU setup
	@echo "✅ GPU setup complete"

start: validate ## Start services with docker-compose
	@echo "🚀 Starting services in $(DEPLOYMENT_MODE) mode..."
	DEPLOYMENT_MODE=$(DEPLOYMENT_MODE) docker-compose --profile $(DEPLOYMENT_MODE) up -d

stop: ## Stop all services
	@echo "🛑 Stopping services..."
	docker-compose down

restart: stop start ## Restart all services

logs: ## View logs from all services
	docker-compose logs -f

logs-api: ## View API server logs only
	docker-compose logs -f api-server

logs-llama: ## View llama server logs only
	docker-compose logs -f llama-server-$(DEPLOYMENT_MODE)

health: ## Check health of all services
	@echo "🏥 Checking service health..."
	@curl -f http://localhost:8000/health || echo "❌ API server unhealthy"
	@curl -f http://localhost:9090/api/v1/status || echo "❌ Prometheus unhealthy"
	@curl -f http://localhost:3000/api/health || echo "❌ Grafana unhealthy"

test: ## Run memory replay tests
	@echo "🧪 Running memory replay tests..."
	python3 scripts/memory_replay.py --url http://localhost:8000

open: ## Open service URLs in browser
	@echo "🌐 Opening services..."
	@command -v open >/dev/null 2>&1 && open http://localhost:8000/docs || echo "API docs: http://localhost:8000/docs"
	@command -v open >/dev/null 2>&1 && open http://localhost:9090 || echo "Prometheus: http://localhost:9090"
	@command -v open >/dev/null 2>&1 && open http://localhost:3000 || echo "Grafana: http://localhost:3000"

deploy-swarm: build-all ## Deploy to Docker Swarm
	@echo "🐝 Deploying to Docker Swarm..."
	@if ! docker node ls >/dev/null 2>&1; then \
		echo "🔧 Initializing Docker Swarm..."; \
		docker swarm init; \
	fi
	@echo "📦 Creating external volumes..."
	docker volume create prometheus_data || true
	docker volume create grafana_data || true
	@echo "🚀 Deploying stack..."
	docker stack deploy -c $(SWARM_FILE) llama-stack

swarm-logs: ## View Swarm stack logs
	docker service logs -f llama-stack_api-server

swarm-status: ## Show Swarm stack status
	docker stack services llama-stack

remove-swarm: ## Remove Swarm stack
	@echo "🗑️  Removing Swarm stack..."
	docker stack rm llama-stack

clean: ## Clean up Docker resources
	@echo "🧹 Cleaning up..."
	docker-compose down -v --remove-orphans
	docker system prune -f
	docker volume prune -f

clean-all: clean ## Clean up everything including images
	docker rmi -f $$(docker images -q llama-server:* llama-api:* 2>/dev/null) || true

all: setup-$(DEPLOYMENT_MODE) start health ## Complete setup and deployment
	@echo ""
	@echo "🎉 Deployment complete!"
	@echo ""
	@echo "Services available at:"
	@echo "  API Server:   http://localhost:8000"
	@echo "  API Docs:     http://localhost:8000/docs"
	@echo "  Prometheus:   http://localhost:9090"
	@echo "  Grafana:      http://localhost:3000 (admin/admin)"
	@echo ""
	@echo "Run 'make test' to validate the deployment"
	@echo "Run 'make open' to open services in browser"

# Development helpers
dev-cpu: ## Quick development setup (CPU)
	$(MAKE) DEPLOYMENT_MODE=cpu all

dev-gpu: ## Quick development setup (GPU)
	$(MAKE) DEPLOYMENT_MODE=gpu all

# Monitoring helpers
metrics: ## Show current metrics
	@curl -s http://localhost:8000/metrics | head -20

status: ## Show service status
	@docker-compose ps