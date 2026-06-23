from dataclasses import dataclass
from datetime import datetime


@dataclass
class VKGroup:
    id: int # FIXME: Заменить "id" на "group_id"
    name: str
    screen_name: str
    is_closed: int = 0
    
    url: str = ""


@dataclass
class VKUser:
    id: int # FIXME: Заменить "id" на "user_id"
    first_name: str
    last_name: str
    is_closed: bool
    
    url: str =""


@dataclass
class VKPost:
    id: int # FIXME: Заменить "id" на "post_id"
    owner_id: int
    text: str
    date: int
    is_pinned: bool = False
    
    signer_id: int | None = None
    from_id: int | None = None
    
    author: VKUser | VKGroup | None = None
    
    photos: list[dict] | None = None
    
    url: str = ""