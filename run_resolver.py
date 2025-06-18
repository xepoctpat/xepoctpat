#!/usr/bin/env python3
"""
Runner script for the CI/CD Failure Resolution Agent
This script can be run manually or scheduled to automatically resolve workflow failures
"""

import os
import sys
import argparse
import logging
from ci_failure_resolver import GitHubActionsResolver

def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('ci_resolver.log')
        ]
    )

def main():
    parser = argparse.ArgumentParser(description='CI/CD Failure Resolution Agent')
    parser.add_argument('--repo-owner', default='xepoctpat', help='GitHub repository owner')
    parser.add_argument('--repo-name', default='xepoctpat', help='GitHub repository name')
    parser.add_argument('--token', help='GitHub token (or set GITHUB_TOKEN env var)')
    parser.add_argument('--dry-run', action='store_true', help='Analyze only, do not apply fixes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--max-runs', type=int, default=10, help='Maximum number of failed runs to analyze')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Get GitHub token
    github_token = args.token or os.getenv('GITHUB_TOKEN')
    if not github_token:
        logger.error("GitHub token is required. Use --token or set GITHUB_TOKEN environment variable")
        sys.exit(1)
    
    try:
        # Create resolver instance
        resolver = GitHubActionsResolver(args.repo_owner, args.repo_name, github_token)
        
        if args.dry_run:
            logger.info("Running in dry-run mode - no fixes will be applied")
            
            # Get failed runs
            failed_runs = resolver.get_failed_runs(args.max_runs)
            if not failed_runs:
                print("✅ No recent failed runs found!")
                return
            
            # Analyze patterns
            patterns = resolver.analyze_failure_patterns(failed_runs)
            
            # Generate fixes (but don't apply)
            fixes = resolver.generate_fixes(patterns)
            
            # Print analysis
            print(f"\n📊 Analysis of {len(failed_runs)} failed runs:")
            for category, issues in patterns.items():
                if issues:
                    print(f"\n{category.replace('_', ' ').title()}:")
                    for issue in issues:
                        print(f"  - {issue}")
            
            print(f"\n🔧 Proposed fixes ({len(fixes)}):")
            for fix in fixes:
                print(f"  - {fix['description']}")
            
            print("\nRun without --dry-run to apply these fixes.")
        
        else:
            # Run full resolution cycle
            logger.info("Starting full resolution cycle...")
            report = resolver.run_resolution_cycle()
            print("\n" + "="*60)
            print(report)
            print("="*60)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
