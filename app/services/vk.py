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


    async def request(self, method: str, params: dict={}):
        url = f"https://api.vk.com/method/{method}"

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


    async def get_group_by_link(self, link: str):
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


    async def get_group_info(self, link: str):
        result = await self.get_group_by_link(link)

        if not result["ok"]:
            code = result["error_code"]

            if code == 100:
                return {"ok": False, "status": "not_found"}
            
            if code == 15:
                return {"ok": False, "status": "access_denied"}
            
            return {"ok": False, "status": "unknown_error", "code": code}

        group = result["group"]

        if group.get("is_closed") == 2:
            return {"ok": False, "status": "private", "group": group}

        if group.get("is_closed") == 1:
            return {"ok": False, "status": "closed", "group": group}

        return {"ok": True, "status": "ok", "group": group}


    async def get_wall(self, group_id: int, count: int = 10):
        return await self.request("wall.get", {
            "owner_id": -group_id,
            "count": count
        })


def extract_screen_name(url: str) -> str:
    s = url.strip()
    s = s.replace("https://", "").replace("http://", "")
    s = re.sub(r"^(m\.)?vk\.(com|ru)/", "", s)
    s = s.split("?")[0]
    s = s.split("/")[0]
    
    return s


async def test():
    group_link = "https://vk.com/pso_p1nv"
    group_link = "https://vk.com/vids_dolboyoba"

    async with VKSession(TOKEN, ssl=False) as vk:

        info = await vk.get_group_by_link(extract_screen_name(group_link))
        # print("\nGROUP INFO")
        # print("ID:", info["id"])
        # print("Name:", info["name"])
        # print("URL:", info["url"])
        # print("Last post ID:", info["last_post_id"])

        # wall = await vk.get_wall(info["id"], count=3)

        # print("\nLATEST POSTS")

        # for post in wall["items"]:
        #     print("\n---")
        #     print("Post ID:", post["id"])
        #     print("Text:", post.get("text", "(empty)"))


if __name__ == "__main__":
    asyncio.run(test())