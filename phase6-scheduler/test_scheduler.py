"""
Test script for scheduler functionality
"""
import asyncio
import os
import sys

# Set environment variable for mock mode
os.environ["USE_MOCKS"] = "true"

# Import after setting environment variable
from scheduler import MockMusicDiscoveryScheduler
import yaml

async def test_scheduler():
    """Test scheduler with mock components."""
    print("Testing Phase 6 Scheduler...")
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize mock scheduler
    scheduler = MockMusicDiscoveryScheduler(config)
    
    # Start scheduler
    print("Starting scheduler...")
    scheduler.start()
    
    # Get job status
    status = scheduler.get_job_status()
    print(f"Scheduler status: {status}")
    
    # Execute manual workflow
    print("\nExecuting manual workflow...")
    await scheduler.execute_manual_workflow()
    
    # Stop scheduler
    print("\nStopping scheduler...")
    scheduler.stop()
    
    print("\nScheduler test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_scheduler())
