"""
Orchestration Logger for Phase 3: AI Orchestration Layer.
Tracks execution time, current module, retry count, API latency, failed requests, and pipeline status.
"""
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import structlog


logger = structlog.get_logger(__name__)


class OrchestrationLogger:
    """
    Comprehensive logging for orchestration pipeline.
    Tracks execution metrics and stores logs separately.
    """
    
    def __init__(self, log_dir: str = "./data/orchestration_logs", max_logs: int = 10000):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.execution_log_file = self.log_dir / "execution_logs.json"
        self.metrics_log_file = self.log_dir / "metrics_logs.json"
        self.failure_log_file = self.log_dir / "failure_logs.json"
        
        self.max_logs = max_logs
        
        # In-memory tracking
        self.execution_logs: List[Dict[str, Any]] = []
        self.metrics = defaultdict(dict)
        self.failure_logs: List[Dict[str, Any]] = []
        
        # Load existing logs
        self._load_logs()
    
    def _load_logs(self) -> None:
        """Load existing logs from storage."""
        if self.execution_log_file.exists():
            try:
                with open(self.execution_log_file, 'r', encoding='utf-8') as f:
                    self.execution_logs = json.load(f)
            except Exception as e:
                logger.error("Failed to load execution logs", error=str(e))
        
        if self.metrics_log_file.exists():
            try:
                with open(self.metrics_log_file, 'r', encoding='utf-8') as f:
                    self.metrics = defaultdict(dict, json.load(f))
            except Exception as e:
                logger.error("Failed to load metrics logs", error=str(e))
        
        if self.failure_log_file.exists():
            try:
                with open(self.failure_log_file, 'r', encoding='utf-8') as f:
                    self.failure_logs = json.load(f)
            except Exception as e:
                logger.error("Failed to load failure logs", error=str(e))
    
    def _save_logs(self) -> None:
        """Save logs to storage."""
        try:
            # Trim if exceeding max
            if len(self.execution_logs) > self.max_logs:
                self.execution_logs = self.execution_logs[-self.max_logs:]
            
            if len(self.failure_logs) > self.max_logs:
                self.failure_logs = self.failure_logs[-self.max_logs:]
            
            with open(self.execution_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.execution_logs, f, indent=2, ensure_ascii=False)
            
            with open(self.metrics_log_file, 'w', encoding='utf-8') as f:
                json.dump(dict(self.metrics), f, indent=2, ensure_ascii=False)
            
            with open(self.failure_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.failure_logs, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error("Failed to save logs", error=str(e))
    
    def log_execution_start(
        self,
        user_id: str,
        session_id: str,
        query: str,
        pipeline_id: str
    ) -> str:
        """
        Log the start of an orchestration execution.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            query: User query
            pipeline_id: Unique pipeline execution ID
            
        Returns:
            Execution ID
        """
        execution_id = f"exec_{pipeline_id}_{int(time.time() * 1000)}"
        
        log_entry = {
            "execution_id": execution_id,
            "user_id": user_id,
            "session_id": session_id,
            "query": query,
            "pipeline_id": pipeline_id,
            "started_at": datetime.utcnow().isoformat(),
            "status": "started",
            "current_module": None,
            "retry_count": 0,
            "steps": []
        }
        
        self.execution_logs.append(log_entry)
        self._save_logs()
        
        logger.info(
            "Execution started",
            execution_id=execution_id,
            user_id=user_id,
            session_id=session_id
        )
        
        return execution_id
    
    def log_module_start(
        self,
        execution_id: str,
        module_name: str,
        step_order: int
    ) -> None:
        """
        Log the start of a module execution.
        
        Args:
            execution_id: Execution identifier
            module_name: Name of the module being executed
            step_order: Order in the pipeline
        """
        # Find execution log
        execution_log = next(
            (log for log in self.execution_logs if log["execution_id"] == execution_id),
            None
        )
        
        if execution_log:
            execution_log["current_module"] = module_name
            execution_log["current_step_order"] = step_order
            execution_log["module_start_time"] = time.time()
            
            step_log = {
                "step_name": module_name,
                "step_order": step_order,
                "status": "running",
                "started_at": datetime.utcnow().isoformat()
            }
            execution_log["steps"].append(step_log)
            
            self._save_logs()
            
            logger.info(
                "Module started",
                execution_id=execution_id,
                module=module_name,
                step_order=step_order
            )
    
    def log_module_complete(
        self,
        execution_id: str,
        module_name: str,
        success: bool,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log the completion of a module execution.
        
        Args:
            execution_id: Execution identifier
            module_name: Name of the module
            success: Whether the module succeeded
            output_data: Output data from the module
            error_message: Error message if failed
        """
        execution_log = next(
            (log for log in self.execution_logs if log["execution_id"] == execution_id),
            None
        )
        
        if execution_log:
            # Calculate duration
            module_start_time = execution_log.get("module_start_time", time.time())
            duration_ms = (time.time() - module_start_time) * 1000
            
            # Update the last step
            if execution_log["steps"]:
                execution_log["steps"][-1]["status"] = "completed" if success else "failed"
                execution_log["steps"][-1]["completed_at"] = datetime.utcnow().isoformat()
                execution_log["steps"][-1]["duration_ms"] = duration_ms
                execution_log["steps"][-1]["output_data"] = output_data
                execution_log["steps"][-1]["error_message"] = error_message
            
            # Update metrics
            self._update_module_metrics(module_name, duration_ms, success)
            
            self._save_logs()
            
            logger.info(
                "Module completed",
                execution_id=execution_id,
                module=module_name,
                success=success,
                duration_ms=duration_ms
            )
    
    def log_retry(
        self,
        execution_id: str,
        module_name: str,
        retry_count: int,
        reason: str
    ) -> None:
        """
        Log a retry attempt.
        
        Args:
            execution_id: Execution identifier
            module_name: Name of the module being retried
            retry_count: Current retry count
            reason: Reason for retry
        """
        execution_log = next(
            (log for log in self.execution_logs if log["execution_id"] == execution_id),
            None
        )
        
        if execution_log:
            execution_log["retry_count"] = retry_count
            
            retry_log = {
                "module": module_name,
                "retry_count": retry_count,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if "retries" not in execution_log:
                execution_log["retries"] = []
            execution_log["retries"].append(retry_log)
            
            self._save_logs()
            
            logger.warning(
                "Retry logged",
                execution_id=execution_id,
                module=module_name,
                retry_count=retry_count,
                reason=reason
            )
    
    def log_api_latency(
        self,
        execution_id: str,
        api_name: str,
        latency_ms: float,
        success: bool
    ) -> None:
        """
        Log API latency.
        
        Args:
            execution_id: Execution identifier
            api_name: Name of the API called
            latency_ms: Latency in milliseconds
            success: Whether the API call succeeded
        """
        execution_log = next(
            (log for log in self.execution_logs if log["execution_id"] == execution_id),
            None
        )
        
        if execution_log:
            api_log = {
                "api_name": api_name,
                "latency_ms": latency_ms,
                "success": success,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if "api_calls" not in execution_log:
                execution_log["api_calls"] = []
            execution_log["api_calls"].append(api_log)
            
            # Update metrics
            self._update_api_metrics(api_name, latency_ms, success)
            
            self._save_logs()
            
            logger.info(
                "API latency logged",
                execution_id=execution_id,
                api=api_name,
                latency_ms=latency_ms,
                success=success
            )
    
    def log_failure(
        self,
        execution_id: str,
        module_name: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None
    ) -> None:
        """
        Log a failure.
        
        Args:
            execution_id: Execution identifier
            module_name: Name of the module that failed
            error_type: Type of error
            error_message: Error message
            stack_trace: Optional stack trace
        """
        failure_log = {
            "execution_id": execution_id,
            "module_name": module_name,
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.failure_logs.append(failure_log)
        
        # Update execution log
        execution_log = next(
            (log for log in self.execution_logs if log["execution_id"] == execution_id),
            None
        )
        
        if execution_log:
            execution_log["status"] = "failed"
            execution_log["error"] = {
                "module": module_name,
                "type": error_type,
                "message": error_message
            }
        
        # Update failure metrics
        self._update_failure_metrics(module_name, error_type)
        
        self._save_logs()
        
        logger.error(
            "Failure logged",
            execution_id=execution_id,
            module=module_name,
            error_type=error_type,
            error_message=error_message
        )
    
    def log_pipeline_complete(
        self,
        execution_id: str,
        success: bool,
        total_duration_ms: float,
        final_status: str
    ) -> None:
        """
        Log the completion of the entire pipeline.
        
        Args:
            execution_id: Execution identifier
            success: Whether the pipeline succeeded
            total_duration_ms: Total execution time in milliseconds
            final_status: Final status of the pipeline
        """
        execution_log = next(
            (log for log in self.execution_logs if log["execution_id"] == execution_id),
            None
        )
        
        if execution_log:
            execution_log["status"] = final_status
            execution_log["success"] = success
            execution_log["completed_at"] = datetime.utcnow().isoformat()
            execution_log["total_duration_ms"] = total_duration_ms
            execution_log["current_module"] = None
            
            self._save_logs()
            
            logger.info(
                "Pipeline completed",
                execution_id=execution_id,
                success=success,
                total_duration_ms=total_duration_ms,
                final_status=final_status
            )
    
    def _update_module_metrics(
        self,
        module_name: str,
        duration_ms: float,
        success: bool
    ) -> None:
        """Update module-level metrics."""
        if module_name not in self.metrics["modules"]:
            self.metrics["modules"][module_name] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_duration_ms": 0,
                "avg_duration_ms": 0,
                "min_duration_ms": float('inf'),
                "max_duration_ms": 0
            }
        
        metrics = self.metrics["modules"][module_name]
        metrics["total_calls"] += 1
        metrics["total_duration_ms"] += duration_ms
        metrics["avg_duration_ms"] = metrics["total_duration_ms"] / metrics["total_calls"]
        metrics["min_duration_ms"] = min(metrics["min_duration_ms"], duration_ms)
        metrics["max_duration_ms"] = max(metrics["max_duration_ms"], duration_ms)
        
        if success:
            metrics["successful_calls"] += 1
        else:
            metrics["failed_calls"] += 1
    
    def _update_api_metrics(
        self,
        api_name: str,
        latency_ms: float,
        success: bool
    ) -> None:
        """Update API-level metrics."""
        if "apis" not in self.metrics:
            self.metrics["apis"] = {}
        
        if api_name not in self.metrics["apis"]:
            self.metrics["apis"][api_name] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_latency_ms": 0,
                "avg_latency_ms": 0,
                "min_latency_ms": float('inf'),
                "max_latency_ms": 0
            }
        
        metrics = self.metrics["apis"][api_name]
        metrics["total_calls"] += 1
        metrics["total_latency_ms"] += latency_ms
        metrics["avg_latency_ms"] = metrics["total_latency_ms"] / metrics["total_calls"]
        metrics["min_latency_ms"] = min(metrics["min_latency_ms"], latency_ms)
        metrics["max_latency_ms"] = max(metrics["max_latency_ms"], latency_ms)
        
        if success:
            metrics["successful_calls"] += 1
        else:
            metrics["failed_calls"] += 1
    
    def _update_failure_metrics(
        self,
        module_name: str,
        error_type: str
    ) -> None:
        """Update failure metrics."""
        if "failures" not in self.metrics:
            self.metrics["failures"] = {}
        
        key = f"{module_name}:{error_type}"
        if key not in self.metrics["failures"]:
            self.metrics["failures"][key] = {
                "module": module_name,
                "error_type": error_type,
                "count": 0
            }
        
        self.metrics["failures"][key]["count"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return dict(self.metrics)
    
    def get_execution_logs(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get execution logs, optionally filtered."""
        logs = self.execution_logs
        
        if user_id:
            logs = [log for log in logs if log.get("user_id") == user_id]
        
        if session_id:
            logs = [log for log in logs if log.get("session_id") == session_id]
        
        # Sort by started_at descending
        logs.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        
        return logs[:limit]
    
    def get_failure_logs(
        self,
        module_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get failure logs, optionally filtered."""
        logs = self.failure_logs
        
        if module_name:
            logs = [log for log in logs if log.get("module_name") == module_name]
        
        # Sort by timestamp descending
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return logs[:limit]
    
    def clear_old_logs(self, days: int = 30) -> int:
        """Clear logs older than specified days."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        old_count = 0
        
        # Clear execution logs
        old_executions = [
            log for log in self.execution_logs
            if log.get("started_at", "") < cutoff_str
        ]
        old_count += len(old_executions)
        self.execution_logs = [
            log for log in self.execution_logs
            if log.get("started_at", "") >= cutoff_str
        ]
        
        # Clear failure logs
        old_failures = [
            log for log in self.failure_logs
            if log.get("timestamp", "") < cutoff_str
        ]
        old_count += len(old_failures)
        self.failure_logs = [
            log for log in self.failure_logs
            if log.get("timestamp", "") >= cutoff_str
        ]
        
        if old_count > 0:
            self._save_logs()
            logger.info("Cleared old logs", count=old_count, days=days)
        
        return old_count


class MockOrchestrationLogger:
    """Mock logger for testing without file I/O."""
    
    def __init__(self):
        self.execution_logs: List[Dict[str, Any]] = []
        self.metrics = defaultdict(dict)
        self.failure_logs: List[Dict[str, Any]] = []
    
    def log_execution_start(self, user_id: str, session_id: str, query: str, pipeline_id: str) -> str:
        execution_id = f"exec_{pipeline_id}_{int(time.time() * 1000)}"
        self.execution_logs.append({
            "execution_id": execution_id,
            "user_id": user_id,
            "session_id": session_id,
            "query": query,
            "pipeline_id": pipeline_id,
            "started_at": datetime.utcnow().isoformat(),
            "status": "started"
        })
        return execution_id
    
    def log_module_start(self, execution_id: str, module_name: str, step_order: int) -> None:
        pass
    
    def log_module_complete(self, execution_id: str, module_name: str, success: bool, output_data: Optional[Dict[str, Any]] = None, error_message: Optional[str] = None) -> None:
        pass
    
    def log_retry(self, execution_id: str, module_name: str, retry_count: int, reason: str) -> None:
        pass
    
    def log_api_latency(self, execution_id: str, api_name: str, latency_ms: float, success: bool) -> None:
        pass
    
    def log_failure(self, execution_id: str, module_name: str, error_type: str, error_message: str, stack_trace: Optional[str] = None) -> None:
        pass
    
    def log_pipeline_complete(self, execution_id: str, success: bool, total_duration_ms: float, final_status: str) -> None:
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        return dict(self.metrics)
    
    def get_execution_logs(self, user_id: Optional[str] = None, session_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self.execution_logs[:limit]
    
    def get_failure_logs(self, module_name: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self.failure_logs[:limit]
    
    def clear_old_logs(self, days: int = 30) -> int:
        return 0
