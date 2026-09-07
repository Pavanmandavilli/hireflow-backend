from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.hiring_model import Candidate, HiringCall, Job


class HiringRepository:
    def __init__(self, db: AsyncSession): self.db = db

    async def create_job(self, job: Job) -> Job:
        self.db.add(job); await self.db.flush(); await self.db.refresh(job); return job

    async def get_job(self, job_id: int) -> Job | None: return await self.db.get(Job, job_id)

    async def list_jobs(self) -> list[Job]:
        result = await self.db.execute(select(Job).order_by(Job.created_at.desc()))
        return list(result.scalars().all())

    async def get_candidate(self, candidate_id: int) -> Candidate | None: return await self.db.get(Candidate, candidate_id)

    async def upsert_candidate(self, candidate: Candidate) -> Candidate:
        self.db.add(candidate); await self.db.flush(); await self.db.refresh(candidate); return candidate

    async def list_candidates(self, job_id: int | None = None) -> list[Candidate]:
        stmt = select(Candidate).order_by(Candidate.match_score.desc().nullslast(), Candidate.created_at.desc())
        if job_id is not None: stmt = stmt.where(Candidate.job_id == job_id)
        result = await self.db.execute(stmt); return list(result.scalars().all())

    async def create_call(self, call: HiringCall) -> HiringCall:
        self.db.add(call); await self.db.flush(); await self.db.refresh(call); return call

    async def get_call(self, call_id: int) -> HiringCall | None: return await self.db.get(HiringCall, call_id)

    async def get_call_by_hunar_id(self, hunar_id: str) -> HiringCall | None:
        result = await self.db.execute(select(HiringCall).where(HiringCall.hunar_call_id == hunar_id))
        return result.scalar_one_or_none()

    async def list_calls(self, job_id: int | None = None) -> list[HiringCall]:
        stmt = select(HiringCall).order_by(HiringCall.created_at.desc())
        if job_id is not None: stmt = stmt.where(HiringCall.job_id == job_id)
        result = await self.db.execute(stmt); return list(result.scalars().all())
