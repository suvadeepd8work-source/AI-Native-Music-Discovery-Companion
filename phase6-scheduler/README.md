# Phase 6: Scheduler Module

## Overview

Phase 6 is an automated scheduler that executes the complete music discovery workflow on a weekly basis. It runs every Monday at 10:00 AM IST to ensure the system stays up-to-date with the latest reviews, insights, and recommendations.

## Features

- **Automated Weekly Execution**: Runs every Monday at 10:00 AM IST
- **Review Download**: Downloads latest reviews from multiple music review sources
- **Insight Generation**: Generates AI-powered insights from downloaded reviews
- **Frontend Updates**: Automatically updates frontend with latest data
- **Workflow Orchestration**: Coordinates all phases of the music discovery system
- **Comprehensive Logging**: Stores detailed logs of all scheduler executions
- **Manual Execution**: Supports on-demand manual workflow execution

## Architecture

### Components

1. **Scheduler** (`scheduler.py`): Main scheduler using APScheduler
2. **Workflow Executor** (`workflow_executor.py`): Coordinates all phases
3. **Review Downloader** (`review_downloader.py`): Downloads reviews from external sources
4. **Insight Generator** (`insight_generator.py`): Generates AI-powered insights
5. **Frontend Updater** (`frontend_updater.py`): Updates frontend with latest data
6. **Scheduler Logger** (`scheduler_logger.py`): Logs scheduler execution

### Workflow Execution

The weekly workflow executes the following steps in order:

1. **Download Latest Reviews**
   - Fetches reviews from Pitchfork, Rolling Stone, NME, AllMusic
   - Stores reviews in database for processing

2. **Generate Insights**
   - Analyzes reviews using Groq AI
   - Generates pain points, theme clusters, user segments
   - Creates product insights and executive summary

3. **Update Frontend**
   - Updates insights page with latest data
   - Updates recommendations page
   - Updates history page
   - Clears frontend cache

4. **Execute Complete Workflow**
   - Syncs Phase 1: AI Conversation Engine
   - Syncs Phase 2: Music Recommendation Engine
   - Syncs Phase 3: AI Orchestration
   - Syncs Phase 4: Backend API

## Installation

### Prerequisites

- Python 3.8+
- APScheduler
- Groq API Key (for insight generation)

### Setup

1. Navigate to the scheduler directory:
```bash
cd phase6-scheduler
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Configure scheduler settings in `config.yaml`:
```yaml
scheduler:
  enabled: true
  timezone: "Asia/Kolkata"
  day_of_week: "mon"
  hour: 10
  minute: 0
```

## Running the Scheduler

### Production Mode

Start the scheduler (runs continuously):
```bash
python main.py
```

The scheduler will:
- Start immediately
- Schedule the next run for Monday 10:00 AM IST
- Run automatically every week
- Log all executions to `./logs/scheduler/scheduler.log`

### Manual Execution

Run a single workflow execution manually (for testing):
```bash
python main.py manual
```

### Mock Mode

For testing without real APIs:
```bash
USE_MOCKS=true python main.py
```

## Configuration

Edit `config.yaml` to customize:

- **Scheduler Settings**: timezone, schedule, job defaults
- **Review Sources**: which sources to download from
- **Insight Types**: which insights to generate
- **Frontend URLs**: frontend and API endpoints
- **Workflow URLs**: URLs for each phase
- **Logging Settings**: log directory and format

## API Endpoints

The scheduler does not expose REST endpoints. It runs as a background service.

## Monitoring

### Check Scheduler Status

The scheduler logs its status to the console and log files. Check:
- Console output for real-time status
- `./logs/scheduler/scheduler.log` for detailed execution logs

### View Workflow History

Use the SchedulerLogger to view recent workflow executions:
```python
from scheduler_logger import SchedulerLogger

logger = SchedulerLogger(config)
history = await logger.get_workflow_history(limit=10)
```

## Logging

Logs are stored in `./logs/scheduler/scheduler.log` in JSON format. Each log entry includes:
- Event type (workflow_start, workflow_completion, workflow_failure, step_completion)
- Job ID
- Timestamp
- Results or error details

## Error Handling

- Individual step failures are logged but don't stop the workflow
- Complete workflow failures are logged and can be retried manually
- Misfire grace time of 1 hour allows for delayed executions

## Development

### Project Structure

```
phase6-scheduler/
├── main.py                    # Entry point
├── scheduler.py              # Main scheduler
├── workflow_executor.py      # Workflow orchestration
├── review_downloader.py      # Review download
├── insight_generator.py      # Insight generation
├── frontend_updater.py       # Frontend updates
├── scheduler_logger.py       # Logging
├── config.yaml               # Configuration
├── requirements.txt          # Dependencies
├── .env.example             # Environment template
└── README.md                # This file
```

### Adding New Review Sources

1. Add source to `review_sources` in `config.yaml`
2. Implement download method in `ReviewDownloader`
3. Add to parallel download tasks in `download_latest_reviews`

### Adding New Insight Types

1. Add type to `insight_types` in `config.yaml`
2. Implement generation method in `InsightGenerator`
3. Add to parallel generation tasks in `generate_insights`

## Performance

- **Execution Time**: ~5-10 seconds for complete workflow (mock mode)
- **Parallel Execution**: All steps run in parallel where possible
- **Resource Usage**: Minimal, runs as background service

## Troubleshooting

### Scheduler Not Starting

- Check configuration file syntax
- Verify timezone settings
- Check log files for errors

### Workflow Failures

- Review logs in `./logs/scheduler/scheduler.log`
- Check API connectivity
- Verify environment variables
- Run manual execution for testing

### Missed Executions

- Check system uptime during scheduled time
- Review misfire grace time settings
- Check job store configuration

## Phase Independence

This phase can:
- Run independently without other phases
- Be deployed as a standalone service
- Use mock data when external services are unavailable
- Be tested in isolation

## License

This is part of the AI-Native Music Discovery Companion project.
