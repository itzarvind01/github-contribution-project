#!/usr/bin/env python3
"""
GitHub Activity Logger
Creates a dated Markdown record of real work you completed, then commits it.
It does not backdate, generate random commits, or create activity without a real entry.
"""
from datetime import date, datetime
from pathlib import Path
import subprocess
import sys

def run(args, check=True):
    return subprocess.run(args, text=True, capture_output=True, check=check)

def git(*args):
    result = run(["git", *args], check=False)
    if result.returncode != 0:
        print(result.stderr.strip() or result.stdout.strip())
        sys.exit(result.returncode)
    return result.stdout.strip()

def main():
    root = Path.cwd()
    if not (root / ".git").exists():
        print("This folder is not a Git repository.")
        print("Run: git init")
        return

    name = git("config", "user.name")
    email = git("config", "user.email")
    if not name or not email:
        print("Set your Git identity first:")
        print('  git config user.name "Your GitHub username"')
        print('  git config user.email "YOUR_VERIFIED_GITHUB_EMAIL"')
        return

    print(f"Git identity: {name} <{email}>")
    print("\nRecord only work you actually completed (coding, debugging, tests, docs, learning project).")
    summary = input("What did you work on today? ").strip()
    if len(summary) < 10:
        print("Please enter a meaningful description (at least 10 characters). Nothing committed.")
        return

    details = input("What changed or what did you learn? ").strip()
    if not details:
        print("Please add a short detail. Nothing committed.")
        return

    today = date.today().isoformat()
    folder = root / "activity"
    folder.mkdir(exist_ok=True)
    log_file = folder / f"{today}.md"

    timestamp = datetime.now().astimezone().isoformat(timespec="minutes")
    entry = (
        f"\n## {timestamp}\n\n"
        f"**Work:** {summary}\n\n"
        f"**Result:** {details}\n"
    )
    with log_file.open("a", encoding="utf-8") as f:
        f.write(entry)

    git("add", str(log_file.relative_to(root)))
    status = git("status", "--porcelain")
    if not status:
        print("No new changes to commit.")
        return

    message = f"Document work: {summary[:60]}"
    git("commit", "-m", message)
    print("\nSaved and committed your real work log.")
    print("Commit date is the actual current date; no historical dates were changed.")

    push = input("Push this commit to GitHub now? (y/N): ").strip().lower()
    if push == "y":
        remotes = git("remote")
        if not remotes:
            print("No remote configured. Add one with:")
            print("  git remote add origin https://github.com/itzarvind01/YOUR_REPO.git")
            print("Then push with: git push -u origin main")
            return
        branch = git("branch", "--show-current")
        git("push", "-u", "origin", branch)
        print("Pushed to GitHub.")
    else:
        print("Not pushed. When ready, push with: git push -u origin main")

if __name__ == "__main__":
    main()
