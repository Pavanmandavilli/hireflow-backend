# gunicorn.conf.py — production WSGI/ASGI server configuration
import multiprocessing

# Workers
worker_class = "uvicorn.workers.UvicornWorker"
workers = multiprocessing.cpu_count() * 2 + 1
threads = 1

# Networking
host = "0.0.0.0"
port = 8000
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
