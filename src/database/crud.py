from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.database import models, schema  


def get_users(db: Session):
    return db.query(models.User_Db).all()


def get_specific_user(db: Session, detail: schema.UserLookup):
    if detail.email and detail.name:
        user = db.query(models.User_Db).filter(
            models.User_Db.email == detail.email
        ).first()

    elif detail.email:
        user = db.query(models.User_Db).filter(
            models.User_Db.email == detail.email
        ).first()

    elif detail.name:
        user = db.query(models.User_Db).filter(
            models.User_Db.name == detail.name
        ).first()

    else:
        return {"error": "Please provide either an email or a name."}

    return user if user else {"error": "User not found."}


def create_user(db: Session, user: schema.UserCreate):
    user_data = models.User_Db(
        name=user.name,
        email=user.email,
        preferences=user.preferences,
    )
    db.add(user_data)
    try:
        db.commit()
        db.refresh(user_data)
    except IntegrityError:
        db.rollback()
        raise ValueError(f"A user with email '{user.email}' already exists.")
    return user_data


def update_preferences(db: Session, update_data: schema.UpdatePreferences):
    user = db.query(models.User_Db).filter(
        models.User_Db.email == update_data.email 
    ).first()

    if not user:
        return None

    if update_data.preferences is not None:
        user.preferences = update_data.preferences

    db.commit()
    db.refresh(user)
    return user