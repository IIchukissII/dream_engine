"""Scheduler service entry point using APScheduler."""

import logging
import sys
import threading
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, jsonify

from .config import LOG_LEVEL
from .flows.cleanup import account_cleanup_flow

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Flask app for health checks
app = Flask(__name__)

# Store last run info
last_run = {"time": None, "status": None, "result": None}


def run_cleanup():
    """Run the cleanup flow and track results."""
    global last_run
    logger.info("Starting scheduled cleanup job")
    try:
        result = account_cleanup_flow()
        last_run = {
            "time": datetime.utcnow().isoformat(),
            "status": "success",
            "result": result
        }
        logger.info(f"Cleanup completed: {result}")
    except Exception as e:
        last_run = {
            "time": datetime.utcnow().isoformat(),
            "status": "error",
            "result": str(e)
        }
        logger.error(f"Cleanup failed: {e}")


@app.route('/health')
@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "scheduler",
        "last_run": last_run
    })


@app.route('/status')
@app.route('/api/status')
def status():
    """Status endpoint with job info."""
    return jsonify({
        "service": "storm-logos-scheduler",
        "jobs": [
            {
                "name": "account-cleanup",
                "schedule": "daily at 03:00 UTC",
                "last_run": last_run
            }
        ]
    })


@app.route('/run')
@app.route('/api/run')
def manual_run():
    """Manually trigger cleanup (for testing)."""
    threading.Thread(target=run_cleanup).start()
    return jsonify({"message": "Cleanup job started"})


def main():
    """Start the scheduler service."""
    logger.info("Starting Storm-Logos Scheduler Service")

    # Create scheduler
    scheduler = BackgroundScheduler()

    # Add cleanup job - runs daily at 3 AM UTC
    scheduler.add_job(
        run_cleanup,
        CronTrigger(hour=3, minute=0),
        id='account-cleanup',
        name='Account Cleanup',
        replace_existing=True
    )

    # Start scheduler
    scheduler.start()
    logger.info("Scheduler started - cleanup runs daily at 03:00 UTC")

    # Run Flask server for health checks
    logger.info("Starting health check server on port 4200")
    app.run(host='0.0.0.0', port=4200, threaded=True)


if __name__ == "__main__":
    main()
