from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
import redis
import json
import os
from sqlalchemy import Column, Integer, String, Boolean, Text, create_engine, and_, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Optional, List

DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/hobbymatch")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = FastAPI()
r = redis.from_url(REDIS_URL, decode_responses=True)

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


class UserProfileDB(Base):
    __tablename__ = "profiles"
    user_id = Column(Integer, primary_key=True)
    name = Column(String)
    hobby = Column(String)
    city = Column(String)
    skill_level = Column(String)
    has_equipment = Column(Boolean)
    bio = Column(Text, nullable=True)
    photo_path = Column(String, nullable=True)
    photo_attachment = Column(String, nullable=True)
    views_count = Column(Integer, default=0)


class LikeDB(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_user_id = Column(Integer)
    to_user_id = Column(Integer)
    notified = Column(Boolean, default=False)


Base.metadata.create_all(bind=engine)

with engine.connect() as conn:
    conn.execute(
        text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS photo_attachment VARCHAR")
    )
    conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UserProfile(BaseModel):
    user_id: int
    name: str = Field(..., min_length=2, max_length=30)
    hobby: str = Field(..., min_length=2, max_length=50)
    city: str = Field(default="Не указан", max_length=50)
    skill_level: str = Field(default="Новичок")
    has_equipment: bool = Field(default=False)
    bio: str = Field(default="Чистый лист", max_length=300)
    photo_path: Optional[str] = None
    photo_attachment: Optional[str] = None

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    user_id: int
    name: str
    hobby: str
    city: str
    skill_level: str
    has_equipment: bool
    bio: Optional[str] = None
    photo_path: Optional[str] = None
    photo_attachment: Optional[str] = None
    views_count: int = 0

    class Config:
        from_attributes = True


class ViewRequest(BaseModel):
    viewer_id: int


class LikeRequest(BaseModel):
    from_user_id: int


class LikedBy(BaseModel):
    user_id: int
    name: str


@app.post("/profiles/")
async def save_profile(profile: UserProfile, db: Session = Depends(get_db)):
    new_user = UserProfileDB(**profile.model_dump())
    db.merge(new_user)
    db.commit()
    r.set(f"profile:{profile.user_id}", profile.model_dump_json(), ex=600)
    return {"status": "ok"}


@app.get("/profiles/{user_id}", response_model=UserProfileResponse)
async def get_profile(user_id: int, db: Session = Depends(get_db)):
    cached = r.get(f"profile:{user_id}")
    if cached:
        data = json.loads(cached)
        user = db.query(UserProfileDB).filter(UserProfileDB.user_id == user_id).first()
        if user:
            data["views_count"] = user.views_count or 0
        return data

    user = db.query(UserProfileDB).filter(UserProfileDB.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    return user


@app.get("/profiles/search/{user_id}")
async def search_partners(user_id: int, db: Session = Depends(get_db)):
    me = db.query(UserProfileDB).filter(UserProfileDB.user_id == user_id).first()
    if not me:
        return []

    results = db.query(UserProfileDB).filter(
        and_(
            UserProfileDB.hobby.ilike(me.hobby),
            UserProfileDB.city.ilike(me.city),
            UserProfileDB.user_id != user_id
        )
    ).all()
    return results


@app.post("/profiles/{user_id}/view")
async def record_view(user_id: int, body: ViewRequest, db: Session = Depends(get_db)):
    if body.viewer_id == user_id:
        return {"status": "ok", "views_count": 0}
    user = db.query(UserProfileDB).filter(UserProfileDB.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    user.views_count = (user.views_count or 0) + 1
    db.commit()
    r.delete(f"profile:{user_id}")
    return {"status": "ok", "views_count": user.views_count}


@app.post("/profiles/{user_id}/like")
async def like_profile(user_id: int, body: LikeRequest, db: Session = Depends(get_db)):
    existing = db.query(LikeDB).filter(
        LikeDB.from_user_id == body.from_user_id,
        LikeDB.to_user_id == user_id
    ).first()
    if existing:
        return {"status": "already_liked"}

    like = LikeDB(from_user_id=body.from_user_id, to_user_id=user_id)
    db.add(like)
    db.commit()
    return {"status": "liked"}


@app.get("/profiles/{user_id}/likes/unread")
async def get_unread_likes(user_id: int, db: Session = Depends(get_db)):
    likes = db.query(LikeDB).filter(
        LikeDB.to_user_id == user_id,
        LikeDB.notified == False
    ).all()
    result = []
    for l in likes:
        p = db.query(UserProfileDB).filter(UserProfileDB.user_id == l.from_user_id).first()
        if p:
            result.append({"user_id": p.user_id, "name": p.name, "like_id": l.id})
    return result


@app.post("/profiles/{user_id}/likes/mark-read")
async def mark_likes_read(user_id: int, db: Session = Depends(get_db)):
    db.query(LikeDB).filter(
        LikeDB.to_user_id == user_id,
        LikeDB.notified == False
    ).update({"notified": True})
    db.commit()
    return {"status": "ok"}


@app.get("/profiles/{user_id}/likes", response_model=List[LikedBy])
async def get_likes(user_id: int, db: Session = Depends(get_db)):
    likes = db.query(LikeDB).filter(
        LikeDB.to_user_id == user_id
    ).order_by(LikeDB.id.desc()).limit(5).all()
    if not likes:
        return []
    profile_map = {}
    for l in likes:
        p = db.query(UserProfileDB).filter(UserProfileDB.user_id == l.from_user_id).first()
        if p:
            profile_map[l.from_user_id] = p.name
    return [{"user_id": uid, "name": name} for uid, name in profile_map.items()]
