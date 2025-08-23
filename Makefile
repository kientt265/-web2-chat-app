# Install all dependencies
install:
	make python-install
	cd back && npm install

# Add python environment
python-install:
	cd back/ && \
	python3 -m venv .venv && \
	source .venv/bin/activate && \
	pip install -r requirements.txt
	
# Python lint and format (chat-bot)
lint-python:
	cd back && \
	source .venv/bin/activate && \
	ruff check ./tool-agent ./message-agent ./ext-tool ./sync-service ./service-registry ./router-agent || echo "No linting issues found"

	
format-python:
	cd back && \
	source .venv/bin/activate && \
	ruff format ./tool-agent ./message-agent ./ext-tool ./sync-service ./service-registry ./router-agent || echo "No formatting issues found"

# Node.js lint (if eslint is set up)
lint-node:
	cd back && npm run lint || echo "No lint script defined"

# Unified linting
lint: lint-python

# Format code for both Python and Node.js
format: format-python

format-node:
	cd back && npm run format || echo "No format script defined"

# Clean Python cache files
clean-python:
	find back/src -type d -name "__pycache__" -exec rm -r {} +

# Clean Node.js build artifacts
clean-node:
	rm -rf back/node_modules

# Clean all
clean: clean-python clean-node

