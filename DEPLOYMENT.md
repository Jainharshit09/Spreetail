# Deployment Guide

This guide covers building and deploying the Shared Expenses App using Docker.

## Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 1.29+)

## Project Structure

```
.
├── Dockerfile.backend      # Django backend Dockerfile
├── Dockerfile.frontend     # React/Vite frontend Dockerfile
├── docker-compose.yml      # Orchestration file
├── nginx.conf              # Nginx main config
├── nginx-default.conf      # Nginx app config
├── .dockerignore           # Files to exclude from Docker build
├── .env.example            # Environment variables template
└── requirements.txt        # Python dependencies (updated with production packages)
```

## Quick Start with Docker Compose

### 1. Setup Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 2. Build and Run

```bash
docker-compose up --build
```

This will:
- Build the backend image (Django + Gunicorn)
- Build the frontend image (React/Vite + Nginx)
- Start both services with proper networking
- Run database migrations automatically

### 3. Access the Application

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000/api
- **Admin Panel**: http://localhost:8000/admin

## Building Individually

### Build Backend

```bash
docker build -f Dockerfile.backend -t shared-expenses-backend:latest .
docker run -p 8000:8000 shared-expenses-backend:latest
```

### Build Frontend

```bash
docker build -f Dockerfile.frontend -t shared-expenses-frontend:latest .
docker run -p 80:80 shared-expenses-frontend:latest
```

## Docker Images Overview

### Backend Image (Dockerfile.backend)

- **Base Image**: python:3.11-slim (multi-stage build)
- **Size**: ~200MB
- **Port**: 8000
- **Server**: Gunicorn with 4 workers
- **Features**:
  - Static file collection
  - Health checks
  - Security headers
  - Production-ready configuration

### Frontend Image (Dockerfile.frontend)

- **Base Image**: node:20-alpine (builder) + nginx:alpine (production)
- **Size**: ~50MB
- **Port**: 80
- **Server**: Nginx
- **Features**:
  - SPA routing support
  - Gzip compression
  - Security headers
  - Cache optimization
  - Health checks

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Django
DEBUG=False
SECRET_KEY=your-super-secret-key-change-this
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Security (set to True in production with HTTPS)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

## Production Deployment

### Using Docker Registry (e.g., Docker Hub, AWS ECR)

1. **Tag images**:
```bash
docker tag shared-expenses-backend:latest myregistry/shared-expenses-backend:v1.0.0
docker tag shared-expenses-frontend:latest myregistry/shared-expenses-frontend:v1.0.0
```

2. **Push images**:
```bash
docker push myregistry/shared-expenses-backend:v1.0.0
docker push myregistry/shared-expenses-frontend:v1.0.0
```

3. **Update docker-compose.yml** to use the pushed images instead of building locally.

### Cloud Deployment Options

#### AWS (ECS or App Runner)
- Use the pushed images from ECR
- Configure RDS for PostgreSQL (instead of SQLite)
- Use S3 for media files
- Use CloudFront for CDN

#### Azure (Container Instances or App Service)
- Push to Azure Container Registry
- Deploy using Azure Container Instances or App Service
- Use Azure Database for PostgreSQL
- Use Azure Blob Storage for media

#### Google Cloud (Cloud Run)
- Push to Google Container Registry
- Deploy to Cloud Run
- Use Cloud SQL for PostgreSQL
- Use Cloud Storage for media

#### DigitalOcean (App Platform)
- Push to DigitalOcean Container Registry
- Deploy using App Platform
- Use Managed Databases for PostgreSQL
- Use Spaces for media storage

### Kubernetes Deployment

For Kubernetes, create:

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shared-expenses-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: shared-expenses-backend
  template:
    metadata:
      labels:
        app: shared-expenses-backend
    spec:
      containers:
      - name: backend
        image: myregistry/shared-expenses-backend:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DEBUG
          value: "False"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /admin/
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /admin/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

### PostgreSQL Migration (Recommended for Production)

To use PostgreSQL instead of SQLite:

1. **Update requirements.txt**:
```bash
pip install psycopg2-binary==2.9.9
```

2. **Update django settings**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'shared_expenses'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

3. **Update docker-compose.yml** to include PostgreSQL service:
```yaml
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: shared_expenses
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: your-db-password
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

## Monitoring and Logging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Health Checks

Built-in health checks are configured for both services. View status:

```bash
docker-compose ps
```

## Maintenance Commands

```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Collect static files
docker-compose exec backend python manage.py collectstatic

# Shell access
docker-compose exec backend python manage.py shell

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild services
docker-compose up --build --force-recreate
```

## Security Checklist for Production

- [ ] Change `SECRET_KEY` to a random value
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS` correctly
- [ ] Set `SECURE_SSL_REDIRECT=True` with valid HTTPS certificate
- [ ] Enable `SESSION_COOKIE_SECURE=True`
- [ ] Enable `CSRF_COOKIE_SECURE=True`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Store secrets in environment variables or secret management systems
- [ ] Use HTTPS/TLS for all traffic
- [ ] Set up proper logging and monitoring
- [ ] Configure firewall rules appropriately
- [ ] Regularly update base images and dependencies
- [ ] Use resource limits (memory, CPU)
- [ ] Set up automated backups
- [ ] Configure CORS properly for your domain

## Troubleshooting

### Backend connection refused
```bash
docker-compose logs backend
```

### Static files not serving
```bash
docker-compose exec backend python manage.py collectstatic --noinput --clear
```

### Frontend not connecting to backend
- Check CORS settings in `.env`
- Verify backend is running: `docker-compose ps`
- Check backend logs: `docker-compose logs backend`

### Database errors
```bash
docker-compose exec backend python manage.py migrate
```

### Port already in use
```bash
# Change ports in docker-compose.yml or kill existing services
docker ps
docker stop <container_id>
```

## Performance Optimization

- Use CloudFront/CDN for static files
- Enable database query caching
- Implement API rate limiting
- Use Redis for session storage
- Compress responses (already enabled in Nginx)
- Use async tasks for long-running operations (Celery + Redis)

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Django Deployment Guide](https://docs.djangoproject.com/en/6.0/howto/deployment/)
- [Vite Documentation](https://vitejs.dev/)
- [Nginx Documentation](https://nginx.org/)
