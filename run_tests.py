#!/usr/bin/env python
"""
Test Runner

Simple script to run tests for the framework and applications.
Wraps pytest with Django test configuration and provides coverage reporting.
"""

import os
import sys
import subprocess
import argparse


def run_command(command, description):
    """Run a command and display results"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print('='*60)
    
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"❌ {description} failed!")
        return False
    else:
        print(f"✅ {description} passed!")
        return True


def main():
    parser = argparse.ArgumentParser(description='Run project tests')
    parser.add_argument('--app', help='Run tests for specific app')
    parser.add_argument('--models', action='store_true', help='Run only model tests')
    parser.add_argument('--api', action='store_true', help='Run only API tests')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage report')
    parser.add_argument('--slow', action='store_true', help='Include slow tests')
    parser.add_argument('--parallel', action='store_true', help='Run tests in parallel')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd_parts = ['pytest']
    
    # Test selection
    if args.app:
        cmd_parts.append(f'apps/{args.app}/')
    
    # Test type markers
    markers = []
    if args.models:
        markers.append('models')
    if args.api:
        markers.append('api')
    if not args.slow:
        markers.append('not slow')
    
    if markers:
        cmd_parts.append(f'-m "{" and ".join(markers)}"')
    
    # Coverage
    if args.coverage:
        cmd_parts.extend(['--cov=forsviksbruk_backend', '--cov=apps', '--cov-report=html', '--cov-report=term-missing'])
    
    # Parallel execution
    if args.parallel:
        cmd_parts.append('-n auto')
    
    # Verbosity
    if args.verbose:
        cmd_parts.append('-v')
    
    # Standard options
    cmd_parts.extend(['--tb=short', '--strict-markers'])
    
    command = ' '.join(cmd_parts)
    
    # Run tests
    success = run_command(command, "Project Tests")
    
    if args.coverage and success:
        print(f"\n📊 Coverage report generated in htmlcov/index.html")
    
    if success:
        print(f"\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
