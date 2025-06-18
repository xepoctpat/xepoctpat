# CI/CD Failure Resolution Agent

An intelligent agent that automatically detects and resolves GitHub Actions workflow failures in your repository.

## Features

- **Automatic Failure Detection**: Monitors recent workflow runs and identifies failure patterns
- **Intelligent Analysis**: Analyzes logs to determine root causes of failures
- **Automated Fixes**: Applies common fixes for workflow issues
- **Comprehensive Reporting**: Generates detailed reports of issues found and fixes applied
- **Dry-run Mode**: Test analysis without applying changes
- **Scheduled Execution**: Runs automatically every 6 hours to catch and fix issues quickly

## Supported Fix Types

### Workflow Configuration Issues
- Updates deprecated action versions to stable releases
- Adds missing permissions to workflows
- Fixes language configuration for CodeQL analysis
- Corrects workflow syntax and structure

### Common GitHub Actions Problems
- Profile README activity workflow failures
- CodeQL analysis configuration issues
- Metrics/stats generation failures
- Permission and token-related errors
- Rate limiting and API issues

### Repository-Specific Fixes
- Detects actual languages present in repository
- Configures workflows based on repository content
- Removes or disables workflows for unsupported features

## Usage

### Manual Execution

```bash
# Install dependencies
pip install -r requirements.txt

# Run with dry-run to see what would be fixed
python run_resolver.py --dry-run

# Apply fixes
python run_resolver.py

# Run with custom parameters
python run_resolver.py --repo-owner myorg --repo-name myrepo --token $GITHUB_TOKEN
```

### GitHub Actions Integration

The agent runs automatically via GitHub Actions:

- **Scheduled**: Every 6 hours
- **Manual**: Via workflow_dispatch trigger
- **Dry-run**: Available as input option

### Environment Variables

- `GITHUB_TOKEN`: Required for API access
- `GITHUB_REPOSITORY_OWNER`: Repository owner (auto-detected in Actions)
- `GITHUB_REPOSITORY_NAME`: Repository name (auto-detected in Actions)

## Command Line Options

```
--repo-owner     GitHub repository owner (default: xepoctpat)
--repo-name      GitHub repository name (default: xepoctpat)
--token          GitHub token (or set GITHUB_TOKEN env var)
--dry-run        Analyze only, do not apply fixes
--verbose        Enable verbose logging
--max-runs       Maximum number of failed runs to analyze (default: 10)
```

## How It Works

1. **Fetch Failed Runs**: Retrieves recent failed workflow runs via GitHub API
2. **Analyze Patterns**: Examines job logs to identify common failure patterns
3. **Generate Fixes**: Creates targeted fixes based on identified issues
4. **Apply Changes**: Updates workflow files and configurations
5. **Report Results**: Generates comprehensive reports and commits changes

## Failure Pattern Detection

The agent recognizes and fixes these common patterns:

### Profile README Failures
- API rate limiting issues
- Deprecated action versions
- Missing permissions
- Token configuration problems

### CodeQL Analysis Failures
- Languages not present in repository
- Autobuild failures for unsupported projects
- Missing source code detection

### Metrics Workflow Failures
- API authentication issues
- Rate limiting problems
- Missing permissions for file writes

### General Issues
- Permission errors across workflows
- Deprecated action versions
- Token expiration or invalid tokens

## Generated Reports

Each run generates a detailed report including:

- Issues identified by category
- Fixes applied with success/failure status
- Additional changes made
- Recommendations for ongoing maintenance

Reports are saved as artifacts and can be downloaded from the Actions tab.

## Security Considerations

- Uses repository's `GITHUB_TOKEN` with minimal required permissions
- Only modifies workflow files, never touches source code
- All changes are committed with clear attribution
- Dry-run mode available for testing

## Maintenance

The agent is designed to be self-maintaining:

- Automatically updates action versions to stable releases
- Adapts to repository changes (new languages, removed files)
- Provides recommendations for manual review
- Logs all activities for audit purposes

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure `GITHUB_TOKEN` has `contents: write` permission
2. **No Fixes Applied**: Check if issues are already resolved or require manual intervention
3. **Rate Limiting**: Agent includes backoff and retry logic for API calls

### Logs

Check the following for debugging:
- `ci_resolver.log`: Detailed execution logs
- GitHub Actions logs: Workflow execution details
- Resolution reports: Summary of actions taken

## Contributing

To extend the agent's capabilities:

1. Add new failure pattern detection in `_analyze_*_failure` methods
2. Implement corresponding fix methods
3. Update the `generate_fixes` method to include new fix types
4. Test with dry-run mode before deploying

## License

This agent is part of the repository automation suite and follows the same license as the parent repository.
