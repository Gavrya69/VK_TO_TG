import aiohttp
import asyncio
import os

from dotenv import load_dotenv

from services.vk.mapper import map_group, map_posts
from utils import extract_group_ref


load_dotenv()

TOKEN = os.getenv("VK_TOKEN")
API_VERSION = "5.199"


class VKSession:
    def __init__(self, token: str=TOKEN, api_version: str=API_VERSION, ssl=False):
        self.token = token
        self.api_version = api_version
        self.ssl = ssl
        self.session = None
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        await self.close()    
    
    async def start(self):
        if self.session and not self.session.closed:
            return self

        timeout = aiohttp.ClientTimeout(total=15)
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=self.ssl),
            timeout=timeout
        )
        return self
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    
    async def request(self, method: str, params: dict=None):
        url = f"https://api.vk.com/method/{method}"
        
        if params is None:
            params = {}
        
        params.update({
            "access_token": self.token,
            "v": self.api_version
        })
        
        try:
            async with self.session.get(url, params=params) as resp:
                data = await resp.json()
                
                if "error" in data:
                    error_code = data["error"].get("error_code")
                    
                    if error_code == 5:
                        status = "access_denied"
                    elif error_code == 6:
                        status = "too_many_requests"
                    elif error_code == 100:
                        status = "not_found"
                    else:
                        status = "unknown_error"
                    
                    return {"ok": False, "status": status, "error_code": error_code,}
                
                return {"ok": True, "response": data["response"]}
            
        except aiohttp.ClientError:
            return {"ok": False, "status": "network_error"}
        
        except asyncio.TimeoutError:
            return {"ok": False, "status": "timeout"}
    
    
    async def get_group_by_ref(self, ref: str):
        result = await self.request("groups.getById", {
            "group_id": extract_group_ref(ref)
        })
        
        if not result["ok"]:
            return result
        
        data = result["response"]
        group = data[0] if isinstance(data, list) else data["groups"][0]
        
        return {"ok": True, "group": map_group(group)}
    
    
    async def check_group(self, ref: str):
        result = await self.get_group_by_ref(ref)
        
        if not result["ok"]:
            return result
        
        group = result["group"]
        
        if group.is_closed == 1:
            return {"ok": False, "status": "closed", "group": group}
        
        if group.is_closed == 2:
            return {"ok": False, "status": "private", "group": group}
        
        return {"ok": True, "group": group}
    
    
    async def get_group_info(self, ref: str):
        return await self.check_group(ref)
    
    
    async def get_group_posts(
        self, 
        ref: str, 
        count: int=1, 
        with_pinned: bool=False,
        with_ads: bool=False,
    ):
        result = await self.check_group(ref)
        
        if not result["ok"]:
            return result
        
        group = result["group"]
        
        response = await self.request("wall.get", {
            "owner_id": -group.id,
            "count": min(count + 10, 100),
            "extended": 1
        })
        
        if not response["ok"]:
            return response
        
        data = response["response"]
        
        items = data.get("items", [])
        profiles = data.get("profiles", [])
        groups = data.get("groups", [])
        
        if not with_pinned:
            items = [p for p in items if not p.get("is_pinned")]
            
        if not with_ads:
            valid_items = []
            for p in items:
                if p.get("marked_as_ads") == 1:
                    continue
                if "copy_history" in p and p["copy_history"]:
                    if p["copy_history"][0].get("marked_as_ads") == 1:
                        continue
                valid_items.append(p)
            
            items = valid_items
        
        items = items[:count]
        
        posts = map_posts({
            "items": items,
            "profiles": profiles,
            "groups": groups,
        })
        
        return {"ok": True, "posts": posts}
    
    
    async def get_new_posts(self, ref: str, last_post_id: int):
        result = await self.get_group_posts(ref=ref, count=20, with_pinned=True)
        
        if not result["ok"]:
            return result
        
        posts = result["posts"]
        new_posts = [post for post in posts if post.id > last_post_id]
        
        new_posts.sort(key=lambda x: x.id)
        
        return {"ok": True, "posts": new_posts}


vk = VKSession()