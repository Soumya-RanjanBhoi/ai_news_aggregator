from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from src.database.database import engine, SessionLocal, get_db, Base
from src.database import schema, models
from src.database import crud

Base.metadata.create_all(bind=engine)

app = FastAPI()

def modify_data(user_data):
    new_set=[]
    test=user_data.preferences
    for item in test:
        no_items = len(item['subcategories'])
        for i in range(no_items):
            rs=dict({"category":item["category"],"preference":item["subcategories"][i]})
            new_set.append(rs)
    return new_set


@app.post("/create_user", response_model=schema.UserGet)
def create_user(user: schema.UserCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_user(db, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/get_user", response_model=schema.UserGet)
def get_user_detail(
    name: str = Query(default=None, description="Name of the user"),
    email: str = Query(default=None, description="Email of the user"),
    db: Session = Depends(get_db)
):
    detail = schema.UserLookup(name=name, email=email)
    user = crud.get_specific_user(db, detail)

    if isinstance(user, dict) and "error" in user:
        raise HTTPException(status_code=404, detail=user["error"])
    return user


@app.put("/user/{email}", response_model=schema.UserGet)
def update_preferences(
    email: str,                                 
    preferences: schema.UpdatePreferences,       
    db: Session = Depends(get_db)
):
    
    preferences.email = email
    user = crud.update_preferences(db, preferences)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

