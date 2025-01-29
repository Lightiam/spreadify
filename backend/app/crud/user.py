from typing import Optional
from sqlalchemy.orm import Session
from ..schemas.auth import UserCreate, UserUpdate, User
from ..models.user import User as UserModel

def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.email == email).first()

def create_user(db: Session, user: UserCreate) -> UserModel:
    db_user = UserModel(
        email=user.email,
        name=user.name,
        picture=user.picture
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: str, user: UserUpdate) -> Optional[UserModel]:
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        return None
    
    for field, value in user.dict(exclude_unset=True).items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: str) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(UserModel).offset(skip).limit(limit).all()
