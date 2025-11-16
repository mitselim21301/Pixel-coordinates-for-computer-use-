.PHONY: help install install-dev install-gpu test lint format calibrate run clean build publish docker

# Default target
.DEFAULT_GOAL := help

# Python interpreter
PYTHON := python3
PIP := $(PYTHON) -m pip

# Project info
PROJECT_NAME := mcp-accurate-click-server
SRC_DIR := src
TEST_DIR := tests

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install core dependencies
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	@echo "✓ Core dependencies installed"

install-dev: ## Install development dependencies
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .
	pre-commit install
	@echo "✓ Development environment ready"

install-gpu: ## Install with GPU support
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements-gpu.txt
	$(PIP) install -e .
	@echo "✓ GPU-enabled installation complete"

install-editable: ## Install in editable mode
	$(PIP) install -e .
	@echo "✓ Installed in editable mode"

test: ## Run test suite
	pytest $(TEST_DIR) -v --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html

test-fast: ## Run tests without coverage
	pytest $(TEST_DIR) -v

test-integration: ## Run integration tests only
	pytest $(TEST_DIR) -v -m integration

test-unit: ## Run unit tests only
	pytest $(TEST_DIR) -v -m "not integration"

test-parallel: ## Run tests in parallel
	pytest $(TEST_DIR) -v -n auto

lint: ## Run linters (ruff, black check, mypy)
	@echo "Running ruff..."
	ruff check $(SRC_DIR) $(TEST_DIR)
	@echo "Running black (check only)..."
	black --check $(SRC_DIR) $(TEST_DIR)
	@echo "Running mypy..."
	mypy $(SRC_DIR)
	@echo "✓ All linters passed"

format: ## Format code with black and ruff
	@echo "Formatting with black..."
	black $(SRC_DIR) $(TEST_DIR)
	@echo "Fixing with ruff..."
	ruff check --fix $(SRC_DIR) $(TEST_DIR)
	@echo "✓ Code formatted"

type-check: ## Run type checking with mypy
	mypy $(SRC_DIR)

calibrate: ## Run calibration workflow
	$(PYTHON) scripts/calibrate.sh

run: ## Start MCP server
	$(PYTHON) scripts/start_server.sh

run-debug: ## Start MCP server with debug logging
	MCP_DEBUG=1 $(PYTHON) -m mcp_accurate_click.server --log-level debug

clean: ## Clean build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "✓ Cleaned build artifacts"

build: clean ## Build distribution packages
	$(PYTHON) -m build
	@echo "✓ Build complete - packages in dist/"

publish-test: build ## Publish to TestPyPI
	$(PYTHON) -m twine upload --repository testpypi dist/*

publish: build ## Publish to PyPI
	$(PYTHON) -m twine upload dist/*

docker-build: ## Build Docker image
	docker build -t $(PROJECT_NAME):latest -f docker/Dockerfile .

docker-build-gpu: ## Build Docker image with GPU support
	docker build -t $(PROJECT_NAME):gpu -f docker/Dockerfile.gpu .

docker-run: ## Run Docker container
	docker-compose up

docker-stop: ## Stop Docker container
	docker-compose down

docker-shell: ## Open shell in Docker container
	docker run -it --rm $(PROJECT_NAME):latest /bin/bash

check: lint test ## Run all checks (lint + test)

pre-commit: format lint test ## Run pre-commit checks

verify: ## Verify installation
	$(PYTHON) -c "import mcp_accurate_click; print('✓ Package imported successfully')"
	mcp-accurate-click --version

benchmark: ## Run performance benchmarks
	$(PYTHON) -m pytest tests/benchmarks/ -v --benchmark-only

coverage-report: ## Generate and open coverage report
	pytest $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html
	@echo "Opening coverage report..."
	@which open > /dev/null && open htmlcov/index.html || \
	 which xdg-open > /dev/null && xdg-open htmlcov/index.html || \
	 echo "Please open htmlcov/index.html manually"

docs: ## Build documentation
	cd docs && make html
	@echo "✓ Documentation built - open docs/_build/html/index.html"

docs-serve: ## Serve documentation locally
	cd docs && make html && python -m http.server 8000 --directory _build/html

init-dev: install-dev ## Initialize development environment
	@echo "✓ Development environment initialized"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run 'make test' to verify installation"
	@echo "  2. Run 'make calibrate' to calibrate your system"
	@echo "  3. Run 'make run' to start the MCP server"
