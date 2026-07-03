"""
Workflow Executor
Executes the complete music discovery workflow by coordinating all phases.
"""
import asyncio
import structlog
from typing import Dict, Any, Optional
from datetime import datetime


logger = structlog.get_logger(__name__)


class WorkflowExecutor:
    """
    Executes the complete music discovery workflow by coordinating all phases.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.phase1_url = self.config.get("phase1_url", "http://localhost:8001")
        self.phase2_url = self.config.get("phase2_url", "http://localhost:8002")
        self.phase3_url = self.config.get("phase3_url", "http://localhost:8003")
        self.phase4_url = self.config.get("phase4_url", "http://localhost:8005")
    
    async def execute_workflow(self) -> Dict[str, Any]:
        """
        Execute the complete workflow:
        1. Trigger Phase 1 conversation engine sync
        2. Trigger Phase 2 recommendation engine sync
        3. Trigger Phase 3 orchestration sync
        4. Trigger Phase 4 backend API sync
        5. Aggregate results
        """
        start_time = datetime.now()
        results = {}
        
        try:
            logger.info("Starting complete workflow execution")
            
            # Execute all phases in parallel
            phase1_result, phase2_result, phase3_result, phase4_result = await asyncio.gather(
                self._sync_phase1(),
                self._sync_phase2(),
                self._sync_phase3(),
                self._sync_phase4(),
                return_exceptions=True
            )
            
            # Collect results
            results["phase1"] = self._handle_result(phase1_result, "Phase 1")
            results["phase2"] = self._handle_result(phase2_result, "Phase 2")
            results["phase3"] = self._handle_result(phase3_result, "Phase 3")
            results["phase4"] = self._handle_result(phase4_result, "Phase 4")
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            results["execution_time_seconds"] = execution_time
            results["status"] = "completed"
            results["timestamp"] = datetime.now().isoformat()
            
            logger.info(
                "Workflow execution completed",
                execution_time=execution_time,
                phase1_status=results["phase1"]["status"],
                phase2_status=results["phase2"]["status"],
                phase3_status=results["phase3"]["status"],
                phase4_status=results["phase4"]["status"]
            )
            
            return results
            
        except Exception as e:
            logger.error("Workflow execution failed", error=str(e))
            results["status"] = "failed"
            results["error"] = str(e)
            results["timestamp"] = datetime.now().isoformat()
            return results
    
    async def _sync_phase1(self) -> Dict[str, Any]:
        """Sync Phase 1: AI Conversation Engine."""
        logger.info("Syncing Phase 1: AI Conversation Engine")
        # In production, this would call Phase 1's sync endpoint
        await asyncio.sleep(1)  # Simulate work
        return {"status": "success", "synced_records": 100}
    
    async def _sync_phase2(self) -> Dict[str, Any]:
        """Sync Phase 2: Music Recommendation Engine."""
        logger.info("Syncing Phase 2: Music Recommendation Engine")
        # In production, this would call Phase 2's sync endpoint
        await asyncio.sleep(2)  # Simulate work
        return {"status": "success", "synced_records": 50}
    
    async def _sync_phase3(self) -> Dict[str, Any]:
        """Sync Phase 3: AI Orchestration."""
        logger.info("Syncing Phase 3: AI Orchestration")
        # In production, this would call Phase 3's sync endpoint
        await asyncio.sleep(1)  # Simulate work
        return {"status": "success", "synced_records": 25}
    
    async def _sync_phase4(self) -> Dict[str, Any]:
        """Sync Phase 4: Backend API."""
        logger.info("Syncing Phase 4: Backend API")
        # In production, this would call Phase 4's sync endpoint
        await asyncio.sleep(1)  # Simulate work
        return {"status": "success", "synced_records": 75}
    
    def _handle_result(self, result: Any, phase_name: str) -> Dict[str, Any]:
        """Handle result from a phase execution."""
        if isinstance(result, Exception):
            logger.error(f"{phase_name} failed", error=str(result))
            return {
                "status": "failed",
                "error": str(result),
                "synced_records": 0
            }
        return result


class MockWorkflowExecutor:
    """Mock workflow executor for testing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    async def execute_workflow(self) -> Dict[str, Any]:
        """Mock workflow execution."""
        logger.info("Mock workflow execution")
        await asyncio.sleep(1)
        return {
            "status": "completed",
            "phase1": {"status": "success", "synced_records": 100},
            "phase2": {"status": "success", "synced_records": 50},
            "phase3": {"status": "success", "synced_records": 25},
            "phase4": {"status": "success", "synced_records": 75},
            "execution_time_seconds": 1.0,
            "timestamp": datetime.now().isoformat()
        }
