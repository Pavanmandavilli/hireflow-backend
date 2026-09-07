from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.hiring_repository import HiringRepository
from app.schemas.hiring_schema import JobCreate, JobResponse, CandidateSearchRequest, CandidateResponse, CallRequest, BulkCallRequest, CallResponse
from app.services.hiring_service import HiringService
from app.services.hunar_service import HunarService, HunarAPIError

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db)) -> HiringService:
    return HiringService(HiringRepository(db))


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(service: HiringService = Depends(get_service)):
    return await service.repo.list_jobs()


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(payload: JobCreate, service: HiringService = Depends(get_service)):
    return await service.create_job(payload)


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, service: HiringService = Depends(get_service)):
    job = await service.repo.get_job(job_id)
    if not job: raise HTTPException(404, "Job not found")
    return job


@router.post("/candidates/search", response_model=list[CandidateResponse])
async def search_candidates(payload: CandidateSearchRequest, service: HiringService = Depends(get_service)):
    try: return await service.search_candidates(payload)
    except ValueError as e: raise HTTPException(404, str(e)) from e


@router.get("/candidates", response_model=list[CandidateResponse])
async def list_candidates(job_id: int | None = None, service: HiringService = Depends(get_service)):
    return await service.repo.list_candidates(job_id)


@router.get("/hunar/agents")
async def list_hunar_agents():
    try: return await HunarService().list_agents()
    except HunarAPIError as e: raise HTTPException(502, str(e)) from e


@router.get("/hunar/numbers")
async def list_hunar_numbers():
    try: return await HunarService().list_numbers()
    except HunarAPIError as e: raise HTTPException(502, str(e)) from e


@router.post("/calls", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
async def create_call(payload: CallRequest, service: HiringService = Depends(get_service)):
    try: return await service.create_call(payload)
    except ValueError as e: raise HTTPException(404, str(e)) from e
    except HunarAPIError as e: raise HTTPException(502, str(e)) from e


@router.post("/calls/bulk", response_model=list[CallResponse], status_code=status.HTTP_201_CREATED)
async def create_bulk_calls(payload: BulkCallRequest, service: HiringService = Depends(get_service)):
    try: return await service.create_bulk_calls(payload)
    except ValueError as e: raise HTTPException(400, str(e)) from e
    except HunarAPIError as e: raise HTTPException(502, str(e)) from e


@router.get("/calls", response_model=list[CallResponse])
async def list_calls(job_id: int | None = None, service: HiringService = Depends(get_service)):
    return await service.repo.list_calls(job_id)


@router.get("/calls/{call_id}", response_model=CallResponse)
async def get_call(call_id: int, service: HiringService = Depends(get_service)):
    call = await service.repo.get_call(call_id)
    if not call: raise HTTPException(404, "Call not found")
    return call


@router.post("/webhooks/hunar", status_code=200)
async def hunar_webhook(request: Request, service: HiringService = Depends(get_service)):
    payload: dict[str, Any] = await request.json()
    call = await service.process_webhook(payload)
    return {"received": True, "updated": call is not None}
