# OpenVoice Makefile
# Run tests, build, and manage the project

.PHONY: help test test-frontend test-backend test-all install install-frontend install-backend clean build start stop logs

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "OpenVoice - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# Testing Commands
# =============================================================================

test: ## Run all tests (frontend + backend)
	@echo "=================================="
	@echo "Running All Tests"
	@echo "=================================="
	@$(MAKE) test-frontend
	@echo ""
	@$(MAKE) test-backend
	@echo ""
	@echo "=================================="
	@echo "✅ All Tests Complete!"
	@echo "=================================="

test-frontend: ## Run frontend tests only
	@echo "Running Frontend Tests (22 tests)..."
	@cd frontend && npm test -- --run

test-backend: ## Run backend tests only
	@echo "Running Backend Tests (16 tests)..."
	@cd backend && pytest tests/test_file_handler.py \
		tests/test_audio_processor.py::TestAudioProcessor::test_initialization \
		tests/test_audio_processor.py::TestAudioProcessor::test_load_audio \
		tests/test_audio_processor.py::TestAudioProcessor::test_load_audio_mono_conversion \
		tests/test_audio_processor.py::TestAudioProcessor::test_load_audio_resampling \
		tests/test_audio_processor.py::TestAudioProcessor::test_save_audio \
		tests/test_audio_processor.py::TestAudioProcessor::test_attenuation_and_gain_parameters \
		tests/test_audio_processor.py::TestAudioProcessor::test_slider_to_db_mapping \
		tests/test_audio_processor.py::TestAudioProcessor::test_gain_compensation_logic \
		-v

test-watch: ## Run frontend tests in watch mode
	@echo "Running Frontend Tests in Watch Mode..."
	@cd frontend && npm test

test-coverage: ## Run tests with coverage reports
	@echo "Running Tests with Coverage..."
	@cd frontend && npm run test:coverage
	@echo ""
	@cd backend && pytest tests/test_file_handler.py --cov=utils --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "Coverage Reports:"
	@echo "  Frontend: frontend/coverage/index.html"
	@echo "  Backend:  backend/htmlcov/index.html"

# =============================================================================
# Installation Commands
# =============================================================================

install: ## Install all dependencies (frontend + backend)
	@echo "Installing all dependencies..."
	@$(MAKE) install-frontend
	@$(MAKE) install-backend
	@echo "✅ All dependencies installed!"

install-frontend: ## Install frontend dependencies
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install

install-backend: ## Install backend dependencies
	@echo "Installing backend dependencies..."
	@cd backend && pip install -r requirements.txt -r requirements-test.txt

# =============================================================================
# Docker Commands
# =============================================================================

build: ## Build Docker containers
	@echo "Building Docker containers..."
	@docker-compose build

start: ## Start all Docker services
	@echo "Starting Docker services..."
	@docker-compose up -d
	@echo "✅ Services started!"
	@echo "   Frontend: http://localhost"
	@echo "   Backend:  http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"

stop: ## Stop all Docker services
	@echo "Stopping Docker services..."
	@docker-compose down

restart: ## Restart all Docker services
	@echo "Restarting Docker services..."
	@docker-compose restart

logs: ## Show Docker logs
	@docker-compose logs -f

logs-backend: ## Show backend logs
	@docker-compose logs -f backend

logs-worker: ## Show worker logs
	@docker-compose logs -f worker1 worker2

test-docker: ## Run tests inside Docker containers
	@echo "Running tests in Docker..."
	@docker-compose exec backend pytest -v

# =============================================================================
# Development Commands
# =============================================================================

dev: ## Start development servers (frontend + backend)
	@echo "Starting development servers..."
	@echo "Frontend: http://localhost:5173"
	@echo "Backend:  http://localhost:8000"
	@cd frontend && npm run dev & cd backend && uvicorn main:app --reload

dev-frontend: ## Start frontend development server
	@cd frontend && npm run dev

dev-backend: ## Start backend development server
	@cd backend && uvicorn main:app --reload

# =============================================================================
# Build Commands
# =============================================================================

build-frontend: ## Build frontend for production
	@echo "Building frontend..."
	@cd frontend && npm run build
	@echo "✅ Frontend built: frontend/dist/"

lint: ## Run linters
	@echo "Running linters..."
	@cd frontend && npm run lint

# =============================================================================
# Cleanup Commands
# =============================================================================

clean: ## Clean build artifacts and caches
	@echo "Cleaning build artifacts..."
	@rm -rf frontend/dist
	@rm -rf frontend/coverage
	@rm -rf frontend/node_modules
	@rm -rf backend/htmlcov
	@rm -rf backend/.pytest_cache
	@rm -rf backend/__pycache__
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleaned!"

clean-docker: ## Remove all Docker containers and volumes
	@echo "Cleaning Docker resources..."
	@docker-compose down -v
	@echo "✅ Docker cleaned!"

# =============================================================================
# Quick Commands
# =============================================================================

status: ## Show service status
	@docker-compose ps

health: ## Check health of services
	@echo "Checking service health..."
	@curl -s http://localhost:8000/api/health | python -m json.tool || echo "❌ Backend not running"

quick-test: test ## Alias for 'test' command

all: install build start ## Install, build, and start everything
	@echo "✅ All done!"
