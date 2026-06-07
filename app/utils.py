import re
import time

def extract_screen_name(url: str) -> str:
    s = url.strip()
    s = s.replace("https://", "").replace("http://", "")
    s = re.sub(r"^(m\.)?vk\.(com|ru)/", "", s)
    s = s.split("?")[0]
    s = s.split("/")[0]
    
    return s


def split_post(text: str, limit: int=4000) -> list[str]:
    chunks = []

    while len(text) > limit:
        pos = text.rfind("\n", 0, limit)

        if pos == -1:
            pos = limit

        chunks.append(text[:pos])
        text = text[pos:].lstrip()

    if text:
        chunks.append(text)

    return chunks


