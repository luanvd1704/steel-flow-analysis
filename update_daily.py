#!/usr/bin/env python3
"""
Daily Data Update Script for Steel Flow Analysis
Automates: Fetch data → Export Excel → Git commit & push

Usage:
    python update_daily.py
"""

import subprocess
import sys
import datetime
from pathlib import Path
import time


def print_header():
    """Print script header"""
    print("=" * 60)
    print("     Steel Flow Analysis - Daily Data Update")
    print("=" * 60)
    print()


def print_timestamp(message):
    """Print message with timestamp"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def run_command(cmd, cwd=None, check=True):
    """
    Run shell command and return result

    Args:
        cmd: Command as list or string
        cwd: Working directory
        check: Raise exception on error

    Returns:
        subprocess.CompletedProcess
    """
    if isinstance(cmd, str):
        cmd = cmd.split()

    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False  # We'll handle errors manually
    )

    if check and result.returncode != 0:
        print(f"Error: Command failed with code {result.returncode}")
        print(f"Command: {' '.join(cmd)}")
        print(f"Stderr: {result.stderr}")
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)

    return result


def fetch_and_export_data(project_root):
    """
    Step 1: Fetch data from APIs and export to Excel

    Args:
        project_root: Path to project root directory

    Returns:
        bool: True if successful, False otherwise
    """
    print_timestamp("Starting data fetch and export...")
    print()

    stock_analyst_dir = project_root / "Stock-analyst"
    export_script = stock_analyst_dir / "export_excel.py"

    if not export_script.exists():
        print(f"Error: export_excel.py not found at {export_script}")
        return False

    try:
        # Run export_excel.py
        print_timestamp("Running export_excel.py...")
        result = run_command(
            [sys.executable, "export_excel.py"],
            cwd=stock_analyst_dir,
            check=False  # Don't raise exception, handle errors gracefully
        )

        # Print output
        if result.stdout:
            print(result.stdout)

        if result.returncode != 0:
            print_timestamp("Warning: export_excel.py completed with errors")
            if result.stderr:
                print("Stderr:", result.stderr)
            print_timestamp("Continuing with git operations (flexible error handling)...")
            return True  # Still return True to continue with git operations
        else:
            print_timestamp("Data fetch and export completed successfully!")

        return True

    except Exception as e:
        print_timestamp(f"Error during data fetch: {e}")
        print_timestamp("Continuing with git operations (flexible error handling)...")
        return True  # Continue even on error, per user requirement


def check_excel_files(project_root):
    """
    Check if Excel files exist and were updated

    Args:
        project_root: Path to project root directory

    Returns:
        list: List of Excel files that exist
    """
    stock_analyst_dir = project_root / "Stock-analyst"
    excel_files = [
        "steel_foreign_trading.xlsx",
        "steel_self_trading.xlsx",
        "steel_valuation.xlsx",
        "vnindex_market.xlsx"
    ]

    print()
    print_timestamp("Checking Excel files...")

    existing_files = []
    for filename in excel_files:
        filepath = stock_analyst_dir / filename
        if filepath.exists():
            file_size = filepath.stat().st_size / 1024  # KB
            print_timestamp(f"✓ {filename} ({file_size:.1f} KB)")
            existing_files.append(f"Stock-analyst/{filename}")
        else:
            print_timestamp(f"✗ {filename} (not found)")

    return existing_files


def git_operations(project_root, files_to_commit):
    """
    Step 2: Git add, commit, and push

    Args:
        project_root: Path to project root directory
        files_to_commit: List of files to commit

    Returns:
        bool: True if successful, False otherwise
    """
    print()
    print_timestamp("Starting git operations...")

    if not files_to_commit:
        print_timestamp("Warning: No files to commit")
        return False

    try:
        # Check git status first
        result = run_command(["git", "status", "--porcelain"], cwd=project_root, check=True)

        if not result.stdout.strip():
            print_timestamp("No changes to commit (files already up to date)")
            return True

        # Git add
        print_timestamp("Adding files to git...")
        run_command(["git", "add"] + files_to_commit, cwd=project_root, check=True)
        print_timestamp("✓ Files staged")

        # Generate commit message
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        commit_message = f"Update data: {today}"

        # Git commit
        print_timestamp(f"Committing: {commit_message}")
        result = run_command(
            ["git", "commit", "-m", commit_message],
            cwd=project_root,
            check=True
        )

        # Extract commit hash
        commit_hash = None
        if result.stdout:
            # Parse commit hash from output (format: "[main abc1234] message")
            for line in result.stdout.split('\n'):
                if line.strip().startswith('['):
                    parts = line.split()
                    if len(parts) >= 2:
                        commit_hash = parts[1].rstrip(']')
                        break

        if commit_hash:
            print_timestamp(f"✓ Committed: {commit_hash}")
        else:
            print_timestamp("✓ Committed successfully")

        # Git push
        print_timestamp("Pushing to origin/main...")
        result = run_command(["git", "push", "origin", "main"], cwd=project_root, check=True)
        print_timestamp("✓ Pushed to origin/main")

        return True

    except subprocess.CalledProcessError as e:
        print_timestamp(f"Git operation failed: {e}")
        if e.stderr:
            print("Error details:", e.stderr)
        return False
    except Exception as e:
        print_timestamp(f"Unexpected error during git operations: {e}")
        return False


def print_summary(success, duration):
    """Print final summary"""
    print()
    print("=" * 60)
    if success:
        print("     Update completed successfully!")
    else:
        print("     Update completed with errors")
    print("=" * 60)
    print(f"Duration: {duration}")
    print()

    if success:
        print("Next steps:")
        print("1. GitHub received the commit")
        print("2. Streamlit Cloud will detect changes (~1-2 min)")
        print("3. App will redeploy automatically (~1-2 min)")
        print("4. Users will see fresh data within ~5 minutes")
        print()


def main():
    """Main execution function"""
    start_time = time.time()

    # Print header
    print_header()

    # Get project root
    project_root = Path(__file__).parent.resolve()
    print_timestamp(f"Project root: {project_root}")
    print()

    # Step 1: Fetch and export data
    fetch_success = fetch_and_export_data(project_root)

    if not fetch_success:
        print_timestamp("Data fetch failed. Aborting.")
        sys.exit(1)

    # Check Excel files
    files_to_commit = check_excel_files(project_root)

    # Step 2: Git operations
    git_success = git_operations(project_root, files_to_commit)

    # Calculate duration
    end_time = time.time()
    duration_seconds = int(end_time - start_time)
    duration_str = f"{duration_seconds // 60}m {duration_seconds % 60}s"

    # Print summary
    overall_success = fetch_success and git_success
    print_summary(overall_success, duration_str)

    # Exit with appropriate code
    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
