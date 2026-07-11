# Quick Start Guide

## For Development

### Prerequisites
- Docker and Docker Compose installed
- Git

### Step 1: Clone/Setup
```bash
cd shared-expenses-app
cp .env.example .env
```

### Step 2: Build & Run
```bash
docker-compose up --build
```

### Step 3: Access Application
- Frontend: http://localhost
- Backend API: http://localhost:8000/api
- Admin Panel: http://localhost:8000/admin

### Step 4: Create Admin User
```bash
docker-compose exec backend python manage.py createsuperuser
```

## For Deployment

### Quick Deploy with Docker

1. **Update `.env`**:
```bash
cp .env.example .env
# Edit .env with production settings
```

2. **Build Images**:
```bash
docker build -f Dockerfile.backend -t app-backend:latest .
docker build -f Dockerfile.frontend -t app-frontend:latest .
```

3. **Run Containers**:
```bash
docker run -d -p 8000:8000 --env-file .env --name backend app-backend:latest
docker run -d -p 80:80 --name frontend app-frontend:latest
```

## Common Commands

### View Logs
```bash
docker-compose logs -f backend    # Backend logs
docker-compose logs -f frontend   # Frontend logs
docker-compose logs -f            # All logs
```

### Database Management
```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py collectstatic
```

### Shell Access
```bash
docker-compose exec backend python manage.py shell
```

### Stop Services
```bash
docker-compose down        # Stop all services
docker-compose down -v     # Stop all and remove volumes
```

## Environment Variables

Key variables in `.env`:

- `DEBUG` - Set to `False` in production
- `SECRET_KEY` - Must be changed for production
- `ALLOWED_HOSTS` - Your domain names
- `CORS_ALLOWED_ORIGINS` - Frontend URLs allowed to access API
- `SECURE_SSL_REDIRECT` - Set to `True` with HTTPS
- `SESSION_COOKIE_SECURE` - Set to `True` with HTTPS
- `CSRF_COOKIE_SECURE` - Set to `True` with HTTPS

## Production Checklist

- [ ] Changed SECRET_KEY in .env
- [ ] Set DEBUG=False
- [ ] Updated ALLOWED_HOSTS
- [ ] Configured CORS_ALLOWED_ORIGINS
- [ ] Set up HTTPS/SSL
- [ ] Updated security cookie settings
- [ ] Tested database migrations
- [ ] Created superuser account
- [ ] Verified static files are serving
- [ ] Configured backups

## Troubleshooting

**Backend not responding?**
```bash
docker-compose logs backend
docker-compose exec backend python manage.py migrate
```

**Static files not loading?**
```bash
docker-compose exec backend python manage.py collectstatic --noinput --clear
```

**Port already in use?**
```bash
docker-compose down
# or change ports in docker-compose.yml
```

## For More Details

See `DEPLOYMENT.md` for comprehensive deployment guide.

---

**Happy deploying! 🚀**
