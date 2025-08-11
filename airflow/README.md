# Apache Airflow for Boxing Data Pipeline


### First Time Setup
```bash
# 1. Navigate to docker directory
cd /Users/devin/repos/projects/data-pipelines/airflow/docker

# 2. Run setup script
./setup.sh

# Wait for "Setup complete!"
```

### Start Airflow
```bash
# From the docker directory
cd /Users/devin/repos/projects/data-pipelines/airflow/docker

# Start all services
docker compose up -d
```

### Access Airflow UI
- URL: http://localhost:8080
- Username: `admin`
- Password: `admin123`
