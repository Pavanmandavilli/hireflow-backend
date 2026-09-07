# gunicorn.conf.py — production WSGI/ASGI server configuration
import multiprocessing
import os

# Workers — capped at 2 for free-tier containers (low RAM)
worker_class = "uvicorn.workers.UvicornWorker"
workers = min(multiprocessing.cpu_count() * 2 + 1, 2)
threads = 1

# Networking — respect PORT injected by Railway / Render / Fly / Koyeb
host = "0.0.0.0"
port = int(os.environ.get("PORT", 8000))
bind = f"{host}:{port}"


# Timeouts
timeout = 120
keepalive = 5
graceful_timeout = 30

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(D)sµs'

# Process naming
proc_name = "fastapi-service"

# Reload (disable in production)
reload = False
