# Install all dependencies
install:
	make python-install
	cd back && npm install

# Add python environment
python-install:
	cd back/agent && \
	python3 -m venv .venv && \
	source .venv/bin/activate && \
	pip install -r requirements.txt
	
# Python lint and format (chat-bot)
lint-python:
	cd back/agent && \
	source .venv/bin/activate && \
	ruff check . && \
	pylint .
format-python:
	cd back/agent && \
	source .venv/bin/activate && \
	ruff format .

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

