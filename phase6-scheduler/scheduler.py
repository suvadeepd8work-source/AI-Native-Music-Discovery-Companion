"""
Phase 6: Scheduler Module
Automated workflow execution for weekly review processing and insight generation.
Runs every Monday at 10:00 AM IST.
"""
import asyncio
import structlog
from datetime import datetime
from typing import Optional, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
import pytz

from workflow_executor import WorkflowExecutor
from review_downloader import ReviewDownloader
from insight_generator import InsightGenerator
from frontend_updater import FrontendUpdater
from scheduler_logger import SchedulerLogger


logger = structlog.get_logger(__name__)


class MusicDiscoveryScheduler:
    """
    Main scheduler for automated music discovery workflow execution.
    Runs every Monday at 10:00 AM IST.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or {}
        
        # Configure scheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': True,
            'max_instances': 1,
            'misfire_grace_time': 3600  # 1 hour grace time
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=pytz.timezone('Asia/Kolkata')  # IST timezone
        )
        
        # Initialize components
        self.workflow_executor = WorkflowExecutor(config)
        self.review_downloader = ReviewDownloader(config)
        self.insight_generator = InsightGenerator(config)
        self.frontend_updater = FrontendUpdater(config)
        self.scheduler_logger = SchedulerLogger(config)
        
        self.is_running = False
    
    def start(self):
        """Start the scheduler."""
        if not self.is_running:
            # Schedule weekly job for Monday 10:00 AM IST
            self.scheduler.add_job(
                self.execute_weekly_workflow,
                CronTrigger(
                    day_of_week='mon',
                    hour=10,
                    minute=0,
                    timezone=pytz.timezone('Asia/Kolkata')
                ),
                id='weekly_workflow',
                name='Weekly Music Discovery Workflow',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info(
                "Scheduler started",
                next_run_time=self.scheduler.get_job('weekly_workflow').next_run_time
            )
        else:
            logger.warning("Scheduler already running")
    
    def stop(self):
        """Stop the scheduler."""
        if self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("Scheduler stopped")
    
    async def execute_weekly_workflow(self):
        """
        Execute the complete weekly workflow:
        1. Download latest reviews
        2. Generate insights
        3. Update frontend
        4. Log execution
        """
        job_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            logger.info("Starting weekly workflow", job_id=job_id)
            
            # Log workflow start
            await self.scheduler_logger.log_workflow_start(job_id)
            
            # Step 1: Download latest reviews
            logger.info("Step 1: Downloading latest reviews", job_id=job_id)
            review_stats = await self.review_downloader.download_latest_reviews()
            await self.scheduler_logger.log_step_completion(
                job_id, "download_reviews", review_stats
            )
            
            # Step 2: Generate insights
            logger.info("Step 2: Generating insights", job_id=job_id)
            insight_stats = await self.insight_generator.generate_insights()
            await self.scheduler_logger.log_step_completion(
                job_id, "generate_insights", insight_stats
            )
            
            # Step 3: Update frontend
            logger.info("Step 3: Updating frontend", job_id=job_id)
            frontend_stats = await self.frontend_updater.update_frontend()
            await self.scheduler_logger.log_step_completion(
                job_id, "update_frontend", frontend_stats
            )
            
            # Step 4: Execute complete workflow
            logger.info("Step 4: Executing complete workflow", job_id=job_id)
            workflow_stats = await self.workflow_executor.execute_workflow()
            await self.scheduler_logger.log_step_completion(
                job_id, "execute_workflow", workflow_stats
            )
            
            # Log workflow completion
            await self.scheduler_logger.log_workflow_completion(
                job_id,
                {
                    "download_reviews": review_stats,
                    "generate_insights": insight_stats,
                    "update_frontend": frontend_stats,
                    "execute_workflow": workflow_stats
                }
            )
            
            logger.info(
                "Weekly workflow completed successfully",
                job_id=job_id,
                total_reviews=review_stats.get("total_reviews", 0),
                total_insights=insight_stats.get("total_insights", 0)
            )
            
        except Exception as e:
            logger.error(
                "Weekly workflow failed",
                job_id=job_id,
                error=str(e)
            )
            await self.scheduler_logger.log_workflow_failure(job_id, str(e))
            raise
    
    async def execute_manual_workflow(self):
        """
        Manually trigger workflow execution (for testing or on-demand runs).
        """
        logger.info("Manual workflow execution triggered")
        await self.execute_weekly_workflow()
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time."""
        job = self.scheduler.get_job('weekly_workflow')
        if job:
            return job.next_run_time
        return None
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get scheduler job status."""
        job = self.scheduler.get_job('weekly_workflow')
        if job:
            return {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "scheduler_running": self.is_running
            }
        return {
            "scheduler_running": self.is_running,
            "job_found": False
        }


class MockMusicDiscoveryScheduler:
    """Mock scheduler for testing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.is_running = False
        self.execution_count = 0
    
    def start(self):
        """Start the mock scheduler."""
        self.is_running = True
        logger.info("Mock scheduler started")
    
    def stop(self):
        """Stop the mock scheduler."""
        self.is_running = False
        logger.info("Mock scheduler stopped")
    
    async def execute_weekly_workflow(self):
        """Mock workflow execution."""
        self.execution_count += 1
        logger.info("Mock weekly workflow executed", count=self.execution_count)
    
    async def execute_manual_workflow(self):
        """Mock manual workflow execution."""
        await self.execute_weekly_workflow()
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Return mock next run time."""
        return None
    
    def get_job_status(self) -> Dict[str, Any]:
        """Return mock job status."""
        return {
            "scheduler_running": self.is_running,
            "job_found": True,
            "execution_count": self.execution_count
        }
