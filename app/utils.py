import re
import time


def extract_group_ref(value: str | int) -> str | int:
    if isinstance(value, int):
        return value

    value = value.strip()

    if value.isdigit():
        return int(value)

    value = value.replace("https://", "").replace("http://", "")
    value = re.sub(r"^(m\.)?vk\.(com|ru)/", "", value)
    value = value.split("?")[0]
    value = value.split("/")[0]

    return value


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


