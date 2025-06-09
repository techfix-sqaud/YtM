FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies (optional but recommended for SSL, etc.)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app code
COPY src/ .

# Make sure Flask sees the right environment
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Expose the port
EXPOSE 5000

# Run the Flask app
CMD ["flask", "run"]
