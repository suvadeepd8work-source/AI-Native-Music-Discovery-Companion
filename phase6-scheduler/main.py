"""
Phase 6: Scheduler Main Application
Entry point for the automated music discovery scheduler.
"""
import asyncio
import yaml
import structlog
from typing import Optional
import os
from pydantic_settings import BaseSettings

from scheduler import MusicDiscoveryScheduler, MockMusicDiscoveryScheduler
from scheduler_logger import SchedulerLogger


# Configuration
class Settings(BaseSettings):
    use_mocks: bool = os.getenv("USE_MOCKS", "false").lower() == "true"
    config_file: str = "config.yaml"
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")


settings = Settings()

# Load configuration
with open(settings.config_file, 'r') as f:
    config = yaml.safe_load(f)

# Add API key to config
if settings.groq_api_key:
    config["insight_generation"]["groq_api_key"] = settings.groq_api_key

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


# Initialize scheduler
scheduler: Optional[MusicDiscoveryScheduler] = None


async def main():
    """Main entry point for the scheduler."""
    global scheduler
    
    logger.info("Starting Phase 6: Music Discovery Scheduler")
    
    try:
        # Initialize scheduler
        if settings.use_mocks:
            logger.info("Using mock scheduler")
            scheduler = MockMusicDiscoveryScheduler(config)
        else:
            logger.info("Using production scheduler")
            scheduler = MusicDiscoveryScheduler(config)
        
        # Start scheduler
        scheduler.start()
        
        # Print scheduler status
        job_status = scheduler.get_job_status()
        logger.info("Scheduler status", **job_status)
        
        if job_status.get("next_run_time"):
            print(f"\n✓ Scheduler started successfully")
            print(f"✓ Next run: {job_status['next_run_time']}")
            print(f"✓ Schedule: Every Monday at 10:00 AM IST")
        else:
            print(f"\n✓ Mock scheduler started")
        
        # Keep the scheduler running
        try:
            while True:
                await asyncio.sleep(3600)  # Check every hour
                logger.info("Scheduler heartbeat")
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down")
        
    except Exception as e:
        logger.error("Scheduler failed to start", error=str(e))
        raise
    finally:
        if scheduler:
            scheduler.stop()
        logger.info("Scheduler shutdown complete")


async def run_manual_workflow():
    """Manually trigger a workflow execution (for testing)."""
    global scheduler
    
    logger.info("Running manual workflow")
    
    try:
        # Initialize scheduler
        if settings.use_mocks:
            scheduler = MockMusicDiscoveryScheduler(config)
        else:
            scheduler = MusicDiscoveryScheduler(config)
        
        # Execute manual workflow
        await scheduler.execute_manual_workflow()
        
        logger.info("Manual workflow completed")
        
    except Exception as e:
        logger.error("Manual workflow failed", error=str(e))
        raise
    finally:
        if scheduler:
            scheduler.stop()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        # Run manual workflow
        asyncio.run(run_manual_workflow())
    else:
        # Run scheduler
        asyncio.run(main())
