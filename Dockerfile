FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for FPDF sometimes, though usually pure python)
# RUN apt-get update && apt-get install -y build-essential

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app/ app/
COPY templates/ templates/
COPY static/ static/
# Copy root level files if needed (like Procfile or config scripts, though Procfile not needed with CMD)
COPY run.py .

# Expose the port
ENV PORT=8000
EXPOSE 8000

# Run the application using the python wrapper script to handle PORT env var safely
CMD ["python", "run.py"]
