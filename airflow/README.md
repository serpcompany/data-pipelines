# Apache Airflow for Boxing Data Pipeline

## 📁 Directory Structure
```
airflow/
├── docker/                 # Docker setup files
│   ├── docker compose.yml  # Docker services configuration
│   ├── .env                # Environment variables
│   └── setup.sh            # Initial setup script
├── dags/                   # Your pipeline definitions
│   ├── boxing_pipeline_docker.py
│   ├── boxing_etl_dag.py
│   ├── boxing_scraping_dag.py
│   └── test_dag.py
├── logs/                   # Task execution logs
├── plugins/                # Custom Airflow plugins
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites
1. Install Docker Desktop for Mac: https://www.docker.com/products/docker-desktop/
2. Make sure Docker is running (whale icon in menu bar)

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
docker compose --env-file .env up -d

# Check status
docker compose ps
```

### Access Airflow UI
- URL: http://localhost:8080
- Username: `admin`
- Password: `admin123`

### Stop Airflow
```bash
# From the docker directory
cd /Users/devin/repos/projects/data-pipelines/airflow/docker

# Stop services
docker compose down
```

## 📊 Your DAGs (Pipelines)

| DAG Name | Description | Schedule |
|----------|-------------|----------|
| `boxing_pipeline_docker` | Main boxing data pipeline | Manual |
| `boxing_etl_dag` | ETL from data lake to staging | Daily |
| `boxing_scraping_dag` | Web scraping from BoxRec | Daily |
| `test_dag` | Simple test pipeline | Manual |

## 🎯 How to Run a Pipeline

1. Open http://localhost:8080
2. Login with admin/admin123
3. Click on a DAG name
4. Click the Play button (▶️)
5. Click "Trigger DAG"
6. Watch tasks turn green as they complete

## 🔧 Common Commands

All commands should be run from the docker directory:
```bash
cd /Users/devin/repos/projects/data-pipelines/airflow/docker
```

### Check Status
```bash
docker compose ps
```

### View Logs
```bash
# All logs
docker compose logs -f

# Specific service
docker compose logs -f airflow-scheduler
```

### Restart Services
```bash
docker compose restart
```

### Run DAG via CLI
```bash
docker compose exec airflow-webserver airflow dags trigger boxing_pipeline_docker
```

### List DAGs
```bash
docker compose exec airflow-webserver airflow dags list
```

## ❗ Troubleshooting

### Docker Not Running
- Open Docker Desktop app
- Wait for whale icon in menu bar

### Can't Access UI
- Check Docker is running: `docker compose ps`
- Check logs: `docker compose logs airflow-webserver`
- Make sure port 8080 isn't in use

### DAGs Not Showing
- Check files are in `airflow/dags/`
- Wait 30 seconds for refresh
- Check for errors: `docker compose exec airflow-webserver airflow dags list-import-errors`

### Reset Everything
```bash
cd /Users/devin/repos/projects/data-pipelines/airflow/docker
docker compose down -v
./setup.sh
docker compose --env-file .env up -d
```

## 📝 Configuration

### Environment Variables
Edit `airflow/docker/.env` to change:
- Admin username/password
- Python packages
- Database credentials

### Add New DAGs
1. Create Python file in `airflow/dags/`
2. Wait 30 seconds for auto-refresh
3. Check UI for new DAG

## 🏗️ Architecture

- **PostgreSQL**: Metadata database
- **Webserver**: UI on port 8080
- **Scheduler**: Executes DAGs
- **LocalExecutor**: Runs tasks in parallel

## 📦 What Was Cleaned Up

Removed standalone-only files:
- ❌ airflow.cfg (standalone config)
- ❌ airflow.db (SQLite database)
- ❌ start_airflow.sh (standalone script)
- ❌ init_airflow.sh (standalone init)
- ❌ generate_secrets.py (not needed)
- ❌ Old .env file

Everything is now Docker-based for consistency!