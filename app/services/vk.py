import aiohttp
import asyncio
import os
import re

from dotenv import load_dotenv

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
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=self.ssl))
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()


    async def request(self, method: str, params: dict=None) -> dict:
        url = f"https://api.vk.com/method/{method}"
        
        if params is None:
            params = {}
        params.update({
            "access_token": self.token,
            "v": self.api_version
        })

        async with self.session.get(url, params=params) as resp:
            data = await resp.json()

            if "error" in data:
                return {
                    "ok": False,
                    "error_code": data["error"]["error_code"],
                }

            return {"ok": True, "response": data["response"]}


    async def get_group_by_link(self, link: str) -> dict:
        result = await self.request(
            "groups.getById", {
            "group_id": extract_screen_name(link)
        })

        if not result["ok"]:
            return result

        data = result["response"]

        if isinstance(data, dict) and "groups" in data: 
            return {"ok": True, "group": data["groups"][0]}

        return {"ok": True, "group": data[0]}

    
    async def check_group(self, link: str) -> dict: 
        result = await self.get_group_by_link(link)

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
    

    async def get_group_info(self, link: str) -> dict:
        return await self.check_group(link)


    async def get_group_posts(self, link: str, count: int = 1) -> dict:
        result = await self.check_group(link)

        if not result["ok"]:
            return result

        group = result["group"]
        
        return await self.request("wall.get", {
            "owner_id": -group["id"],
            "count": count
        })
        
        
    async def get_last_post(self, link: str) -> dict:
        result = await self.get_walls(link, count=3)

        if not result["ok"]:
            return result

        for post in result["response"]["items"]:
            if not post.get("is_pinned"):
                return {"ok": True, "post": post}

        return {"ok": False, "status": "no_posts"}


def extract_screen_name(url: str) -> str:
    s = url.strip()
    s = s.replace("https://", "").replace("http://", "")
    s = re.sub(r"^(m\.)?vk\.(com|ru)/", "", s)
    s = s.split("?")[0]
    s = s.split("/")[0]
    
    return s


async def test():
    group_link = "https://vk.com/pso_pnv"

    async with VKSession(TOKEN, ssl=False) as vk:
        
        info = await vk.get_group_info(extract_screen_name(group_link))
        posts = await vk.get_group_posts(extract_screen_name(group_link), count=5)
        
        import json
        with open("temp.json", "w", encoding="utf-8") as file:
            json.dump(info, file, indent=4, ensure_ascii=False)
        with open("temp1.json", "w", encoding="utf-8") as file:
            json.dump(posts, file, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(test())