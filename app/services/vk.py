import aiohttp
import asyncio
import os
import re

from dotenv import load_dotenv

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
                    return {
                        "ok": False,
                        "error_code": data["error"]["error_code"],
                    }

                return {"ok": True, "response": data["response"]}
            
        except aiohttp.ClientError:
            return {"ok": False, "status": "network_error"}
        
        except asyncio.TimeoutError:
            return {"ok": False, "status": "timeout"}


    async def get_group_by_ref(self, ref: str):
        result = await self.request(
            "groups.getById", {
            "group_id": extract_group_ref(ref)
        })

        if not result["ok"]:
            return result

        data = result["response"]

        if isinstance(data, dict) and "groups" in data: 
            return {"ok": True, "group": data["groups"][0]}

        return {"ok": True, "group": data[0]}


    async def check_group(self, ref: str): 
        result = await self.get_group_by_ref(ref)

        if not result["ok"]:
            code = result["error_code"]

            if code == 100:
                return {"ok": False, "status": "not_found"}

            if code == 15:
                return {"ok": False, "status": "access_denied"}

            return {"ok": False, "status": "unknown_error", "code": code}

        group = result["group"]

        if group["is_closed"] == 2:
            return {"ok": False, "status": "private", "group": group}

        if group["is_closed"] == 1: 
            return {"ok": False, "status": "closed", "group": group}

        return {"ok": True, "group": group}


    async def get_group_info(self, ref: str):
        return await self.check_group(ref)


    async def get_group_posts(self, ref: str, count: int=1, with_pinned: bool=False):
        result = await self.check_group(ref)

        if not result["ok"]:
            return result

        group = result["group"]

        result = await self.request("wall.get", {
            "owner_id": -group["id"],
            "count": count+5
        })
        
        posts = result["response"]["items"]
        if not with_pinned:
            posts = [post for post in posts if not post.get("is_pinned")]
        
        posts = posts[:count]
        
        posts = await self.add_posts_authors(posts)

        return {"ok": True, "posts": posts}


    async def get_user_info(self, user_id: int | list):
        if isinstance(user_id, int):
            user_id = [user_id]
            
        result = await self.request(
            "users.get", {
            "user_ids": ', '.join(map(str, user_id))
        })
        
        if not result["response"]:
            return {"ok": False}

        return {"ok": True, "users": result["response"]}


    async def get_new_posts(self, group_ref: str, last_post_id: int):
        result = await self.get_group_posts(group_ref, 20)
        
        if not result["ok"]:
            return result
        
        posts = result["posts"]
        new_posts = []
        
        for post in posts:
            if post.get("is_pinned"):
                continue
            
            if post["id"] > last_post_id:
                new_posts.append(post)
            
        new_posts.sort(key=lambda x: x["id"])
        
        return {"ok": True, "posts": new_posts}


    async def add_posts_authors(self, posts: dict):
        author_ids = [post.get("signer_id") for post in posts if post.get("signer_id")]
        
        if not len(author_ids):
            return posts
        
        authors = (await self.get_user_info(author_ids)).get("users")
        authors_by_id = {author["id"]: author for author in authors}
        
        for post in posts:
            signer_id = post.get("signer_id")
            if signer_id in authors_by_id:
                post["author_info"] = authors_by_id[signer_id]

        return posts


vk = VKSession()


# ==================
#   ТЕСТОВОЕ ГОВНО
# ==================

async def test():
    group_ref = "https://vk.com/pso_pnv"
    group_ref = "https://vk.com/club239462773"

    async with VKSession(TOKEN, ssl=False) as vk1:
        import json
        i = 0
        
        i += 1
        info = await vk1.get_group_info(group_ref)
        with open(f"temp{i}.json", "w", encoding="utf-8") as file:
            json.dump(info, file, indent=4, ensure_ascii=False)
        
        i += 1
        info = await vk1.get_group_posts(group_ref, 3, True)
        with open(f"temp{i}.json", "w", encoding="utf-8") as file:
            json.dump(info, file, indent=4, ensure_ascii=False)
            
        # i += 1
        # info = await vk1.get_new_posts(group_ref, 515500)        
        # with open(f"temp{i}.json", "w", encoding="utf-8") as file:
        #     json.dump(info, file, indent=4, ensure_ascii=False)
        
        # i += 1
        # info = await vk1.get_user_info([143522729, 143522728])        
        # with open(f"temp{i}.json", "w", encoding="utf-8") as file:
        #     json.dump(info, file, indent=4, ensure_ascii=False)
        
            

if __name__ == "__main__":
    asyncio.run(test())