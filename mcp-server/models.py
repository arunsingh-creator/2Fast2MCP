"""Pydantic models for the Employee Onboarding Agent."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class OnboardingTask(BaseModel):
    """A single onboarding task."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    description: str
    category: str  # github, slack, gdrive, general
    status: TaskStatus = TaskStatus.PENDING
    completed_at: Optional[datetime] = None
    details: Optional[str] = None


class Employee(BaseModel):
    """A new hire being onboarded."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    email: str
    role: str
    team: str
    github_username: Optional[str] = None
    start_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class OnboardingStatus(BaseModel):
    """Full onboarding status for an employee."""
    employee: Employee
    tasks: list[OnboardingTask] = []
    progress_percent: float = 0.0
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def update_progress(self):
        if not self.tasks:
            self.progress_percent = 0.0
            return
        done = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        self.progress_percent = round((done / len(self.tasks)) * 100, 1)
        if self.progress_percent == 100.0 and not self.completed_at:
            self.completed_at = datetime.now()


class OnboardingRequest(BaseModel):
    """Request to onboard a new employee."""
    name: str
    email: str
    role: str
    team: str
    github_username: Optional[str] = None
