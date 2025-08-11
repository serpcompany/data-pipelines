#!/bin/bash

echo "Setting up Airflow with Docker..."
echo "================================"

# Get current user ID
export AIRFLOW_UID=$(id -u)
echo "Using UID: $AIRFLOW_UID"

# Create necessary directories
echo "Creating directories..."
mkdir -p ../logs ../plugins

# Set permissions
echo "Setting permissions..."
chmod -R 777 ../logs
chmod -R 777 ../dags
chmod -R 777 ../plugins

# Load environment variables
echo "Loading environment variables..."
export $(cat .env | grep -v '^#' | xargs)

# Initialize Airflow database
echo "Initializing Airflow..."
docker compose --env-file .env up airflow-init

echo "================================"
echo "Setup complete!"
echo ""
echo "To start Airflow, run:"
echo "  cd airflow/docker"
echo "  docker compose --env-file .env up -d"
echo ""
echo "Then access the web UI at:"
echo "  http://localhost:8080"
echo ""
echo "Login credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "To stop Airflow:"
echo "  docker compose down"