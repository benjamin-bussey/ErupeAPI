from typing import List, Optional

from pydantic import BaseModel


class Character(BaseModel):
    id: int
    user_id: int
    is_female: bool
    is_new_character: bool
    small_gr_level: int
    name: str
    gr_override_level: int
    exp: int
    weapon: int
    last_login: int


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: str
    characters: List[Character] = []


class UserInDB(User):
    password: str


class Guild(BaseModel):
    id: int
    name: str
    created_at: str
    leader_id: str
    main_motto: str
    rp: int
    comment: str
    festival_colour: str
    guild_hall: int


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
