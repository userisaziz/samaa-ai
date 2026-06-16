
import os
from celery import Celery
import platform

# Set environment variables
os.environ.setdefault('FSTAB_ENABLED', 'false')

# Create Celery app
app = Celery('cxsamaa')

# Configure Celery from src.config.settings
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/1',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # Process one task at a time
)

# Auto-discover tasks in workers module
# Note: Explicitly import worker modules to register tasks
import src.workers.pipeline_worker  # noqa: F401

@app.on_after_configure.connect
def on_after_configure(sender, **kwargs):
    system = platform.system()
    if system == "Darwin":
        sender.conf.worker_pool = "solo"
        sender.conf.worker_concurrency = 1
        print(f"🍎 Detected macOS: Switched to 'solo' pool to prevent crashes.")
    else:
        if not sender.conf.worker_pool:
            sender.conf.worker_pool = "prefork"
        print(f"☁️ Detected Linux/Cloud: Using '{sender.conf.worker_pool}' pool.")

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
