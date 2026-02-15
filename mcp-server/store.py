"""In-memory data store for onboarding progress tracking."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from models import Employee, OnboardingStatus, OnboardingTask, TaskStatus


class OnboardingStore:
    """Thread-safe in-memory store with optional JSON persistence."""

    def __init__(self, persist_path: Optional[str] = None):
        self._employees: dict[str, Employee] = {}
        self._statuses: dict[str, OnboardingStatus] = {}
        self._persist_path = persist_path or os.getenv(
            "ONBOARD_DATA_PATH", "data/onboarding.json"
        )
        self._last_mtime: float = 0  # Track file modification time
        self._load()

    # ── Employee Management ──────────────────────────────────────────

    def add_employee(self, employee: Employee) -> Employee:
        self._employees[employee.id] = employee
        self._statuses[employee.id] = OnboardingStatus(employee=employee)
        self._save()
        return employee

    def get_employee(self, employee_id: str) -> Optional[Employee]:
        self._reload()
        return self._employees.get(employee_id)

    def list_employees(self) -> list[Employee]:
        self._reload()
        return list(self._employees.values())

    # ── Task Management ──────────────────────────────────────────────

    def add_tasks(self, employee_id: str, tasks: list[OnboardingTask]):
        status = self._statuses.get(employee_id)
        if status:
            status.tasks.extend(tasks)
            status.update_progress()
            self._save()

    def mark_task_complete(
        self, employee_id: str, task_id: str, details: Optional[str] = None
    ) -> Optional[OnboardingTask]:
        status = self._statuses.get(employee_id)
        if not status:
            return None
        for task in status.tasks:
            if task.id == task_id:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.details = details
                status.update_progress()
                self._save()
                return task
        return None

    def mark_task_failed(
        self, employee_id: str, task_id: str, details: Optional[str] = None
    ) -> Optional[OnboardingTask]:
        status = self._statuses.get(employee_id)
        if not status:
            return None
        for task in status.tasks:
            if task.id == task_id:
                task.status = TaskStatus.FAILED
                task.details = details
                self._save()
                return task
        return None

    # ── Status ───────────────────────────────────────────────────────

    def get_status(self, employee_id: str) -> Optional[OnboardingStatus]:
        self._reload()
        return self._statuses.get(employee_id)

    def get_all_statuses(self) -> list[OnboardingStatus]:
        self._reload()
        return list(self._statuses.values())

    # ── Persistence ──────────────────────────────────────────────────

    def _save(self):
        try:
            path = Path(self._persist_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                eid: status.model_dump(mode="json")
                for eid, status in self._statuses.items()
            }
            path.write_text(json.dumps(data, indent=2, default=str))
        except Exception:
            pass  # Non-critical — in-memory is the source of truth

    def _load(self):
        try:
            path = Path(self._persist_path)
            if path.exists():
                self._last_mtime = path.stat().st_mtime
                data = json.loads(path.read_text())
                for eid, status_data in data.items():
                    status = OnboardingStatus(**status_data)
                    self._statuses[eid] = status
                    self._employees[eid] = status.employee
        except Exception:
            pass  # Start fresh

    def _reload(self):
        """Reload from disk if the file was modified by another process."""
        try:
            path = Path(self._persist_path)
            if path.exists() and path.stat().st_mtime > self._last_mtime:
                self._employees.clear()
                self._statuses.clear()
                self._load()
        except Exception:
            pass


# Singleton instance
store = OnboardingStore()
