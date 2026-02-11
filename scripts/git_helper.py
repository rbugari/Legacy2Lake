"""
Git Helper: Convenient Git operations for prompt management

Provides simple commands for common Git operations on prompts.

Usage:
    python scripts/git_helper.py commit [message]       # Commit prompt changes
    python scripts/git_helper.py diff <file>            # Show diff for file
    python scripts/git_helper.py history <file> [n]     # Show commit history
    python scripts/git_helper.py status                 # Git status for prompts

Author: Development Team
Date: 2026-02-10
Version: 1.0.0
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def run_git_command(args: List[str], capture_output: bool = False) -> Optional[str]:
    """
    Run a git command
    
    Args:
        args: Git command arguments (e.g., ["status", "--short"])
        capture_output: If True, return output as string
    
    Returns:
        Command output if capture_output=True, None otherwise
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=capture_output,
            text=True,
            check=True
        )
        
        if capture_output:
            return result.stdout
        
        return None
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Git command failed: {e}")
        if capture_output and e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return None
    
    except FileNotFoundError:
        print("❌ Git not found. Make sure Git is installed and in PATH")
        return None


def git_commit_prompts(message: Optional[str] = None):
    """
    Commit changes in prompt_lab/ directory
    
    Args:
        message: Commit message (default: "Update prompts")
    """
    message = message or "Update prompts"
    
    print("🔄 Committing prompt changes...\n")
    
    # Check if there are changes
    status = run_git_command(["status", "--short", "prompt_lab/"], capture_output=True)
    
    if not status or status.strip() == "":
        print("✅ No changes to commit in prompt_lab/")
        return
    
    print("📝 Changes to commit:")
    print(status)
    
    # Add changes
    run_git_command(["add", "prompt_lab/"])
    
    # Commit
    run_git_command(["commit", "-m", message])
    
    print(f"✅ Committed: {message}")


def git_diff_prompt(prompt_file: str):
    """
    Show diff for a specific prompt file
    
    Args:
        prompt_file: Path to prompt file (relative to prompt_lab/)
    """
    # Normalize path
    if not prompt_file.startswith("prompt_lab/"):
        prompt_file = f"prompt_lab/{prompt_file}"
    
    print(f"📄 Diff for {prompt_file}\n")
    
    output = run_git_command(["diff", prompt_file], capture_output=True)
    
    if output:
        if output.strip() == "":
            print("No changes")
        else:
            print(output)
    else:
        print("❌ Failed to get diff")


def git_history_prompt(prompt_file: str, limit: int = 10):
    """
    Show commit history for a specific prompt file
    
    Args:
        prompt_file: Path to prompt file (relative to prompt_lab/)
        limit: Number of commits to show
    """
    # Normalize path
    if not prompt_file.startswith("prompt_lab/"):
        prompt_file = f"prompt_lab/{prompt_file}"
    
    print(f"📜 History for {prompt_file} (last {limit} commits)\n")
    
    output = run_git_command([
        "log",
        f"-{limit}",
        "--oneline",
        "--date=short",
        "--format=%h %ad %s",
        prompt_file
    ], capture_output=True)
    
    if output:
        if output.strip() == "":
            print("No commits found (file may be new)")
        else:
            print(output)
    else:
        print("❌ Failed to get history")


def git_status_prompts():
    """Show Git status for prompt_lab/ directory"""
    print("📊 Git Status - prompt_lab/\n")
    
    # Get status
    output = run_git_command(["status", "--short", "prompt_lab/"], capture_output=True)
    
    if output:
        if output.strip() == "":
            print("✅ No changes")
        else:
            print("Changes:")
            print(output)
            
            # Count changes
            lines = output.strip().split('\n')
            modified = sum(1 for line in lines if line.startswith(' M') or line.startswith('M '))
            added = sum(1 for line in lines if line.startswith('A') or line.startswith('??'))
            deleted = sum(1 for line in lines if line.startswith(' D') or line.startswith('D '))
            
            print(f"\n📈 Summary:")
            if added > 0:
                print(f"   ✅ Added: {added}")
            if modified > 0:
                print(f"   📝 Modified: {modified}")
            if deleted > 0:
                print(f"   ❌ Deleted: {deleted}")
    else:
        print("❌ Failed to get status")


def git_show_prompt(prompt_file: str, commit: str = "HEAD"):
    """
    Show content of a prompt file at a specific commit
    
    Args:
        prompt_file: Path to prompt file
        commit: Git commit reference (default: HEAD)
    """
    # Normalize path
    if not prompt_file.startswith("prompt_lab/"):
        prompt_file = f"prompt_lab/{prompt_file}"
    
    print(f"📖 {prompt_file} @ {commit}\n")
    
    output = run_git_command(["show", f"{commit}:{prompt_file}"], capture_output=True)
    
    if output:
        print(output)
    else:
        print("❌ Failed to show file (may not exist at that commit)")


def git_blame_prompt(prompt_file: str):
    """
    Show who last modified each line of a prompt
    
    Args:
        prompt_file: Path to prompt file
    """
    # Normalize path
    if not prompt_file.startswith("prompt_lab/"):
        prompt_file = f"prompt_lab/{prompt_file}"
    
    print(f"👤 Blame for {prompt_file}\n")
    
    output = run_git_command([
        "blame",
        "--date=short",
        prompt_file
    ], capture_output=True)
    
    if output:
        print(output)
    else:
        print("❌ Failed to get blame info")


def print_usage():
    """Print usage information"""
    print(__doc__)
    print("\nAvailable Commands:")
    print("  commit [message]    - Commit changes in prompt_lab/")
    print("  diff <file>         - Show diff for a prompt file")
    print("  history <file> [n]  - Show commit history (last n commits)")
    print("  status              - Show Git status for prompts")
    print("  show <file> [ref]   - Show file content at commit")
    print("  blame <file>        - Show who modified each line")


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command in ["help", "-h", "--help"]:
        print_usage()
    
    elif command == "commit":
        message = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
        git_commit_prompts(message)
    
    elif command == "diff":
        if len(sys.argv) < 3:
            print("❌ Missing file argument")
            print("Usage: python scripts/git_helper.py diff <file>")
            sys.exit(1)
        git_diff_prompt(sys.argv[2])
    
    elif command == "history":
        if len(sys.argv) < 3:
            print("❌ Missing file argument")
            print("Usage: python scripts/git_helper.py history <file> [limit]")
            sys.exit(1)
        
        prompt_file = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        git_history_prompt(prompt_file, limit)
    
    elif command == "status":
        git_status_prompts()
    
    elif command == "show":
        if len(sys.argv) < 3:
            print("❌ Missing file argument")
            print("Usage: python scripts/git_helper.py show <file> [commit]")
            sys.exit(1)
        
        prompt_file = sys.argv[2]
        commit = sys.argv[3] if len(sys.argv) > 3 else "HEAD"
        git_show_prompt(prompt_file, commit)
    
    elif command == "blame":
        if len(sys.argv) < 3:
            print("❌ Missing file argument")
            print("Usage: python scripts/git_helper.py blame <file>")
            sys.exit(1)
        git_blame_prompt(sys.argv[2])
    
    else:
        print(f"❌ Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
