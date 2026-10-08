import html
import re


VK_REF_RE = re.compile(r"\[(?P<target>[^\]|]+)\|(?P<ref_title>[^\]]+)\]")
VK_MENTION_RE = re.compile(r"@[A-Za-z0-9_.]+(?:\s+\((?P<mention_title>[^)]+)\))?")


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


def vk_ref_to_url(target: str) -> str | None:
    target = target.strip()
    
    if target.startswith(("http://", "https://")):
        return target
    
    if re.fullmatch(r"(?:id|club|public)-?\d+", target):
        return f"https://vk.ru/{target}"
    
    return None


def format_vk_text(text: str) -> str:
    if not text:
        return ""
    
    pattern = re.compile(
        rf"{VK_REF_RE.pattern}|{VK_MENTION_RE.pattern}"
    )
    
    parts = []
    last = 0
    
    for match in pattern.finditer(text):
        parts.append(html.escape(text[last:match.start()]))
        
        target = match.group("target")
        ref_title = match.group("ref_title")
        mention_title = match.group("mention_title")
        
        if target is not None:
            title = html.escape(ref_title)
            url = vk_ref_to_url(target)
            
            if url:
                parts.append(f'<a href="{html.escape(url, quote=True)}">{title}</a>')
            else:
                parts.append(title)
        
        elif mention_title is not None:
            parts.append(html.escape(mention_title))
        
        else:
            parts.append(html.escape(match.group(0)))
        
        last = match.end()
    
    parts.append(html.escape(text[last:]))
    
    return "".join(parts)