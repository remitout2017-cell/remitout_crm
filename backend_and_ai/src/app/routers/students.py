from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_cache
from app.schemas.student import StudentCreate, StudentOut, StudentUpdate
from core.cache import Cache, keys
from db.models import Student
from db.session import get_session

router = APIRouter(prefix="/students", tags=["students"])


@router.post("", response_model=StudentOut, status_code=201)
async def create_student(body: StudentCreate, session: AsyncSession = Depends(get_session)):
    student = Student(**body.model_dump())
    session.add(student)
    await session.commit()
    await session.refresh(student)
    return student


@router.get("", response_model=list[StudentOut])
async def list_students(skip: int = 0, limit: int = 25, session: AsyncSession = Depends(get_session)):
    rows = await session.execute(select(Student).order_by(Student.id).offset(skip).limit(min(limit, 100)))
    return rows.scalars().all()


async def _get(session: AsyncSession, student_id: int) -> Student:
    student = await session.get(Student, student_id)
    if student is None:
        raise HTTPException(404, "Student not found")
    return student


@router.get("/{student_id}", response_model=StudentOut)
async def get_student(
    student_id: int, session: AsyncSession = Depends(get_session), cache: Cache = Depends(get_cache)
):
    async def load():
        return StudentOut.model_validate(await _get(session, student_id)).model_dump(mode="json")

    return await cache.get_or_load(keys.student(student_id), load)


@router.patch("/{student_id}", response_model=StudentOut)
async def update_student(
    student_id: int,
    body: StudentUpdate,
    session: AsyncSession = Depends(get_session),
    cache: Cache = Depends(get_cache),
):
    student = await _get(session, student_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(student, k, v)
    try:
        await session.commit()
    finally:
        await cache.delete(keys.student(student_id))  # after commit, so readers refill from new data
    await session.refresh(student)
    return student
