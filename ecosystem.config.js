module.exports = {
  apps: [
    {
      name: "social-media-platform-backend",
      cwd: "./backend",
      script: "venv/bin/uvicorn",
      args: "app.main:app --host 0.0.0.0 --port 8000",
      interpreter: "venv/bin/python3",
      env: {
        DATABASE_URL: "postgresql://app_user:app_pass@localhost:5432/social_media_platform",
        REDIS_URL: "redis://localhost:6379",
        MINIO_ENDPOINT: "http://localhost:9000",
        MINIO_ACCESS_KEY: "minioadmin",
        MINIO_SECRET_KEY: "minioadmin",
        SECRET_KEY: "change-in-production",
      },
      max_restarts: 10,
    },
    {
      name: "social-media-platform-celery-worker",
      cwd: "./backend",
      script: "venv/bin/celery",
      args: "-A app.tasks.celery_app worker --loglevel=info",
      interpreter: "venv/bin/python3",
      env: {
        DATABASE_URL: "postgresql://app_user:app_pass@localhost:5432/social_media_platform",
        REDIS_URL: "redis://localhost:6379",
      },
      max_restarts: 10,
    },
    {
      name: "social-media-platform-celery-beat",
      cwd: "./backend",
      script: "venv/bin/celery",
      args: "-A app.tasks.celery_app beat --loglevel=info",
      interpreter: "venv/bin/python3",
      env: {
        DATABASE_URL: "postgresql://app_user:app_pass@localhost:5432/social_media_platform",
        REDIS_URL: "redis://localhost:6379",
      },
      max_restarts: 10,
    },
    {
      name: "social-media-platform-frontend",
      cwd: "./frontend",
      script: "npx",
      args: "vite --host 0.0.0.0 --port 3000",
      env: { PORT: 3000, VITE_API_URL: "http://localhost:8000" },
      max_restarts: 10,
    },    {
      name: "social-media-platform-frontend-admin",
      cwd: "./frontend-admin",
      script: "npx",
      args: "vite --host 0.0.0.0 --port 3001",
      env: { PORT: 3001, VITE_API_URL: "http://localhost:8000" },
      max_restarts: 10,
    }
  ],
};
