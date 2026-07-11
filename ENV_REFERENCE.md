# Environment Variables Reference Guide

## How Environment Variables Work

### Loading Order
1. Variables from `.env` file (local development)
2. System environment variables (Docker, servers)
3. Default values in code (fallback)

### Using Variables in docker-compose.yml

```yaml
environment:
  - KEY=${ENV_VAR:-default_value}
  # If ENV_VAR is set, use it; otherwise use default_value
```

## All Available Variables

### 🔑 Core Django Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEBUG` | Yes | `False` | Enable debug mode (NEVER true in production) |
| `SECRET_KEY` | Yes | Generated | Django secret key for sessions & tokens |
| `ALLOWED_HOSTS` | Yes | `localhost,127.0.0.1` | Comma-separated hostnames |
| `DJANGO_LOG_LEVEL` | No | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |

### 🌐 CORS & Frontend

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CORS_ALLOWED_ORIGINS` | Yes | `http://localhost:3000,...` | Comma-separated frontend URLs |
| `VITE_API_URL` | Yes | `http://localhost:8000/api` | Backend API URL for frontend |
| `FRONTEND_PORT` | No | `80` | Port to expose frontend (docker-compose only) |

### 🔒 Security (Production)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECURE_SSL_REDIRECT` | No | `False` | Redirect HTTP to HTTPS (needs SSL cert) |
| `SESSION_COOKIE_SECURE` | No | `False` | Send session cookies only over HTTPS |
| `CSRF_COOKIE_SECURE` | No | `False` | Send CSRF cookies only over HTTPS |
| `SECURE_HSTS_SECONDS` | No | `` | HTTP Strict Transport Security duration |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | No | `` | Include subdomains in HSTS |
| `SECURE_HSTS_PRELOAD` | No | `` | Add domain to HSTS preload list |

### 📧 Email (Optional)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EMAIL_BACKEND` | No | `` | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | No | `` | SMTP server (e.g., `smtp.gmail.com`) |
| `EMAIL_PORT` | No | `` | SMTP port (usually 587 or 465) |
| `EMAIL_USE_TLS` | No | `` | Use TLS encryption |
| `EMAIL_HOST_USER` | No | `` | SMTP username/email |
| `EMAIL_HOST_PASSWORD` | No | `` | SMTP password or app password |

### ☁️ AWS S3 Storage (Optional)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `USE_S3` | No | `` | Enable S3 for media/static files |
| `AWS_ACCESS_KEY_ID` | No | `` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | No | `` | AWS secret access key |
| `AWS_STORAGE_BUCKET_NAME` | No | `` | S3 bucket name |
| `AWS_S3_REGION_NAME` | No | `` | AWS region (e.g., `us-east-1`) |

### 🗄️ Database (Optional)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_ENGINE` | No | `sqlite3` | `postgresql` for PostgreSQL |
| `DB_NAME` | No | `db.sqlite3` | Database name |
| `DB_USER` | No | `` | Database username |
| `DB_PASSWORD` | No | `` | Database password |
| `DB_HOST` | No | `` | Database host |
| `DB_PORT` | No | `` | Database port |

### ⚙️ Gunicorn Configuration (Optional)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GUNICORN_WORKERS` | No | `4` | Number of worker processes |
| `GUNICORN_TIMEOUT` | No | `60` | Worker timeout in seconds |
| `GUNICORN_MAX_REQUESTS` | No | `1000` | Requests before worker restart |

## Environment Profiles

### Development

```env
DEBUG=True
SECRET_KEY=dev-key-not-secure
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
VITE_API_URL=http://localhost:8000/api
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
DJANGO_LOG_LEVEL=DEBUG
```

### Staging

```env
DEBUG=False
SECRET_KEY=<generate-random>
ALLOWED_HOSTS=staging.yourdomain.com
CORS_ALLOWED_ORIGINS=https://staging.yourdomain.com
VITE_API_URL=https://api-staging.yourdomain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
DJANGO_LOG_LEVEL=INFO
```

### Production

