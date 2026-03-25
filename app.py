from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from src.database.database import get_engine, get_db, Base
from src.database import schema, models
from src.database import crud
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables initialized")
    except Exception as e:
        print(f"⚠ Warning: Could not initialize database tables at startup: {e}")
        print("  Tables will be created on first database access")
    yield
    pass

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def modify_data(user_data):
    new_set=[]
    test=user_data.preferences
    for item in test:
        no_items = len(item['subcategories'])
        for i in range(no_items):
            rs=dict({"category":item["category"],"preference":item["subcategories"][i]})
            new_set.append(rs)
    return new_set


@app.get('/')
def start():
    return HTTPException(status_code=200,detail={"message": "Newsflow API is running successfully"})

@app.get('/health')
def health_check():
    return HTTPException(status_code=200,detail={"message":"Service is running well"})

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

