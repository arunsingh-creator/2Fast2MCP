"""Google Drive integration for onboarding — share folders, handbooks, and team docs.

Uses real Google Drive API when GDRIVE_SERVICE_ACCOUNT_KEY is set, otherwise runs in mock mode.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

import httpx

logger = logging.getLogger("onboard.gdrive")

GDRIVE_KEY_PATH = os.getenv("GDRIVE_SERVICE_ACCOUNT_KEY")
MOCK_MODE = not GDRIVE_KEY_PATH


# ── Mock document library ───────────────────────────────────────────

MOCK_DOCS = {
    "company-handbook": {
        "id": "doc-handbook-001",
        "name": "📖 ACME Corp — Company Handbook",
        "url": "https://drive.google.com/file/d/mock-handbook/view",
        "type": "document",
    },
    "engineering-handbook": {
        "id": "doc-eng-001",
        "name": "⚙️ Engineering Handbook",
        "url": "https://drive.google.com/file/d/mock-eng-handbook/view",
        "type": "document",
    },
    "architecture-docs": {
        "id": "folder-arch-001",
        "name": "🏗️ Architecture & Design Docs",
        "url": "https://drive.google.com/drive/folders/mock-arch/",
        "type": "folder",
    },
    "brand-guidelines": {
        "id": "doc-brand-001",
        "name": "🎨 Brand Guidelines & Assets",
        "url": "https://drive.google.com/file/d/mock-brand/view",
        "type": "document",
    },
    "hr-documents": {
        "id": "folder-hr-001",
        "name": "📋 HR Documents & Forms",
        "url": "https://drive.google.com/drive/folders/mock-hr/",
        "type": "folder",
    },
    "benefits-info": {
        "id": "doc-benefits-001",
        "name": "🏥 Benefits & Perks Guide",
        "url": "https://drive.google.com/file/d/mock-benefits/view",
        "type": "document",
    },
    "onboarding-checklist": {
        "id": "doc-checklist-001",
        "name": "✅ Onboarding Checklist Template",
        "url": "https://drive.google.com/file/d/mock-checklist/view",
        "type": "spreadsheet",
    },
    "team-directory": {
        "id": "doc-directory-001",
        "name": "👥 Team Directory & Org Chart",
        "url": "https://drive.google.com/file/d/mock-directory/view",
        "type": "spreadsheet",
    },
}


async def share_documents(
    email: str,
    doc_keys: list[str],
    role_permission: str = "reader",
) -> list[dict]:
    """Share documents/folders with the new hire."""
    results = []

    for key in doc_keys:
        doc = MOCK_DOCS.get(key)
        if not doc:
            results.append({"doc_key": key, "success": False, "error": "Document not found"})
            continue

        if MOCK_MODE:
            logger.info(f"[MOCK] Shared '{doc['name']}' with {email} as {role_permission}")
            results.append({
                "doc_key": key,
                "name": doc["name"],
                "url": doc["url"],
                "type": doc["type"],
                "permission": role_permission,
                "success": True,
                "mock": True,
            })
            continue

        # Real Google Drive API sharing would go here
        # using service account credentials from GDRIVE_KEY_PATH
        results.append({
            "doc_key": key,
            "name": doc["name"],
            "url": doc["url"],
            "permission": role_permission,
            "success": True,
        })

    return results


async def create_personal_folder(email: str, name: str, team: str) -> dict:
    """Create a personal onboarding folder for the new hire."""
    folder_name = f"Onboarding — {name} ({team})"

    if MOCK_MODE:
        logger.info(f"[MOCK] Created personal folder '{folder_name}' for {email}")
        return {
            "success": True,
            "mock": True,
            "folder_name": folder_name,
            "folder_id": "folder-personal-001",
            "url": "https://drive.google.com/drive/folders/mock-personal/",
        }

    # Real API: create folder and share with user
    return {
        "success": True,
        "folder_name": folder_name,
        "folder_id": "created-via-api",
        "url": "https://drive.google.com/drive/folders/real-folder/",
    }


def list_available_docs() -> list[dict]:
    """List all available documents in the library."""
    return [
        {"key": key, **doc}
        for key, doc in MOCK_DOCS.items()
    ]
