#!/usr/bin/env python3
"""
Test script for the CI/CD Failure Resolution Agent
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from ci_failure_resolver import GitHubActionsResolver

class TestGitHubActionsResolver(unittest.TestCase):
    """Test cases for the GitHubActionsResolver"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.resolver = GitHubActionsResolver(
            repo_owner="test_owner",
            repo_name="test_repo", 
            github_token="test_token"
        )
    
    def test_initialization(self):
        """Test resolver initialization"""
        self.assertEqual(self.resolver.repo_owner, "test_owner")
        self.assertEqual(self.resolver.repo_name, "test_repo")
        self.assertEqual(self.resolver.github_token, "test_token")
        self.assertEqual(self.resolver.fixes_applied, [])
    
    @patch('requests.get')
    def test_get_failed_runs(self, mock_get):
        """Test fetching failed workflow runs"""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "workflow_runs": [
                {"id": 1, "name": "Test Workflow", "conclusion": "failure"},
                {"id": 2, "name": "Another Workflow", "conclusion": "failure"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test the method
        failed_runs = self.resolver.get_failed_runs(limit=5)
        
        # Assertions
        self.assertEqual(len(failed_runs), 2)
        self.assertEqual(failed_runs[0]["id"], 1)
        mock_get.assert_called_once()
    
    def test_analyze_readme_failure(self):
        """Test README failure analysis"""
        logs_with_api_error = "Error: Request failed with status 403"
        result = self.resolver._analyze_readme_failure(logs_with_api_error)
        self.assertIn("API request failure", result)
        
        logs_with_read_error = "Error: Cannot read property"
        result = self.resolver._analyze_readme_failure(logs_with_read_error)
        self.assertIn("README file access issue", result)
    
    def test_analyze_codeql_failure(self):
        """Test CodeQL failure analysis"""
        logs_no_source = "No source code was seen during the build"
        result = self.resolver._analyze_codeql_failure(logs_no_source)
        self.assertIn("No source code found", result)
        
        logs_lang_not_found = "Language 'python' not found in repository"
        result = self.resolver._analyze_codeql_failure(logs_lang_not_found)
        self.assertIn("not present in repository", result)
    
    def test_detect_repository_languages(self):
        """Test language detection"""
        # Mock os.walk to simulate repository structure
        with patch('os.walk') as mock_walk:
            mock_walk.return_value = [
                ('.', ['src'], ['README.md', 'test.py']),
                ('./src', [], ['main.js', 'utils.py'])
            ]
            
            languages = self.resolver._detect_repository_languages()
            
            # Should detect both Python and JavaScript
            self.assertIn('python', languages)
            self.assertIn('javascript', languages)
    
    def test_generate_fixes(self):
        """Test fix generation based on patterns"""
        patterns = {
            "profile_readme_failures": ["API request failure"],
            "codeql_failures": ["No source code found"],
            "metrics_failures": [],
            "permission_errors": ["Permission denied"],
            "action_version_issues": [],
            "token_issues": []
        }
        
        fixes = self.resolver.generate_fixes(patterns)
        
        # Should generate fixes for README, CodeQL, and permissions
        self.assertEqual(len(fixes), 3)
        fix_types = [fix['type'] for fix in fixes]
        self.assertIn('workflow_update', fix_types)
        self.assertIn('permission_fix', fix_types)
    
    @patch('builtins.open', create=True)
    @patch('yaml.safe_load')
    @patch('yaml.dump')
    def test_fix_profile_readme_workflow(self, mock_yaml_dump, mock_yaml_load, mock_open):
        """Test profile README workflow fix"""
        # Mock workflow content
        mock_workflow = {
            'jobs': {
                'update-readme': {
                    'steps': [
                        {'uses': 'actions/checkout@v4'},
                        {'uses': 'jamesgeorge007/github-activity-readme@master'}
                    ]
                }
            }
        }
        mock_yaml_load.return_value = mock_workflow
        
        # Test the fix
        result = self.resolver._fix_profile_readme_workflow()
        
        # Should succeed and update the action version
        self.assertTrue(result)
        self.assertIn("Updated profile README workflow", self.resolver.fixes_applied[0])
    
    def test_generate_report(self):
        """Test report generation"""
        patterns = {
            "profile_readme_failures": ["API failure"],
            "codeql_failures": [],
            "metrics_failures": ["Token issue"],
            "permission_errors": [],
            "action_version_issues": [],
            "token_issues": []
        }
        
        fix_results = {
            "Fix README workflow": True,
            "Fix metrics workflow": False
        }
        
        report = self.resolver.generate_report(patterns, fix_results)
        
        # Check report content
        self.assertIn("CI/CD Failure Resolution Report", report)
        self.assertIn("Profile Readme Failures", report)
        self.assertIn("✅ SUCCESS: Fix README workflow", report)
        self.assertIn("❌ FAILED: Fix metrics workflow", report)

def run_integration_test():
    """Run a simple integration test if GitHub token is available"""
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("⚠️  GITHUB_TOKEN not set - skipping integration test")
        return
    
    print("🧪 Running integration test...")
    
    try:
        resolver = GitHubActionsResolver("xepoctpat", "xepoctpat", github_token)
        
        # Test API connectivity
        failed_runs = resolver.get_failed_runs(limit=1)
        print(f"✅ API connectivity test passed - found {len(failed_runs)} recent failed runs")
        
        # Test pattern analysis (dry run)
        if failed_runs:
            patterns = resolver.analyze_failure_patterns(failed_runs[:1])
            print(f"✅ Pattern analysis test passed - identified {sum(len(v) for v in patterns.values())} issues")
        
        print("✅ Integration test completed successfully")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")

def main():
    """Main test runner"""
    print("🚀 Starting CI/CD Failure Resolver Tests")
    print("=" * 50)
    
    # Run unit tests
    print("\n📋 Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run integration test if token available
    print("\n🔗 Running integration test...")
    run_integration_test()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()
