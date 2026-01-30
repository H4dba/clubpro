FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy wait script
COPY wait-for-db.py /usr/local/bin/wait-for-db.py
RUN chmod +x /usr/local/bin/wait-for-db.py

# Create entrypoint script
RUN echo '#!/bin/bash' > /usr/local/bin/docker-entrypoint.sh && \
    echo 'set -e' >> /usr/local/bin/docker-entrypoint.sh && \
    echo 'cd /app' >> /usr/local/bin/docker-entrypoint.sh && \
    echo 'echo "Waiting for postgres..."' >> /usr/local/bin/docker-entrypoint.sh && \
    echo 'python /usr/local/bin/wait-for-db.py' >> /usr/local/bin/docker-entrypoint.sh && \
    echo 'echo "Running migrations..."' >> /usr/local/bin/docker-entrypoint.sh && \
    echo 'python manage.py migrate --noinput' >> /usr/local/bin/docker-entrypoint.sh && \
    echo 'echo "Collecting static files..."' >> /usr/local/bin/docker-entrypoint.sh && \
    echo 'python manage.py collectstatic --noinput || true' >> /usr/local/bin/docker-entrypoint.sh && \
    echo 'echo "Starting server..."' >> /usr/local/bin/docker-entrypoint.sh && \
    echo 'exec "$@"' >> /usr/local/bin/docker-entrypoint.sh && \
    chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy project
COPY . /app/

# Create directory for media files
RUN mkdir -p /app/media /app/staticfiles

# Expose port
EXPOSE 8000

# Run entrypoint script
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
