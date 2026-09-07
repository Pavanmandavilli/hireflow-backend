from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=20)
    location: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_min: int | None = Field(default=None, ge=0)
    experience_max: int | None = Field(default=None, ge=0)


class JobResponse(JobCreate):
    id: int
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class CandidateSearchRequest(BaseModel):
    job_id: int
    query: str | None = None
    location: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class CandidateResponse(BaseModel):
    id: int
    job_id: int | None
    name: str
    email: str | None
    phone: str | None
    title: str | None
    location: str | None
    source: str | None
    profile_url: str | None
    match_score: float | None
    model_config = {"from_attributes": True}


class CallRequest(BaseModel):
    candidate_id: int
    agent_id: str
    from_phone_number: str | None = None
    timezone: str = "Asia/Kolkata"
    max_retry_count: int = Field(default=2, ge=1, le=10)
    custom_data: dict[str, Any] = Field(default_factory=dict)


class BulkCallRequest(BaseModel):
    candidate_ids: list[int] = Field(min_length=1, max_length=100)
    agent_id: str
    from_phone_number: str | None = None
    timezone: str = "Asia/Kolkata"
    max_retry_count: int = Field(default=2, ge=1, le=10)


class CallResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int | None
    hunar_call_id: str | None
    agent_id: str
    request_id: str | None
    status: str
    lifecycle_status: str | None
    duration_seconds: int | None
    recording_url: str | None
    result: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime | None
    model_config = {"from_attributes": True}
