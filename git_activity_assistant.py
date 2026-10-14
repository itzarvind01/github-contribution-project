#!/usr/bin/env python3
"""
Git Activity Assistant
Detects real changes in the current Git repository, reviews them, and
optionally commits and pushes them. It never fabricates dates or changes.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["git", *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(message or f"git {' '.join(args)} failed")
    return result


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    suffix = " [Y/n] " if default else " [y/N] "
    answer = input(prompt + suffix).strip().lower()
    if not answer:
        return default
    return answer in {"y", "yes"}


def main() -> int:
    if git("rev-parse", "--is-inside-work-tree", check=False).returncode != 0:
        print("Error: run this tool from inside a Git repository.")
        return 1

    branch = git("branch", "--show-current").stdout.strip()
    if not branch:
        print("Error: detached HEAD. Switch to a branch before continuing.")
        return 1

    identity_name = git("config", "user.name", check=False).stdout.strip()
    identity_email = git("config", "user.email", check=False).stdout.strip()
    if not identity_name or not identity_email:
        print("Git author identity is not configured.")
        print('Run: git config user.name "Your Name"')
        print('Run: git config user.email "YOUR_VERIFIED_GITHUB_EMAIL"')
        return 1

    print(f"\nRepository: {Path.cwd()}")
    print(f"Branch:     {branch}")
    print(f"Commit as:  {identity_name} <{identity_email}>")

    status = git("status", "--short").stdout.strip()
    if not status:
        print("\nWorking tree is clean. No real changes to commit.")
        return 0

    print("\nDetected changes:")
    print(status)
    print("\nChange summary:")
    print(git("diff", "--stat").stdout.strip() or "(No unstaged diff summary.)")
    staged = git("diff", "--cached", "--stat").stdout.strip()
    if staged:
        print("\nAlready staged:")
        print(staged)

    print("\nReview the full diff before proceeding:")
    print("  git diff")
    print("  git diff --cached")
    if not ask_yes_no("\nStage all changes shown above? Review first; avoid secrets and generated files."):
        print("No files staged. Nothing committed or pushed.")
        return 0

    git("add", "-A")
    staged_status = git("diff", "--cached", "--name-status").stdout.strip()
    if not staged_status:
        print("No changes were staged. Nothing committed.")
        return 0

    print("\nFiles staged for this commit:")
    print(staged_status)
    if not ask_yes_no("Commit these changes?", default=True):
        print("Commit cancelled. Your changes remain staged.")
        return 0

    message = input("Commit message (e.g. 'Improve input validation'): ").strip()
    if len(message) < 5:
        print("Please provide a meaningful commit message of at least 5 characters.")
        print("Nothing committed.")
        return 1

    git("commit", "-m", message)
    print("\nCommit created using the actual current time.")

    remotes = git("remote").stdout.split()
    if not remotes:
        print("No remote is configured. Add one with git remote add origin <URL>.")
        return 0

    if ask_yes_no("Push this commit to the configured upstream?", default=True):
        upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", check=False)
        if upstream.returncode == 0:
            git("push")
        else:
            remote = remotes[0]
            git("push", "-u", remote, branch)
        print("Push completed.")
    else:
        print("Commit kept locally. Push later with: git push")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"\nGit error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("\nCancelled.")
        raise SystemExit(130)
