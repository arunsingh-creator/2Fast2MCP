"""
🤖 AI Employee Onboarding Agent — Custom MCP Server
====================================================
A FastMCP server that exposes onboarding tools for Archestra to orchestrate.

Tools:
  - onboard_new_hire        → Full onboarding flow
  - github_invite_to_org    → Invite to GitHub org & repos
  - slack_send_welcome      → Send Slack welcome + add to channels
  - gdrive_share_docs       → Share Google Drive documents
  - check_onboarding_status → Get real-time progress
  - get_onboarding_checklist→ Role-specific checklist
  - mark_task_complete      → Mark individual tasks done
  - list_all_employees      → List all onboarding employees
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastmcp import FastMCP

from models import Employee, OnboardingTask, TaskStatus
from store import store
from integrations import github_integration, slack_integration, gdrive_integration

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-18s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("onboard.server")

# ── Load workflow templates ──────────────────────────────────────────

WORKFLOWS_DIR = Path(__file__).parent.parent / "workflows"


def _normalize_role(role: str) -> str:
    """Map job titles to workflow file names."""
    role_lower = role.lower().strip()
    # Direct match
    if role_lower in ("engineering", "design", "general"):
        return role_lower
    # Common job title mappings
    engineering_keywords = ["engineer", "developer", "sre", "devops", "backend", "frontend", "fullstack", "swe"]
    design_keywords = ["design", "ux", "ui", "graphic", "illustrat"]
    for kw in engineering_keywords:
        if kw in role_lower:
            return "engineering"
    for kw in design_keywords:
        if kw in role_lower:
            return "design"
    return "general"


def _load_workflow(role: str) -> dict:
    """Load a workflow template by role, falling back to 'general'."""
    normalized = _normalize_role(role)
    for name in [normalized, "general"]:
        path = WORKFLOWS_DIR / f"{name}.json"
        if path.exists():
            return json.loads(path.read_text())
    return {"tasks": [], "channels": [], "docs": [], "repos": []}


def _merge_workflows(role: str) -> dict:
    """Merge role-specific workflow with the general workflow."""
    normalized = _normalize_role(role)
    general = _load_workflow("general")

    # If the role IS general, no merge needed
    if normalized == "general":
        return general

    role_wf = _load_workflow(normalized)

    # Deduplicate tasks by name
    seen_names = set()
    merged_tasks = []
    for t in general.get("tasks", []) + role_wf.get("tasks", []):
        if t["name"] not in seen_names:
            seen_names.add(t["name"])
            merged_tasks.append(t)

    return {
        "tasks": merged_tasks,
        "channels": list(set(general.get("channels", []) + role_wf.get("channels", []))),
        "docs": list(set(general.get("docs", []) + role_wf.get("docs", []))),
        "repos": role_wf.get("repos", []),
    }


# ── FastMCP Server ───────────────────────────────────────────────────

mcp = FastMCP(
    "Onboarding Agent",
    instructions="AI Employee Onboarding Agent — automates new hire setup across GitHub, Slack, and Google Drive",
)


@mcp.tool()
async def onboard_new_hire(
    name: str,
    email: str,
    role: str,
    team: str,
    github_username: Optional[str] = None,
) -> dict:
    """
    🚀 Start the full onboarding process for a new employee.

    This orchestrates the complete workflow:
    1. Creates the employee record
    2. Sends Slack welcome message & adds to channels
    3. Shares Google Drive documents
    4. Invites to GitHub org & repos (if applicable)
    5. Creates a dev environment setup issue

    Args:
        name: Full name of the new hire
        email: Work email address
        role: Job title (e.g., "Software Engineer", "Product Designer")
        team: Team name (e.g., "Platform", "Frontend", "Design")
        github_username: GitHub username (optional, for engineering roles)
    """
    return await _onboard_new_hire_impl(name, email, role, team, github_username)


async def _onboard_new_hire_impl(
    name: str,
    email: str,
    role: str,
    team: str,
    github_username: Optional[str] = None,
) -> dict:
    """Core onboarding logic shared by MCP tool and REST API."""
    logger.info(f"🚀 Starting onboarding for {name} ({role}, {team})")

    # 1. Create employee record
    employee = Employee(
        name=name,
        email=email,
        role=role,
        team=team,
        github_username=github_username,
    )
    store.add_employee(employee)

    # 2. Load & merge workflows
    workflow = _merge_workflows(role)

    # 3. Create tasks from workflow
    tasks = []
    for t in workflow.get("tasks", []):
        tasks.append(OnboardingTask(
            name=t["name"],
            description=t["description"],
            category=t["category"],
        ))
    store.add_tasks(employee.id, tasks)

    results = {"employee_id": employee.id, "name": name, "steps": []}

    # 4. Slack: Welcome DM + channels
    try:
        dm_result = await slack_integration.send_welcome_dm(email, name, role, team)
        results["steps"].append({"step": "slack_welcome_dm", **dm_result})
        _complete_task_by_category(employee.id, "slack", "Send welcome DM")

        channels = workflow.get("channels", [])
        if channels:
            ch_result = await slack_integration.add_to_channels(email, channels)
            results["steps"].append({"step": "slack_channels", "channels": ch_result})
            _complete_task_by_category(employee.id, "slack", "Add to team channels")

        intro_result = await slack_integration.post_intro("#general", name, role, team)
        results["steps"].append({"step": "slack_intro", **intro_result})
        _complete_task_by_category(employee.id, "slack", "Post intro in #general")
    except Exception as e:
        logger.error(f"Slack step failed: {e}")
        results["steps"].append({"step": "slack", "success": False, "error": str(e)})

    # 5. Google Drive: Share docs
    try:
        docs = workflow.get("docs", [])
        if docs:
            doc_result = await gdrive_integration.share_documents(email, docs)
            results["steps"].append({"step": "gdrive_share", "docs": doc_result})
            _complete_task_by_category(employee.id, "gdrive", "Share documents")

        folder_result = await gdrive_integration.create_personal_folder(email, name, team)
        results["steps"].append({"step": "gdrive_folder", **folder_result})
        _complete_task_by_category(employee.id, "gdrive", "Create personal folder")
    except Exception as e:
        logger.error(f"Google Drive step failed: {e}")
        results["steps"].append({"step": "gdrive", "success": False, "error": str(e)})

    # 6. GitHub: Invite & repos (if applicable)
    if github_username:
        try:
            invite_result = await github_integration.invite_to_org(github_username)
            results["steps"].append({"step": "github_invite", **invite_result})
            _complete_task_by_category(employee.id, "github", "Invite to GitHub org")

            repos = workflow.get("repos", [])
            if repos:
                repo_result = await github_integration.grant_repo_access(github_username, repos)
                results["steps"].append({"step": "github_repos", "repos": repo_result})
                _complete_task_by_category(employee.id, "github", "Grant repo access")

            if repos:
                issue_result = await github_integration.create_setup_issue(
                    github_username, repos[0]
                )
                results["steps"].append({"step": "github_issue", **issue_result})
                _complete_task_by_category(employee.id, "github", "Create setup issue")
        except Exception as e:
            logger.error(f"GitHub step failed: {e}")
            results["steps"].append({"step": "github", "success": False, "error": str(e)})

    # 7. Final status
    status = store.get_status(employee.id)
    if status:
        status.update_progress()
        results["progress"] = status.progress_percent
        results["total_tasks"] = len(status.tasks)
        results["completed_tasks"] = sum(
            1 for t in status.tasks if t.status == TaskStatus.COMPLETED
        )

    logger.info(f"✅ Onboarding complete for {name} — {results.get('progress', 0)}%")
    return results


def _complete_task_by_category(employee_id: str, category: str, name_contains: str):
    """Helper to mark a task complete by matching category and partial name."""
    status = store.get_status(employee_id)
    if not status:
        return
    for task in status.tasks:
        if task.category == category and name_contains.lower() in task.name.lower():
            task.status = TaskStatus.COMPLETED
            break
    status.update_progress()


@mcp.tool()
async def github_invite_to_org(
    username: str,
    repos: Optional[list[str]] = None,
    org: Optional[str] = None,
) -> dict:
    """
    Invite a user to the GitHub organization and optionally grant repo access.

    Args:
        username: GitHub username
        repos: List of repository names to grant access to
        org: GitHub organization name (defaults to GITHUB_ORG env var)
    """
    result = {"username": username}
    result["org_invite"] = await github_integration.invite_to_org(username, org)

    if repos:
        result["repo_access"] = await github_integration.grant_repo_access(
            username, repos, org
        )
        result["setup_issue"] = await github_integration.create_setup_issue(
            username, repos[0], org
        )

    return result


@mcp.tool()
async def slack_send_welcome(
    email: str,
    name: str,
    role: str,
    team: str,
    channels: Optional[list[str]] = None,
) -> dict:
    """
    Send a Slack welcome message and add the new hire to channels.

    Args:
        email: Work email of the new hire
        name: Full name
        role: Job title
        team: Team name
        channels: List of Slack channels to add them to (e.g., ["#engineering", "#standup"])
    """
    result = {}
    result["welcome_dm"] = await slack_integration.send_welcome_dm(email, name, role, team)

    if channels:
        result["channels"] = await slack_integration.add_to_channels(email, channels)

    result["intro"] = await slack_integration.post_intro("#general", name, role, team)
    return result


@mcp.tool()
async def gdrive_share_docs(
    email: str,
    doc_keys: Optional[list[str]] = None,
    name: Optional[str] = None,
    team: Optional[str] = None,
) -> dict:
    """
    Share Google Drive documents with the new hire.

    Args:
        email: Work email of the new hire
        doc_keys: List of document keys to share (e.g., ["company-handbook", "engineering-handbook"])
                  Call with no keys to see all available documents.
        name: Full name (for creating personal folder)
        team: Team name (for creating personal folder)
    """
    if not doc_keys:
        return {
            "available_docs": gdrive_integration.list_available_docs(),
            "message": "Pass doc_keys to share specific documents.",
        }

    result = {}
    result["shared"] = await gdrive_integration.share_documents(email, doc_keys)

    if name and team:
        result["personal_folder"] = await gdrive_integration.create_personal_folder(
            email, name, team
        )

    return result


@mcp.tool()
async def check_onboarding_status(employee_id: str) -> dict:
    """
    Check the onboarding progress for an employee.

    Args:
        employee_id: The employee's unique ID (returned from onboard_new_hire)
    """
    return _check_status_impl(employee_id)


def _check_status_impl(employee_id: str) -> dict:
    """Core status check logic shared by MCP tool and REST API."""
    status = store.get_status(employee_id)
    if not status:
        return {"error": f"Employee {employee_id} not found"}

    return {
        "employee": {
            "id": status.employee.id,
            "name": status.employee.name,
            "email": status.employee.email,
            "role": status.employee.role,
            "team": status.employee.team,
            "start_date": status.employee.start_date,
        },
        "progress_percent": status.progress_percent,
        "total_tasks": len(status.tasks),
        "completed_tasks": sum(1 for t in status.tasks if t.status == TaskStatus.COMPLETED),
        "pending_tasks": sum(1 for t in status.tasks if t.status == TaskStatus.PENDING),
        "failed_tasks": sum(1 for t in status.tasks if t.status == TaskStatus.FAILED),
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "category": t.category,
                "status": t.status.value,
                "description": t.description,
            }
            for t in status.tasks
        ],
    }


@mcp.tool()
async def get_onboarding_checklist(role: str) -> dict:
    """
    Get the onboarding checklist template for a specific role.

    Args:
        role: Job role (e.g., "engineering", "design", "general")
    """
    workflow = _merge_workflows(role)
    return {
        "role": role,
        "tasks": workflow.get("tasks", []),
        "channels": workflow.get("channels", []),
        "docs": workflow.get("docs", []),
        "repos": workflow.get("repos", []),
    }


@mcp.tool()
async def complete_task(employee_id: str, task_id: str, details: Optional[str] = None) -> dict:
    """
    Mark an onboarding task as complete.

    Args:
        employee_id: The employee's unique ID
        task_id: The task's unique ID
        details: Optional details/notes about completion
    """
    task = store.mark_task_complete(employee_id, task_id, details)
    if not task:
        return {"error": "Task or employee not found"}

    status = store.get_status(employee_id)
    return {
        "task": {"id": task.id, "name": task.name, "status": task.status.value},
        "progress_percent": status.progress_percent if status else 0,
    }


@mcp.tool()
async def list_all_employees() -> dict:
    """List all employees currently being onboarded."""
    return _list_all_impl()


def _list_all_impl() -> dict:
    """Core list logic shared by MCP tool and REST API."""
    statuses = store.get_all_statuses()
    return {
        "total": len(statuses),
        "employees": [
            {
                "id": s.employee.id,
                "name": s.employee.name,
                "role": s.employee.role,
                "team": s.employee.team,
                "start_date": s.employee.start_date,
                "progress_percent": s.progress_percent,
                "total_tasks": len(s.tasks),
                "completed_tasks": sum(1 for t in s.tasks if t.status == TaskStatus.COMPLETED),
            }
            for s in statuses
        ],
    }


# ── REST API for Dashboard ──────────────────────────────────────────
# The dashboard needs a simple HTTP endpoint to fetch status

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles


async def api_employees(request):
    data = _list_all_impl()
    return JSONResponse(data)


async def api_employee_status(request):
    eid = request.path_params["employee_id"]
    data = _check_status_impl(eid)
    return JSONResponse(data)


async def api_onboard(request):
    body = await request.json()
    data = await _onboard_new_hire_impl(**body)
    return JSONResponse(data)


# Dashboard static files path
DASHBOARD_DIR = Path(__file__).parent.parent / "dashboard"

routes = [
    Route("/api/employees", api_employees),
    Route("/api/employees/{employee_id}", api_employee_status),
    Route("/api/onboard", api_onboard, methods=["POST"]),
]

# Mount dashboard static files if the directory exists
if DASHBOARD_DIR.exists():
    routes.append(Mount("/", app=StaticFiles(directory=str(DASHBOARD_DIR), html=True)))

dashboard_app = Starlette(routes=routes)
dashboard_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Entry Point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import uvicorn

    mode = sys.argv[1] if len(sys.argv) > 1 else "mcp"
    port = int(os.getenv("PORT", "8080"))

    if mode == "api":
        # Run REST API + Dashboard (used in Docker and Railway)
        logger.info(f"🌐 Starting API + Dashboard server on port {port}")
        uvicorn.run(dashboard_app, host="0.0.0.0", port=port)
    elif mode == "sse":
        # Run as MCP server with Streamable HTTP transport (for Archestra Remote MCP)
        mcp_port = int(os.getenv("MCP_PORT", "8000"))
        logger.info(f"🤖 Starting Onboarding MCP Server (Streamable HTTP on port {mcp_port})")
        mcp.run(transport="streamable-http", host="0.0.0.0", port=mcp_port)
    else:
        # Run as MCP server with stdio (default)
        logger.info("🤖 Starting Onboarding MCP Server (stdio)")
        mcp.run(transport="stdio")

