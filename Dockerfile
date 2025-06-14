# Use official Python image
FROM python:3.10-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y tesseract-ocr poppler-utils && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
ENV PORT=10000
EXPOSE 10000

# Run the app
CMD ["python", "app.py"]
