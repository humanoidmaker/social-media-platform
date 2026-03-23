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
