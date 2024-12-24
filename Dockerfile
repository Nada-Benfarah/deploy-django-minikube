FROM python:3.11.2-alpine3.17

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Copy requirements file
COPY ./requirements.txt /requirements.txt

# Install dependencies
RUN apk add --update --no-cache \
    mysql-client \
    build-base \
    mysql-dev \
    musl-dev \
    zlib \
    zlib-dev \
    linux-headers && \
    python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /requirements.txt

# Copy scripts and set permissions
COPY ./scripts /scripts
RUN chmod -R +x /scripts

# Update PATH
ENV PATH="/scripts:/py/bin:$PATH"

# Copy application code
COPY ./app /app
WORKDIR /app

# Expose port 80
EXPOSE 80

# Set default command
CMD ["/scripts/run.sh"]
