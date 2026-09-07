from __future__ import annotations
from typing import Any
from uuid import uuid4
from app.models.hiring_model import Candidate, HiringCall, Job
from app.repositories.hiring_repository import HiringRepository
from app.schemas.hiring_schema import JobCreate, CandidateSearchRequest, CallRequest, BulkCallRequest
from app.services.hunar_service import HunarService
from app.services.people_search_service import PeopleSearchService


class HiringService:
    def __init__(self, repo: HiringRepository, hunar: HunarService | None = None, people: PeopleSearchService | None = None):
        self.repo = repo; self.hunar = hunar or HunarService(); self.people = people or PeopleSearchService()

    async def create_job(self, payload: JobCreate) -> Job:
        return await self.repo.create_job(Job(**payload.model_dump()))

    async def search_candidates(self, payload: CandidateSearchRequest) -> list[Candidate]:
        job = await self.repo.get_job(payload.job_id)
        if not job: raise ValueError("Job not found")
        query = payload.query or (job.skills[0] if job.skills else job.title)
        raw = await self.people.search(query=query, location=payload.location or job.location, limit=payload.limit)
        candidates = []
        for item in raw:
            name = item.get("full_name") or item.get("name") or "Unknown candidate"
            title = item.get("job_title") or item.get("title")
            text = f"{name} {title or ''}".lower()
            skill_hits = sum(1 for s in job.skills if s.lower() in text)
            score = min(99.0, 60.0 + skill_hits * 8.0)
            c = Candidate(job_id=job.id, name=name, email=item.get("work_email") or item.get("email"), phone=item.get("mobile_phone") or item.get("phone"), title=title, location=item.get("location_name") or item.get("location"), source=self.people.active_source, profile_url=item.get("linkedin_url") or item.get("profile_url"), match_score=score, raw_data=item)
            candidates.append(await self.repo.upsert_candidate(c))
        return candidates

    async def create_call(self, payload: CallRequest) -> HiringCall:
        candidate = await self.repo.get_candidate(payload.candidate_id)
        if not candidate: raise ValueError("Candidate not found")
        request_id = f"hire-{uuid4()}"
        custom_data = {"candidate_id": candidate.id, "job_id": candidate.job_id, **payload.custom_data}
        hunar_payload: dict[str, Any] = {"agent_id": payload.agent_id, "callee_name": candidate.name, "mobile_number": candidate.phone, "custom_data": custom_data, "request_id": request_id}
        if payload.from_phone_number: hunar_payload["from_phone_number"] = payload.from_phone_number
        hunar_payload["retry_config"] = {"max_retry_count": payload.max_retry_count, "retry_interval_hours": 3}
        result = await self.hunar.create_call(hunar_payload)
        call = HiringCall(candidate_id=candidate.id, job_id=candidate.job_id, hunar_call_id=str(result.get("id")) if result.get("id") else None, agent_id=payload.agent_id, request_id=request_id, status=result.get("status", "QUEUED"), lifecycle_status=result.get("lifecycle_status"), duration_seconds=result.get("duration_seconds"), recording_url=result.get("recording_url"), result=result.get("result"), custom_data=result.get("custom_data") or custom_data)
        return await self.repo.create_call(call)

    async def create_bulk_calls(self, payload: BulkCallRequest) -> list[HiringCall]:
        candidates = [await self.repo.get_candidate(i) for i in payload.candidate_ids]
        candidates = [c for c in candidates if c is not None]
        if not candidates: raise ValueError("No valid candidates found")
        request_id = f"bulk-{uuid4()}"
        data = [{"callee_name": c.name, "mobile_number": c.phone, "custom_data": {"candidate_id": c.id, "job_id": c.job_id}} for c in candidates]
        hunar_payload = {"agent_id": payload.agent_id, "request_id": request_id, "data": data}
        if payload.from_phone_number: hunar_payload["from_phone_number"] = payload.from_phone_number
        result = await self.hunar.create_bulk_calls(hunar_payload)
        returned = result.get("results", result.get("data", result if isinstance(result, list) else []))
        calls: list[HiringCall] = []
        by_name = {c.name: c for c in candidates}
        for item in returned:
            c = by_name.get(item.get("callee_name"))
            if not c: continue
            calls.append(await self.repo.create_call(HiringCall(candidate_id=c.id, job_id=c.job_id, hunar_call_id=str(item.get("id")) if item.get("id") else None, agent_id=payload.agent_id, request_id=request_id, status=item.get("status", "QUEUED"), lifecycle_status=item.get("lifecycle_status"), custom_data=item.get("custom_data"))))
        return calls

    async def process_webhook(self, payload: dict[str, Any]) -> HiringCall | None:
        hunar_id = payload.get("id") or payload.get("call_id") or payload.get("call", {}).get("id")
        if not hunar_id: return None
        call = await self.repo.get_call_by_hunar_id(str(hunar_id))
        if not call: return None
        call.status = payload.get("status", call.status)
        call.lifecycle_status = payload.get("lifecycle_status", call.lifecycle_status)
        call.duration_seconds = payload.get("duration_seconds", call.duration_seconds)
        call.recording_url = payload.get("recording_url", call.recording_url)
        call.result = payload.get("result", call.result)
        await self.repo.db.flush(); await self.repo.db.refresh(call)
        return call
