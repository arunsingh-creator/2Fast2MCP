"""GitHub integration for onboarding — invite to org, grant repo access, create setup issues.

Uses real GitHub API when GITHUB_TOKEN is set, otherwise runs in mock mode.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

import httpx

logger = logging.getLogger("onboard.github")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_ORG = os.getenv("GITHUB_ORG", "acme-corp")
GITHUB_API = "https://api.github.com"
MOCK_MODE = not GITHUB_TOKEN


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


async def invite_to_org(username: str, org: Optional[str] = None) -> dict:
    """Invite a user to the GitHub organization."""
    org = org or GITHUB_ORG
    if MOCK_MODE:
        logger.info(f"[MOCK] Invited {username} to GitHub org '{org}'")
        return {
            "success": True,
            "mock": True,
            "message": f"Invited {username} to {org}",
            "invitation_id": "mock-inv-001",
        }

    async with httpx.AsyncClient() as client:
        resp = await client.put(
            f"{GITHUB_API}/orgs/{org}/memberships/{username}",
            headers=_headers(),
            json={"role": "member"},
        )
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"Invited {username} to GitHub org '{org}': {data.get('state')}")
        return {"success": True, "state": data.get("state"), "role": data.get("role")}


async def grant_repo_access(
    username: str, repos: list[str], org: Optional[str] = None, permission: str = "push"
) -> list[dict]:
    """Grant a user access to specific repositories."""
    org = org or GITHUB_ORG
    results = []

    for repo in repos:
        if MOCK_MODE:
            logger.info(f"[MOCK] Granted {username} '{permission}' on {org}/{repo}")
            results.append({
                "repo": repo,
                "success": True,
                "mock": True,
                "permission": permission,
            })
            continue

        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{GITHUB_API}/repos/{org}/{repo}/collaborators/{username}",
                headers=_headers(),
                json={"permission": permission},
            )
            resp.raise_for_status()
            results.append({"repo": repo, "success": True, "permission": permission})
            logger.info(f"Granted {username} '{permission}' on {org}/{repo}")

    return results


async def create_setup_issue(
    username: str, repo: str, org: Optional[str] = None
) -> dict:
    """Create a 'Dev Environment Setup' issue assigned to the new hire."""
    org = org or GITHUB_ORG
    title = f"🚀 Dev Environment Setup — {username}"
    body = f"""## Welcome {username}! 👋

This issue tracks your development environment setup.

### Checklist
- [ ] Clone the repository
- [ ] Install dependencies
- [ ] Set up local environment variables (see `.env.example`)
- [ ] Run the test suite
- [ ] Make your first commit on a feature branch
- [ ] Open your first PR (can be a small README fix!)

### Resources
- [Engineering Handbook](https://wiki.acme-corp.dev/handbook)
- [Git Workflow Guide](https://wiki.acme-corp.dev/git-workflow)
- [Code Review Guidelines](https://wiki.acme-corp.dev/code-review)

_This issue was auto-created by the Onboarding Agent_ 🤖
"""
    if MOCK_MODE:
        logger.info(f"[MOCK] Created setup issue for {username} in {org}/{repo}")
        return {
            "success": True,
            "mock": True,
            "issue_number": 42,
            "title": title,
            "url": f"https://github.com/{org}/{repo}/issues/42",
        }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GITHUB_API}/repos/{org}/{repo}/issues",
            headers=_headers(),
            json={
                "title": title,
                "body": body,
                "assignees": [username],
                "labels": ["onboarding", "good first issue"],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "success": True,
            "issue_number": data["number"],
            "title": data["title"],
            "url": data["html_url"],
        }
