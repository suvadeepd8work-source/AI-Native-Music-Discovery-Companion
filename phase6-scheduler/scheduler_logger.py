"""
Scheduler Logger
Logs scheduler execution and workflow results.
"""
import asyncio
import structlog
from typing import Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path


logger = structlog.get_logger(__name__)


class SchedulerLogger:
    """
    Logs scheduler execution and workflow results to file and database.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.log_dir = Path(self.config.get("log_dir", "./logs/scheduler"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "scheduler.log"
    
    async def log_workflow_start(self, job_id: str):
        """Log the start of a workflow execution."""
        log_entry = {
            "event": "workflow_start",
            "job_id": job_id,
            "timestamp": datetime.now().isoformat()
        }
        await self._write_log(log_entry)
        logger.info("Workflow started", job_id=job_id)
    
    async def log_workflow_completion(self, job_id: str, results: Dict[str, Any]):
        """Log the completion of a workflow execution."""
        log_entry = {
            "event": "workflow_completion",
            "job_id": job_id,
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
        await self._write_log(log_entry)
        logger.info("Workflow completed", job_id=job_id, results=results)
    
    async def log_workflow_failure(self, job_id: str, error: str):
        """Log the failure of a workflow execution."""
        log_entry = {
            "event": "workflow_failure",
            "job_id": job_id,
            "timestamp": datetime.now().isoformat(),
            "error": error
        }
        await self._write_log(log_entry)
        logger.error("Workflow failed", job_id=job_id, error=error)
    
    async def log_step_completion(self, job_id: str, step_name: str, stats: Dict[str, Any]):
        """Log the completion of a workflow step."""
        log_entry = {
            "event": "step_completion",
            "job_id": job_id,
            "step_name": step_name,
            "timestamp": datetime.now().isoformat(),
            "stats": stats
        }
        await self._write_log(log_entry)
        logger.info("Step completed", job_id=job_id, step=step_name, stats=stats)
    
    async def _write_log(self, log_entry: Dict[str, Any]):
        """Write log entry to file."""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error("Failed to write log entry", error=str(e))
    
    async def get_workflow_history(self, limit: int = 10) -> list:
        """Get recent workflow execution history."""
        try:
            if not self.log_file.exists():
                return []
            
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
            
            # Parse and return last 'limit' entries
            entries = []
            for line in lines[-limit:]:
                try:
                    entry = json.loads(line.strip())
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
            
            return entries[::-1]  # Return in reverse chronological order
            
        except Exception as e:
            logger.error("Failed to read workflow history", error=str(e))
            return []


class MockSchedulerLogger:
    """Mock scheduler logger for testing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logs = []
    
    async def log_workflow_start(self, job_id: str):
        """Mock log workflow start."""
        self.logs.append({"event": "workflow_start", "job_id": job_id})
        logger.info("Mock workflow started", job_id=job_id)
    
    async def log_workflow_completion(self, job_id: str, results: Dict[str, Any]):
        """Mock log workflow completion."""
        self.logs.append({"event": "workflow_completion", "job_id": job_id, "results": results})
        logger.info("Mock workflow completed", job_id=job_id)
    
    async def log_workflow_failure(self, job_id: str, error: str):
        """Mock log workflow failure."""
        self.logs.append({"event": "workflow_failure", "job_id": job_id, "error": error})
        logger.error("Mock workflow failed", job_id=job_id, error=error)
    
    async def log_step_completion(self, job_id: str, step_name: str, stats: Dict[str, Any]):
        """Mock log step completion."""
        self.logs.append({"event": "step_completion", "job_id": job_id, "step_name": step_name, "stats": stats})
        logger.info("Mock step completed", job_id=job_id, step=step_name)
    
    async def get_workflow_history(self, limit: int = 10) -> list:
        """Mock get workflow history."""
        return self.logs[-limit:][::-1]
