# PurohitConnect Production Deployment Guide

This guide covers deploying PurohitConnect to production environments.

## Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Redis (optional, for caching)
- Nginx or Apache web server
- SSL certificate (Let's Encrypt recommended)
- Domain name

## 1. Server Setup

### Ubuntu/Debian Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib redis-server nginx certbot python3-certbot-nginx

# Create application user
sudo useradd -m -s /bin/bash purohitconnect
sudo usermod -aG www-data purohitconnect
```

### Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE purohitconnect_db;
CREATE USER purohitconnect_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE purohitconnect_db TO purohitconnect_user;
ALTER USER purohitconnect_user CREATEDB;
\q
```

## 2. Application Deployment

### Option A: Docker Compose (recommended for local/staging)
See [DOCKER.md](DOCKER.md):
```bash
docker compose up --build
```

### Option B: Clone and Setup (bare metal)

```bash
# Clone repository
cd /home/purohitconnect
git clone https://github.com/your-org/purohitconnect.git
cd purohitconnect

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary django-storages[boto3]  # Additional production packages
```

### Environment Configuration

```bash
# Copy environment file
cp .env.example .env

# Edit with your production values
nano .env
```

Required production environment variables:
- `SECRET_KEY`: Generate a secure random key
- `DJANGO_DEBUG=False`
- `DATABASE_URL`: PostgreSQL connection string
- `RAZORPAY_KEY_ID` & `RAZORPAY_KEY_SECRET`: Live Razorpay credentials
- `ALLOWED_HOSTS`: Your domain(s)
- `CSRF_TRUSTED_ORIGINS`: HTTPS URLs for your domain
- Security settings: SSL redirect, HSTS, secure cookies

### Database Migration

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

## 3. Gunicorn Setup

### Create Gunicorn Service

```bash
sudo nano /etc/systemd/system/purohitconnect.service
```

Add the following content:

```ini
[Unit]
Description=PurohitConnect Django Application
After=network.target

[Service]
User=purohitconnect
Group=www-data
WorkingDirectory=/home/purohitconnect/purohitconnect
Environment="PATH=/home/purohitconnect/purohitconnect/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings.production"
ExecStart=/home/purohitconnect/purohitconnect/venv/bin/gunicorn --workers 4 --bind unix:/home/purohitconnect/purohitconnect.sock config.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

### Start Gunicorn Service

```bash
sudo systemctl daemon-reload
sudo systemctl start purohitconnect
sudo systemctl enable purohitconnect
sudo systemctl status purohitconnect
```

## 4. Nginx Configuration

### Create Nginx Site Configuration

```bash
sudo nano /etc/nginx/sites-available/purohitconnect
```

Add the following content:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /home/purohitconnect/purohitconnect/staticfiles/;
    }

    location /media/ {
        alias /home/purohitconnect/purohitconnect/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/purohitconnect/purohitconnect.sock;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
    }
}

server {
    listen 80;
    server_name _;
    return 444;
}
```

### Enable Site and SSL

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/purohitconnect /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test SSL renewal
sudo certbot renew --dry-run
```

## 5. Redis Setup (Optional)

For caching and session storage:

```bash
# Install Redis
sudo apt install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
# Set supervised systemd
# Set maxmemory and maxmemory-policy

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Update .env with Redis URLs
REDIS_URL=redis://localhost:6379/1
CACHE_URL=redis://localhost:6379/2
```

## 6. Monitoring and Logging

### Log Rotation

```bash
sudo nano /etc/logrotate.d/purohitconnect
```

Add:

```
/home/purohitconnect/purohitconnect/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 purohitconnect www-data
    postrotate
        systemctl reload purohitconnect
    endscript
}
```

### Health Checks

Create a health check endpoint in Django:

```python
# In views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        connection.cursor()
        return JsonResponse({'status': 'healthy'})
    except:
        return JsonResponse({'status': 'unhealthy'}, status=500)
```

Add to URLs and configure monitoring.

## 7. Backup Strategy

### Database Backup

```bash
# Create backup script
sudo nano /home/purohitconnect/backup.sh
```

Add:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U purohitconnect_user -h localhost purohitconnect_db > /home/purohitconnect/backups/db_$DATE.sql
find /home/purohitconnect/backups -name "db_*.sql" -mtime +7 -delete
```

### Automated Backups

```bash
# Add to crontab
sudo crontab -e
# Add: 0 2 * * * /home/purohitconnect/backup.sh
```

## 8. Security Considerations

### Firewall Setup

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

### File Permissions

```bash
sudo chown -R purohitconnect:www-data /home/purohitconnect
sudo chmod -R 755 /home/purohitconnect
sudo chmod 600 /home/purohitconnect/purohitconnect/.env
```

### Security Updates

```bash
# Automate security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

## 9. Performance Optimization

### Database Optimization

- Add database indexes for frequently queried fields
- Configure connection pooling
- Set up read replicas for high traffic

### Caching

```python
# In settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('CACHE_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### Static File Optimization

- Use CloudFront or similar CDN
- Enable gzip compression in Nginx
- Set appropriate cache headers

## 10. Troubleshooting

### Common Issues

1. **502 Bad Gateway**: Check Gunicorn service status
2. **Database Connection Errors**: Verify DATABASE_URL
3. **Static Files Not Loading**: Run collectstatic
4. **SSL Issues**: Check certbot certificates

### Logs

```bash
# Application logs
sudo journalctl -u purohitconnect -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Gunicorn logs
sudo tail -f /home/purohitconnect/purohitconnect/logs/gunicorn.log
```

## 11. Scaling

For high traffic:

1. **Load Balancer**: Use AWS ELB or Nginx upstream
2. **Multiple Application Servers**: Deploy across multiple instances
3. **Database Read Replicas**: Offload read queries
4. **CDN**: For static/media files
5. **Redis Cluster**: For distributed caching

## 12. Maintenance

### Scheduled jobs (required)

Run hourly to auto-expire unanswered reschedule requests:

```bash
# Linux/macOS cron (example: every hour at :15)
15 * * * * /home/purohitconnect/purohitconnect/scripts/expire_pending_reschedules.sh >> /var/log/purohitconnect-cron.log 2>&1
```

Windows Task Scheduler:
- Program: `powershell.exe`
- Arguments: `-ExecutionPolicy Bypass -File C:\path\to\purohitconnect\scripts\expire_pending_reschedules.ps1`
- Trigger: hourly

Manual run:
```bash
python manage.py run_scheduled_jobs
# or
python manage.py expire_pending_reschedules
```

### Withdrawal / payout ops

1. Verify purohit bank accounts in Admin → **Purohit bank accounts** → **Mark verified**
2. Review queued withdrawals in Admin → **Withdrawal requests**
3. Actions: **Approve & initiate payout**, **Retry RazorpayX payout**, or **Reject & restore wallet funds**
4. Keep `WITHDRAWAL_AUTO_PAYOUT=False` unless bank verification + RazorpayX are fully trusted

### Regular Tasks

- Monitor disk space and logs
- Update dependencies quarterly
- Security patches: monthly
- Database maintenance: weekly
- Full backups: daily
- SSL renewal: automatic via certbot

### Emergency Procedures

- Have rollback procedures ready
- Monitor error rates and response times
- Set up alerts for critical issues
- Document incident response procedures