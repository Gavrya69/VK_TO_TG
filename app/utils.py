import re


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


def split_post(text: str, limit: int=4096, first_limit: int|None=None) -> list[str]:
    def find_split_pos(t: str, max_len: int) -> int:
        pos = t.rfind("\n", 0, max_len)
        if pos != -1:
            return pos
        
        for sep in [". ", "! ", "? "]:
            pos = t.rfind(sep, 0, max_len)
            if pos != -1:
                return pos + 1
        
        return max_len
    
    if first_limit is None:
        first_limit = limit
    
    chunks = []
    
    if len(text) <= first_limit:
        return [text]
    
    pos = find_split_pos(text, first_limit)
    chunks.append(text[:pos].strip())
    text = text[pos:].lstrip()
    
    while len(text) > limit:
        pos = find_split_pos(text, limit)
        chunks.append(text[:pos].strip())
        text = text[pos:].lstrip()
    
    if text:
        chunks.append(text)
    
    return chunks


