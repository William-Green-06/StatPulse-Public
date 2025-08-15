# Use Playwright Python image with all dependencies preinstalled
FROM mcr.microsoft.com/playwright/python:latest

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . .

# Expose port
EXPOSE 10000

# Run the app with Gunicorn
CMD ["gunicorn", "app.main:app", "-b", "0.0.0.0:10000", "-w", "1"]
