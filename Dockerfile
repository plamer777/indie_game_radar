# Use official slim image
FROM python:3.13-slim

# set workdir
WORKDIR /app

# avoid generating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install apt deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    curl \
    redis \
    && rm -rf /var/lib/apt/lists/*

# We'll use pip here - adapt if you use poetry
RUN pip install --upgrade pip
# If you use poetry, install it and run poetry install --no-dev --no-root (or appropriate)
# For a plain requirements.txt flow, just pip install.
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# copy app
COPY . /app

# Expose application port (adjust if necessary)
EXPOSE 8000

# default start command: adjust module path as per your repo
CMD ["python", "main.py"]
