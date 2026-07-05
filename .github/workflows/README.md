# GitHub Actions Workflows

This directory contains GitHub Actions workflows for the AI-Native Music Discovery Companion.

## Weekly Scheduler Workflow

**File**: `weekly-scheduler.yml`

### Purpose

Automates the weekly execution of the Phase 6 Scheduler workflow, which:
- Downloads latest reviews from external music review sources
- Generates AI-powered insights using Groq LLM
- Updates frontend components with fresh data
- Executes complete workflow across all phases
- Logs all execution details for monitoring

### Schedule

- **Trigger**: Every Monday at 10:00 AM IST (4:30 AM UTC)
- **Manual Trigger**: Available via GitHub Actions UI

### Required Secrets

Configure the following secrets in your GitHub repository settings:

1. **GROQ_API_KEY**: Your Groq API key for AI-powered insight generation

To add secrets:
1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add the secret name and value
4. Click "Add secret"

### Workflow Steps

1. **Checkout repository**: Clones the repository code
2. **Set up Python**: Configures Python 3.11 environment
3. **Install dependencies**: Installs Phase 6 scheduler dependencies
4. **Create logs directory**: Sets up logging directory
5. **Run weekly scheduler**: Executes the complete weekly workflow
6. **Upload scheduler logs**: Uploads execution logs as artifacts
7. **Create workflow summary**: Generates execution summary

### Artifacts

- **scheduler-logs-{run_number}**: Contains scheduler execution logs
- **Retention**: 30 days

### Manual Execution

To manually trigger the workflow:
1. Go to Actions tab in GitHub repository
2. Select "Weekly Music Discovery Scheduler" workflow
3. Click "Run workflow"
4. Select branch and click "Run workflow"

### Monitoring

- **Workflow Runs**: View in Actions tab
- **Logs**: Download as artifacts from workflow runs
- **Summary**: View in workflow run summary

### Environment Variables

The workflow uses the following environment variables:

```yaml
GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
USE_MOCKS: false
SCHEDULER_ENABLED: true
SCHEDULER_TIMEZONE: Asia/Kolkata
SCHEDULER_DAY_OF_WEEK: mon
SCHEDULER_HOUR: 10
SCHEDULER_MINUTE: 0
LOG_DIR: ./logs/scheduler
LOG_LEVEL: INFO
LOG_FORMAT: json
```

### Troubleshooting

**Workflow fails to start**:
- Check that secrets are properly configured
- Verify the workflow file syntax is correct
- Check GitHub Actions service status

**Scheduler execution fails**:
- Review workflow logs for error details
- Check GROQ_API_KEY validity
- Verify Phase 6 dependencies are installed correctly

**Logs not uploaded**:
- Check that logs directory was created
- Verify artifact upload permissions
- Check available storage space

### Customization

To modify the schedule:
- Edit the `cron` expression in `weekly-scheduler.yml`
- Current: `'30 4 * * 1'` (Monday 4:30 AM UTC = 10:00 AM IST)
- Format: `minute hour day month day_of_week`

To add additional environment variables:
- Add them to the `env` section of the workflow
- Update corresponding secrets if needed

### Security

- Never commit API keys to the repository
- Use GitHub Secrets for sensitive data
- Review workflow permissions regularly
- Limit workflow access to trusted collaborators

### Related Documentation

- [Phase 6 Scheduler Documentation](../../ARCHITECTURE.md#phase-6-scheduler---automated-workflow-execution)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Cron Syntax Reference](https://crontab.guru/)
