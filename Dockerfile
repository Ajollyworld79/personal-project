FROM python:3.14-slim AS content
WORKDIR /build
RUN pip install --no-cache-dir 'pydantic>=2.9.2'
COPY app/ app/
COPY content/ content/
COPY scripts/export_content.py scripts/export_content.py
RUN python scripts/export_content.py > /build/public-content.json

FROM node:24-slim AS frontend
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci
COPY frontend/ frontend/
COPY scripts/prerender.mjs scripts/prerender.mjs
COPY vite.config.ts tsconfig.json ./
COPY --from=content /build/public-content.json /build/public-content.json
RUN CONTENT_FILE=/build/public-content.json npm run build

FROM python:3.14-slim

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
COPY content/ content/
COPY --from=frontend /build/static/dist/ static/dist/
# Copy root level files
COPY run.py .
COPY Procfile .

# Run as an unprivileged user: a compromised process cannot modify the app or system.
RUN useradd --create-home --uid 10001 app
USER app

# Expose the port
ENV PORT=8000
EXPOSE 8000

# Run the application using the python wrapper script to handle PORT env var safely
CMD ["python", "run.py"]
