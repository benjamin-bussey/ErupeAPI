from datetime import datetime, timedelta
from typing import List, Optional
from os import getenv
import time

from fastapi import Depends, FastAPI, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

from jose import JWTError, jwt
from passlib.context import CryptContext
from starlette.status import HTTP_204_NO_CONTENT

from schemas import UserBase, User, UserCreate, UserInDB, Character, Token, TokenData, Guild, CharacterDelete
from security import SecurityConfig
from database import database
import models


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(
    title=getenv("PROJECT_NAME", "ERUPE_FASTAPI_TEST")
)

# ToDo environment variable driving CORS customization for Docker deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ToDo look into HTTPS middleware configuration problem
# app.add_middleware(HTTPSRedirectMiddleware)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_user(username: str):
    query = models.user.select().where(models.user.c.username == username)
    db_user = await database.fetch_one(query)
    return UserInDB(**db_user)


async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SecurityConfig.SECRET_KEY, algorithm=SecurityConfig.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SecurityConfig.SECRET_KEY, algorithms=[SecurityConfig.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


# Consider boosting security by adding disabled to the users table
async def get_current_active_user(current_user: User = Depends(get_current_user)):
    # if current_user.disabled:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=int(SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/", response_model=User)
async def create_user(new_user: UserCreate):

    # Checking if the username has already been taken
    query = models.user.select().where(models.user.c.username == new_user.username)
    db_user = await database.fetch_one(query)
    if db_user:
        raise HTTPException(status_code=400, detail=f"{models.user.username} is already registered")

    # Hashing plaintext password
    hashed_password = get_password_hash(new_user.password)

    query = models.user.insert().values(username=new_user.username, password=hashed_password)
    last_record_id = await database.execute(query)

    # Creating a new empty character to allow the user to pass the second custom erupe login screen
    create_char_query = models.character.insert().values(
        user_id=last_record_id,
        is_female=False,
        is_new_character=True,
        small_gr_level=0,
        gr_override_mode=True,
        name="",
        unk_desc_string="",
        gr_override_level=0,
        gr_override_unk0=0,
        gr_override_unk1=0,
        exp=0,
        weapon=0,
        last_login=int(time.time()),
        restrict_guild_scout=False
    )
    await database.execute(create_char_query)

    user_character_query = models.character.select().where(models.character.c.user_id == last_record_id)
    user_characters = await database.fetch_all(user_character_query)

    return {"username": new_user.username,
            "id": last_record_id,
            "characters": user_characters}


@app.get("/users/", response_model=List[UserBase])
async def read_users(skip: int = 0, limit: int = 100):
    query = models.user.select().offset(skip).limit(limit)
    return await database.fetch_all(query)


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    user_character_query = models.character.select().where(models.character.c.user_id == int(current_user.id))
    user_characters = await database.fetch_all(user_character_query)

    return {"id": current_user.id,
            "username": current_user.username,
            "characters": user_characters}


@app.get("/users/{username}", response_model=User)
async def read_user(username):
    query = models.user.select().where(models.user.c.username == username)
    db_user = await database.fetch_one(query)

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        user_character_query = models.character.select().where(models.character.c.user_id == db_user["id"])
        user_characters = await database.fetch_all(user_character_query)

        return {**db_user, "characters": user_characters}


@app.post("/characters/", response_model=Character)
async def create_character(current_user: User = Depends(get_current_active_user)):
    create_char_query = models.character.insert().values(
        user_id=int(current_user.id),
        is_female=False,
        is_new_character=True,
        small_gr_level=0,
        gr_override_mode=True,
        name="",
        unk_desc_string="",
        gr_override_level=0,
        gr_override_unk0=0,
        gr_override_unk1=0,
        exp=0,
        weapon=0,
        last_login=int(time.time()),
        restrict_guild_scout=False
    )
    last_created_id = await database.execute(create_char_query)

    query = models.character.select().where(models.character.c.id == last_created_id)

    return await database.fetch_one(query)


@app.get("/characters/", response_model=List[Character])
async def read_characters(skip: int = 0, limit: int = 100):
    query = models.character.select().offset(skip).limit(limit)
    return await database.fetch_all(query)


@app.get("/characters/{name}", response_model=List[Character])
async def read_characters_by_name(name):
    query = models.character.select().where(models.character.c.name == name)
    db_character = await database.fetch_all(query)

    if not db_character:
        raise HTTPException(status_code=404, detail="Character not found")
    else:
        return db_character


@app.delete("/characters/", response_class=Response)
async def delete_character(delete_request: CharacterDelete):
    user = await authenticate_user(delete_request.username, delete_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    delete_query = models.character.delete()\
        .where(models.character.c.name == delete_request.name).where(models.character.c.user_id == int(user.id))

    await database.execute(delete_query)
    return Response(status_code=HTTP_204_NO_CONTENT)


@app.get("/guilds/", response_model=List[Guild])
async def read_guilds(skip: int = 0, limit: int = 100):
    query = models.guild.select().offset(skip).limit(limit)
    return await database.fetch_all(query)