```env
DEBUG=False
SECRET_KEY=<generate-random>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
VITE_API_URL=https://api.yourdomain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
DJANGO_LOG_LEVEL=WARNING
```

## How to Set Environment Variables

### 1. Using .env File (Development)

```bash
# Create file from template
cp .env.example .env

# Edit .env with your values
nano .env
```

### 2. Docker Compose

```bash
# Automatically loads from .env
docker-compose up

# Or pass specific variables
docker-compose -e DEBUG=False up
```

### 3. Docker Run

```bash
docker run --env-file .env -p 8000:8000 app-backend
```

### 4. Linux/Mac Shell

```bash
export DEBUG=False
export SECRET_KEY=your-key-here
python manage.py runserver
```

### 5. Windows PowerShell

```powershell
$env:DEBUG = "False"
$env:SECRET_KEY = "your-key-here"
python manage.py runserver
```

### 6. Cloud Platforms

**AWS (ECS)**
```yaml
containerDefinitions:
  - name: backend
    environment:
      - name: DEBUG
        value: "False"
      - name: SECRET_KEY
        valueFrom: "arn:aws:secretsmanager:..."
```

**Azure (Container Instances)**
```yaml
containers:
- name: backend
  environmentVariables:
  - name: DEBUG
    value: "False"
  - name: SECRET_KEY
    secureValue: ...
```

## ⚠️ Important Security Notes

### Never Commit .env to Git

```bash
# ❌ NEVER do this
git add .env
git commit -m "Add environment variables"

# ✅ DO this instead
git add .env.example
git commit -m "Add environment template"
```

### Generate Secure SECRET_KEY

```bash
# Option 1: Using Django
python manage.py shell
>>> from django.core.management.utils import get_random_secret_key
>>> print(get_random_secret_key())

# Option 2: Using Python
python -c "import secrets; print(secrets.token_urlsafe(50))"

# Option 3: Using OpenSSL
openssl rand -base64 50
```

### Protect Sensitive Variables

Use secret management services:
- **AWS**: AWS Secrets Manager, Systems Manager Parameter Store
- **Azure**: Azure Key Vault
- **GCP**: Secret Manager
- **Generic**: Vault, Consul, etc.

```bash
# Load from AWS Secrets Manager
export SECRET_KEY=$(aws secretsmanager get-secret-value --secret-id app-secret-key --query SecretString --output text)

# Load from Azure Key Vault
export SECRET_KEY=$(az keyvault secret show --name app-secret-key --vault-name mykeyvault --query value --output tsv)
```

## Validation Checklist

- [ ] All required variables are set
- [ ] SECRET_KEY is a random string (not default)
- [ ] DEBUG is False in production
- [ ] ALLOWED_HOSTS matches your domain
- [ ] CORS_ALLOWED_ORIGINS only includes trusted URLs
- [ ] SSL/HTTPS variables match your setup
- [ ] Database credentials are strong
- [ ] Email settings are correct (if using email)
- [ ] AWS credentials have minimal permissions (if using S3)
- [ ] .env file is in .gitignore
- [ ] Backups are configured

## Troubleshooting

### Variables Not Loading

```bash
# Check docker-compose picks up .env
docker-compose config | grep SECRET_KEY

# Check inside container
docker-compose exec backend env | grep DJANGO
```

### Variable Syntax Errors

```bash
# ❌ Wrong - spaces around =
DEBUG = False

# ✅ Correct - no spaces
DEBUG=False

# ❌ Wrong - quotes not needed unless value has spaces
SECRET_KEY="my-key"

# ✅ Correct
SECRET_KEY=my-key
# or with spaces:
SECRET_KEY="my super key with spaces"
```

### Reference Variables Across Services

```yaml
# ✅ Works in docker-compose
services:
  backend:
    environment:
      - API_URL=http://frontend
  frontend:
    environment:
      - BACKEND_URL=http://backend:8000
```

---

**Last Updated**: 2026-07-11
**For Questions**: See DEPLOYMENT.md or QUICKSTART.md
