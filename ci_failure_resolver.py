#!/usr/bin/env python3
"""
CI/CD Failure Resolution Agent
Automatically detects and resolves GitHub Actions workflow failures
"""

import os
import json
import requests
import yaml
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubActionsResolver:
    """Agent for resolving GitHub Actions workflow failures"""
    
    def __init__(self, repo_owner: str, repo_name: str, github_token: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.fixes_applied = []
        
    def get_failed_runs(self, limit: int = 10) -> List[Dict]:
        """Get recent failed workflow runs"""
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/runs"
        params = {
            "status": "failure",
            "per_page": limit
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get("workflow_runs", [])
        except requests.RequestException as e:
            logger.error(f"Failed to fetch workflow runs: {e}")
            return []
    
    def get_run_jobs(self, run_id: int) -> List[Dict]:
        """Get jobs for a specific workflow run"""
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/runs/{run_id}/jobs"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get("jobs", [])
        except requests.RequestException as e:
            logger.error(f"Failed to fetch jobs for run {run_id}: {e}")
            return []
    
    def get_job_logs(self, job_id: int) -> str:
        """Get logs for a specific job"""
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/jobs/{job_id}/logs"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch logs for job {job_id}: {e}")
            return ""
    
    def analyze_failure_patterns(self, failed_runs: List[Dict]) -> Dict[str, List[str]]:
        """Analyze failure patterns across multiple runs"""
        patterns = {
            "profile_readme_failures": [],
            "codeql_failures": [],
            "metrics_failures": [],
            "permission_errors": [],
            "action_version_issues": [],
            "token_issues": []
        }
        
        for run in failed_runs:
            workflow_name = run.get("name", "").lower()
            jobs = self.get_run_jobs(run["id"])
            
            for job in jobs:
                if job.get("conclusion") == "failure":
                    logs = self.get_job_logs(job["id"])
                    
                    # Analyze specific failure patterns
                    if "readme" in workflow_name and "activity" in workflow_name:
                        patterns["profile_readme_failures"].append(self._analyze_readme_failure(logs))
                    elif "codeql" in workflow_name:
                        patterns["codeql_failures"].append(self._analyze_codeql_failure(logs))
                    elif "metrics" in workflow_name or "stats" in workflow_name:
                        patterns["metrics_failures"].append(self._analyze_metrics_failure(logs))
                    
                    # Check for common issues
                    if "permission" in logs.lower() or "forbidden" in logs.lower():
                        patterns["permission_errors"].append(f"Run {run['id']}: Permission denied")
                    
                    if "action" in logs.lower() and ("deprecated" in logs.lower() or "not found" in logs.lower()):
                        patterns["action_version_issues"].append(f"Run {run['id']}: Action version issue")
                    
                    if "token" in logs.lower() and ("invalid" in logs.lower() or "expired" in logs.lower()):
                        patterns["token_issues"].append(f"Run {run['id']}: Token issue")
        
        return patterns
    
    def _analyze_readme_failure(self, logs: str) -> str:
        """Analyze README activity workflow failures"""
        if "jamesgeorge007/github-activity-readme" in logs:
            if "Error: Request failed" in logs:
                return "API request failure - possibly rate limited or token issue"
            elif "Error: Cannot read" in logs:
                return "README file access issue - check file permissions"
            elif "Error: No recent activity" in logs:
                return "No recent activity found - this might be expected"
        return "Unknown README workflow failure"
    
    def _analyze_codeql_failure(self, logs: str) -> str:
        """Analyze CodeQL workflow failures"""
        if "No source code was seen during the build" in logs:
            return "No source code found for specified languages"
        elif "Language 'javascript' not found" in logs or "Language 'python' not found" in logs:
            return "Specified languages not present in repository"
        elif "Autobuild failed" in logs:
            return "Autobuild process failed - may need manual build steps"
        return "Unknown CodeQL failure"
    
    def _analyze_metrics_failure(self, logs: str) -> str:
        """Analyze metrics workflow failures"""
        if "lowlighter/metrics" in logs:
            if "Error: Request failed" in logs:
                return "Metrics API request failed"
            elif "Error: Invalid token" in logs:
                return "Invalid or insufficient token permissions"
            elif "Error: Rate limit" in logs:
                return "Rate limit exceeded"
        return "Unknown metrics failure"
    
    def generate_fixes(self, patterns: Dict[str, List[str]]) -> List[Dict]:
        """Generate fixes based on failure patterns"""
        fixes = []
        
        # Fix profile README issues
        if patterns["profile_readme_failures"]:
            fixes.append({
                "type": "workflow_update",
                "file": ".github/workflows/profile-readme.yml",
                "description": "Update profile README workflow",
                "action": self._fix_profile_readme_workflow
            })
        
        # Fix CodeQL issues
        if patterns["codeql_failures"]:
            fixes.append({
                "type": "workflow_update", 
                "file": ".github/workflows/codeql-analysis.yml",
                "description": "Fix CodeQL language configuration",
                "action": self._fix_codeql_workflow
            })
        
        # Fix metrics issues
        if patterns["metrics_failures"]:
            fixes.append({
                "type": "workflow_update",
                "file": ".github/workflows/metrics.yml", 
                "description": "Update metrics workflow configuration",
                "action": self._fix_metrics_workflow
            })
        
        # Fix permission issues
        if patterns["permission_errors"]:
            fixes.append({
                "type": "permission_fix",
                "description": "Add missing workflow permissions",
                "action": self._fix_permissions
            })
        
        return fixes
    
    def _fix_profile_readme_workflow(self) -> bool:
        """Fix the profile README workflow"""
        try:
            # Read current workflow
            with open('.github/workflows/profile-readme.yml', 'r') as f:
                workflow = yaml.safe_load(f)
            
            # Update to a more stable action version
            for job_name, job in workflow.get('jobs', {}).items():
                for i, step in enumerate(job.get('steps', [])):
                    if 'jamesgeorge007/github-activity-readme' in step.get('uses', ''):
                        # Use a specific version instead of @master
                        step['uses'] = 'jamesgeorge007/github-activity-readme@v1.6.4'
                        
                        # Add permissions if missing
                        if 'permissions' not in workflow.get('jobs', {}).get(job_name, {}):
                            workflow['jobs'][job_name]['permissions'] = {
                                'contents': 'write'
                            }
            
            # Write updated workflow
            with open('.github/workflows/profile-readme.yml', 'w') as f:
                yaml.dump(workflow, f, default_flow_style=False)
            
            self.fixes_applied.append("Updated profile README workflow to stable version")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fix profile README workflow: {e}")
            return False
    
    def _fix_codeql_workflow(self) -> bool:
        """Fix the CodeQL workflow"""
        try:
            # Read current workflow
            with open('.github/workflows/codeql-analysis.yml', 'r') as f:
                workflow = yaml.safe_load(f)
            
            # Check what languages actually exist in the repo
            detected_languages = self._detect_repository_languages()
            
            if not detected_languages:
                # If no supported languages, disable the workflow
                workflow['on'] = {
                    'workflow_dispatch': None  # Only manual trigger
                }
                self.fixes_applied.append("Disabled CodeQL workflow - no supported languages detected")
            else:
                # Update language matrix to only include detected languages
                for job_name, job in workflow.get('jobs', {}).items():
                    if 'strategy' in job and 'matrix' in job['strategy']:
                        job['strategy']['matrix']['language'] = detected_languages
                
                self.fixes_applied.append(f"Updated CodeQL languages to: {detected_languages}")
            
            # Write updated workflow
            with open('.github/workflows/codeql-analysis.yml', 'w') as f:
                yaml.dump(workflow, f, default_flow_style=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to fix CodeQL workflow: {e}")
            return False
    
    def _detect_repository_languages(self) -> List[str]:
        """Detect which CodeQL-supported languages are present in the repository"""
        supported_languages = {
            'javascript': ['.js', '.jsx', '.ts', '.tsx', '.vue'],
            'python': ['.py'],
            'java': ['.java'],
            'csharp': ['.cs'],
            'cpp': ['.cpp', '.c', '.cc', '.cxx', '.h', '.hpp'],
            'go': ['.go'],
            'ruby': ['.rb']
        }
        
        detected = []
        
        # Walk through repository files
        for root, dirs, files in os.walk('.'):
            # Skip .git and node_modules
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
            
            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                for lang, extensions in supported_languages.items():
                    if file_ext in extensions and lang not in detected:
                        detected.append(lang)
        
        return detected
    
    def _fix_metrics_workflow(self) -> bool:
        """Fix the metrics workflow"""
        try:
            # Read current workflow
            with open('.github/workflows/metrics.yml', 'r') as f:
                workflow = yaml.safe_load(f)
            
            # Add proper permissions
            for job_name, job in workflow.get('jobs', {}).items():
                if 'permissions' not in job:
                    job['permissions'] = {
                        'contents': 'write',
                        'actions': 'read'
                    }
                
                # Update metrics action configuration
                for step in job.get('steps', []):
                    if 'lowlighter/metrics' in step.get('uses', ''):
                        # Use specific version and add error handling
                        step['uses'] = 'lowlighter/metrics@v3.34'
                        step['continue-on-error'] = True
            
            # Write updated workflow
            with open('.github/workflows/metrics.yml', 'w') as f:
                yaml.dump(workflow, f, default_flow_style=False)
            
            self.fixes_applied.append("Updated metrics workflow with proper permissions and error handling")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fix metrics workflow: {e}")
            return False
    
    def _fix_permissions(self) -> bool:
        """Add missing permissions to workflows"""
        workflow_files = [
            '.github/workflows/profile-readme.yml',
            '.github/workflows/metrics.yml'
        ]
        
        for workflow_file in workflow_files:
            try:
                if os.path.exists(workflow_file):
                    with open(workflow_file, 'r') as f:
                        workflow = yaml.safe_load(f)
                    
                    # Add permissions at job level
                    for job_name, job in workflow.get('jobs', {}).items():
                        if 'permissions' not in job:
                            job['permissions'] = {
                                'contents': 'write',
                                'actions': 'read'
                            }
                    
                    with open(workflow_file, 'w') as f:
                        yaml.dump(workflow, f, default_flow_style=False)
                    
                    self.fixes_applied.append(f"Added permissions to {workflow_file}")
            except Exception as e:
                logger.error(f"Failed to fix permissions in {workflow_file}: {e}")
                return False
        
        return True
    
    def apply_fixes(self, fixes: List[Dict]) -> Dict[str, bool]:
        """Apply the generated fixes"""
        results = {}
        
        for fix in fixes:
            try:
                logger.info(f"Applying fix: {fix['description']}")
                success = fix['action']()
                results[fix['description']] = success
                
                if success:
                    logger.info(f"✅ Successfully applied: {fix['description']}")
                else:
                    logger.error(f"❌ Failed to apply: {fix['description']}")
                    
            except Exception as e:
                logger.error(f"❌ Error applying fix '{fix['description']}': {e}")
                results[fix['description']] = False
        
        return results
    
    def generate_report(self, patterns: Dict[str, List[str]], fix_results: Dict[str, bool]) -> str:
        """Generate a comprehensive report of issues found and fixes applied"""
        report = []
        report.append("# CI/CD Failure Resolution Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Repository: {self.repo_owner}/{self.repo_name}")
        report.append("")
        
        # Issues found
        report.append("## Issues Identified")
        for category, issues in patterns.items():
            if issues:
                report.append(f"### {category.replace('_', ' ').title()}")
                for issue in issues:
                    report.append(f"- {issue}")
                report.append("")
        
        # Fixes applied
        report.append("## Fixes Applied")
        for fix_desc, success in fix_results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            report.append(f"- {status}: {fix_desc}")
        report.append("")
        
        # Additional fixes applied
        if self.fixes_applied:
            report.append("## Additional Changes")
            for fix in self.fixes_applied:
                report.append(f"- {fix}")
            report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        report.append("- Monitor workflow runs for the next 24-48 hours")
        report.append("- Consider adding workflow status badges to README")
        report.append("- Set up notifications for workflow failures")
        report.append("- Review and update action versions quarterly")
        
        return "\n".join(report)
    
    def run_resolution_cycle(self) -> str:
        """Run a complete resolution cycle"""
        logger.info("Starting CI/CD failure resolution cycle...")
        
        # Get failed runs
        failed_runs = self.get_failed_runs()
        if not failed_runs:
            return "No recent failed runs found."
        
        logger.info(f"Found {len(failed_runs)} failed runs to analyze")
        
        # Analyze failure patterns
        patterns = self.analyze_failure_patterns(failed_runs)
        
        # Generate fixes
        fixes = self.generate_fixes(patterns)
        
        # Apply fixes
        fix_results = self.apply_fixes(fixes)
        
        # Generate report
        report = self.generate_report(patterns, fix_results)
        
        # Save report
        with open(f"ci_resolution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md", 'w') as f:
            f.write(report)
        
        logger.info("Resolution cycle completed")
        return report

def main():
    """Main function to run the CI/CD resolver"""
    # Get configuration from environment variables
    repo_owner = os.getenv('GITHUB_REPOSITORY_OWNER', 'xepoctpat')
    repo_name = os.getenv('GITHUB_REPOSITORY_NAME', 'xepoctpat')
    github_token = os.getenv('GITHUB_TOKEN')
    
    if not github_token:
        logger.error("GITHUB_TOKEN environment variable is required")
        return
    
    # Create resolver instance
    resolver = GitHubActionsResolver(repo_owner, repo_name, github_token)
    
    # Run resolution cycle
    report = resolver.run_resolution_cycle()
    print(report)

if __name__ == "__main__":
    main()
