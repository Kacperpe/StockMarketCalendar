import os
from datetime import datetime

from celery import Celery


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery("trading_worker", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.task_default_queue = "default"
celery_app.conf.task_routes = {
    "sync_mt5_account": {"queue": "sync"},
    "sync_ctrader_account": {"queue": "sync"},
    "recompute_account_metrics": {"queue": "metrics"},
}


@celery_app.task(name="sync_mt5_account")
def sync_mt5_account(account_id: int) -> dict:
    return {"task": "sync_mt5_account", "account_id": account_id, "status": "todo", "at": datetime.utcnow().isoformat()}


@celery_app.task(name="sync_ctrader_account")
def sync_ctrader_account(account_id: int) -> dict:
    return {
        "task": "sync_ctrader_account",
        "account_id": account_id,
        "status": "todo",
        "at": datetime.utcnow().isoformat(),
    }


@celery_app.task(name="recompute_account_metrics")
def recompute_account_metrics(account_id: int) -> dict:
    return {
        "task": "recompute_account_metrics",
        "account_id": account_id,
        "status": "todo",
        "at": datetime.utcnow().isoformat(),
    }

