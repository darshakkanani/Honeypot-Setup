# HoneyPort Makefile
# Automation for development, testing, and deployment

.PHONY: help install setup test lint format clean build docker-build docker-run deploy

# Default target
help:
	@echo "HoneyPort Development Commands:"
	@echo "  install     - Install dependencies"
	@echo "  setup       - Run initial setup"
	@echo "  test        - Run tests"
	@echo "  lint        - Run code linting"
	@echo "  format      - Format code"
	@echo "  clean       - Clean temporary files"
	@echo "  build       - Build application"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run  - Run with Docker Compose"
	@echo "  deploy      - Deploy to production"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Run setup script
setup:
	python scripts/setup.py

# Run tests
test:
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

# Run linting
lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	pylint core/ ai_models/ utils/ dashboard/ --rcfile=.pylintrc

# Format code
format:
	black . --line-length=100
	isort . --profile=black

# Clean temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/

# Build application
build: clean
	python setup.py sdist bdist_wheel

# Build Docker image
docker-build:
	docker build -t honeyport:latest .

# Run with Docker Compose
docker-run:
	docker-compose up -d

# Stop Docker services
docker-stop:
	docker-compose down

# Deploy to production
deploy:
	@echo "Deploying HoneyPort to production..."
	docker-compose -f docker-compose.prod.yml up -d

# Development server
dev:
	python run.py --debug

# Database migrations
migrate:
	python scripts/migrate_db.py

# Generate SSL certificates
ssl:
	openssl req -x509 -newkey rsa:4096 -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem -days 365 -nodes

# Backup data
backup:
	python scripts/backup.py

# Monitor logs
logs:
	tail -f logs/honeyport.log

# Check system health
health:
	curl -f http://localhost:5000/health || echo "Service unhealthy"
