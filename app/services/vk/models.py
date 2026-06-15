from dataclasses import dataclass
from datetime import datetime


@dataclass
class VKGroup:
    id: int
    name: str
    screen_name: str
    is_closed: int = 0
    
    url: str = ""


@dataclass
class VKUser:
    id: int
    first_name: str
    last_name: str
    is_closed: bool
    
    url: str =""


@dataclass
class VKPost:
    id: int
    owner_id: int
    text: str
    date: int
    is_pinned: bool = False
    
    signer_id: int | None = None
    from_id: int | None = None
    
    author: VKUser | VKGroup | None = None
    
    url: str = ""