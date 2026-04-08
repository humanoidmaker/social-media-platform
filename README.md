# Social Media Platform - Social Media Platform

A full-featured social media platform built with React 18, TypeScript, and modern tooling.

## Architecture

- **frontend/** - Main social media app (port 3000)
- **frontend-admin/** - Admin panel (port 3001)
- **Infrastructure** - Docker, Kubernetes, scripts

## Tech Stack

### Frontend
- React 18 + TypeScript
- Vite build tool
- TailwindCSS + shadcn/ui
- Framer Motion animations
- Recharts for analytics
- emoji-mart for emoji picker
- WebSocket for real-time messaging

### Infrastructure
- PostgreSQL - primary database
- Redis - caching & pub/sub
- MinIO - object storage (S3-compatible)
- Mailhog - email testing
- Celery - async task processing

## Quick Start

```bash
# Start all services
make up

# Seed admin user
make seed-admin

# Seed sample data
make seed-data

# Run tests
make test
```

## Ports

| Service | Port |
|---------|------|
| Frontend | 3000 |
| Admin Panel | 3001 |
| Backend API | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| MinIO | 9000/9001 |
| Mailhog | 8025 |


## Deployment

### Docker Compose (Easiest)

```bash
# Clone the repository
git clone https://github.com/humanoidmaker/social-media-platform.git
cd social-media-platform

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### PM2 (Production Process Manager)

```bash
# Install PM2 globally
npm install -g pm2

# Install dependencies
cd backend && pip install -r requirements.txt && cd ..
cd frontend && npm install && cd ..

# Start all services
pm2 start ecosystem.config.js

# Monitor
pm2 monit

# View logs
pm2 logs

# Stop all
pm2 stop all

# Auto-restart on reboot
pm2 startup
pm2 save
```

### Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get pods -n social-media-platform

# View logs
kubectl logs -f deployment/backend -n social-media-platform

# Scale
kubectl scale deployment/backend --replicas=3 -n social-media-platform
```

### Manual Setup

**1. Database:**
```bash
# Start PostgreSQL
pg_ctl start
```

**2. Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv/Scripts/activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database URL and secrets


uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**3. Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**4. Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## License

MIT License — Copyright (c) 2026 Humanoid Maker (www.humanoidmaker.com)
