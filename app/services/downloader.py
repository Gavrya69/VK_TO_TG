import aiohttp
from aiogram.types import BufferedInputFile


class MediaDownloader:
    def __init__(self):
        self.session: aiohttp.ClientSession | None = None
    
    async def start(self):
        if self.session:
            return
        
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False),
            timeout=aiohttp.ClientTimeout(total=15),
        )
    
    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    async def download_image(self, url: str) -> BufferedInputFile:
        if not self.session:
            await self.start()
        
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            
            content_type = resp.headers.get("Content-Type", "")
            if "image" not in content_type:
                raise ValueError(f"Not image: {content_type}")
            
            data = await resp.read()
        
        return BufferedInputFile(data, filename="image.jpg")


downloader = MediaDownloader()