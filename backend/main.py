import os
import re
from datetime import date, datetime
from typing import Generator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./timecapsule.db")
engine_args = {"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    contact: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    handle: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(80), nullable=True)
    password: Mapped[str] = mapped_column(String(255))  # Demo only; use Firebase Auth in production.
    verified: Mapped[bool] = mapped_column(default=False)


class Group(Base):
    __tablename__ = "groups"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    destination: Mapped[str] = mapped_column(String(120))
    member_count: Mapped[int] = mapped_column(Integer, default=1)


class ScrapbookPage(Base):
    __tablename__ = "scrapbook_pages"
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text, default="")
    background: Mapped[str] = mapped_column(String(32), default="#f6efe5")
    group: Mapped[Group] = relationship()


class ItineraryEvent(Base):
    __tablename__ = "itinerary_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    title: Mapped[str] = mapped_column(String(160))
    event_date: Mapped[date] = mapped_column(Date)
    location: Mapped[str] = mapped_column(String(160), default="")


class StepCount(Base):
    __tablename__ = "step_counts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    day: Mapped[date] = mapped_column(Date)
    steps: Mapped[int] = mapped_column(Integer, default=0)


class AccountCreate(BaseModel):
    contact: str
    handle: str
    username: str | None = None
    password: str = Field(min_length=8)


class VerifyRequest(BaseModel):
    contact: str
    code: str = Field(min_length=6, max_length=6)


class LoginRequest(BaseModel):
    login: str
    password: str


class GroupCreate(BaseModel):
    name: str
    destination: str


class EventCreate(BaseModel):
    group_id: int
    title: str
    event_date: date
    location: str = ""


class StepsUpdate(BaseModel):
    user_id: int
    steps: int = Field(ge=0)


app = FastAPI(title="TimeCapsule API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_demo(db: Session) -> None:
    if db.scalar(select(Group.id)):
        return
    group = Group(name="Maui 2026", destination="Maui, Hawaii", member_count=4)
    db.add(group)
    db.flush()
    db.add(ScrapbookPage(group_id=group.id, title="First morning", body="Add photos, notes, and little moments here.", background="#f6efe5"))
    db.add(ItineraryEvent(group_id=group.id, title="Sunrise beach walk", event_date=date.today(), location="Kihei Beach"))
    db.commit()


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_demo(db)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "timecapsule-api"}


@app.post("/auth/account")
def create_account(payload: AccountCreate, db: Session = Depends(get_db)) -> dict:
    if not re.fullmatch(r"@[A-Za-z0-9_]{3,31}", payload.handle):
        raise HTTPException(400, "Handle must start with @ and contain 3-31 letters, numbers, or underscores.")
    if not re.search(r"[A-Za-z]", payload.password) or not re.search(r"\d", payload.password):
        raise HTTPException(400, "Password must contain letters and numbers.")
    if db.scalar(select(User).where((User.contact == payload.contact) | (User.handle == payload.handle))):
        raise HTTPException(409, "Contact or handle is already registered.")
    user = User(**payload.model_dump(), verified=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "contact": user.contact, "handle": user.handle, "verification_required": True, "demo_code": "123456"}


@app.post("/auth/verify")
def verify_account(payload: VerifyRequest, db: Session = Depends(get_db)) -> dict[str, bool]:
    user = db.scalar(select(User).where(User.contact == payload.contact))
    if not user or payload.code != "123456":
        raise HTTPException(400, "Invalid verification code.")
    user.verified = True
    db.commit()
    return {"verified": True}


@app.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where((User.contact == payload.login) | (User.handle == payload.login)))
    if not user or user.password != payload.password:
        raise HTTPException(401, "Invalid login.")
    if not user.verified:
        raise HTTPException(403, "Account must be verified first.")
    return {"id": user.id, "contact": user.contact, "handle": user.handle, "username": user.username}


@app.get("/groups")
def list_groups(db: Session = Depends(get_db)) -> list[dict]:
    return [{"id": g.id, "name": g.name, "destination": g.destination, "member_count": g.member_count} for g in db.scalars(select(Group)).all()]


@app.post("/groups")
def create_group(payload: GroupCreate, db: Session = Depends(get_db)) -> dict:
    group = Group(name=payload.name, destination=payload.destination, member_count=1)
    db.add(group)
    db.commit()
    db.refresh(group)
    return {"id": group.id, "name": group.name, "destination": group.destination, "member_count": group.member_count}


@app.get("/scrapbook/{group_id}")
def list_pages(group_id: int, db: Session = Depends(get_db)) -> list[dict]:
    pages = db.scalars(select(ScrapbookPage).where(ScrapbookPage.group_id == group_id)).all()
    return [{"id": p.id, "title": p.title, "body": p.body, "background": p.background} for p in pages]


@app.get("/calendar/{group_id}")
def list_events(group_id: int, db: Session = Depends(get_db)) -> list[dict]:
    events = db.scalars(select(ItineraryEvent).where(ItineraryEvent.group_id == group_id).order_by(ItineraryEvent.event_date)).all()
    return [{"id": e.id, "title": e.title, "event_date": e.event_date.isoformat(), "location": e.location} for e in events]


@app.post("/calendar/events")
def create_event(payload: EventCreate, db: Session = Depends(get_db)) -> dict:
    event = ItineraryEvent(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"id": event.id, "title": event.title, "event_date": event.event_date.isoformat(), "location": event.location}


@app.get("/steps/{user_id}")
def get_steps(user_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.scalar(select(StepCount).where((StepCount.user_id == user_id) & (StepCount.day == date.today())))
    return {"date": date.today().isoformat(), "steps": row.steps if row else 0}


@app.put("/steps")
def update_steps(payload: StepsUpdate, db: Session = Depends(get_db)) -> dict:
    row = db.scalar(select(StepCount).where((StepCount.user_id == payload.user_id) & (StepCount.day == date.today())))
    if row:
        row.steps = payload.steps
    else:
        db.add(StepCount(user_id=payload.user_id, day=date.today(), steps=payload.steps))
    db.commit()
    return {"date": date.today().isoformat(), "steps": payload.steps}
