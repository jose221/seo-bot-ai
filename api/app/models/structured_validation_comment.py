from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Text
from sqlmodel import Column, Field, SQLModel

from app.models.url_validation_comment import CommentStatus


class StructuredValidationComment(SQLModel, table=True):
    __tablename__ = "structured_validation_comments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(foreign_key="structured_validation_tasks.id", index=True)
    item_key: str = Field(sa_column=Column(Text, nullable=False))
    username: str = Field(max_length=150)
    comment: str = Field(sa_column=Column(Text, nullable=False))
    status: CommentStatus = Field(
        default=CommentStatus.PENDING,
        sa_column=Column(String(20), nullable=False, default=CommentStatus.PENDING.value),
    )
    answer: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    answered_at: Optional[datetime] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
