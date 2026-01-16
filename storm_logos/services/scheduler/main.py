"""Scheduler service entry point."""

import logging
import sys
from datetime import timedelta

from prefect import serve
from prefect.client.schemas.schedules import IntervalSchedule

from .config import LOG_LEVEL
from .flows import account_cleanup_flow

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def main():
    """Start the scheduler service with all flows."""
    logger.info("Starting Storm-Logos Scheduler Service")

    # Create deployment for account cleanup - runs daily at 3 AM UTC
    cleanup_deployment = account_cleanup_flow.to_deployment(
        name="account-cleanup-daily",
        description="Daily cleanup of unverified accounts",
        schedule=IntervalSchedule(interval=timedelta(days=1)),
        tags=["cleanup", "maintenance"]
    )

    logger.info("Serving flows...")

    # Serve all deployments
    serve(cleanup_deployment)


if __name__ == "__main__":
    main()
