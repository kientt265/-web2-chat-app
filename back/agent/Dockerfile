# Use official Python image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port (change if your app uses a different port)
EXPOSE 3004

# Start the application (replace app.py with your entry point)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3004", "--reload"]  