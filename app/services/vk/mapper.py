from datetime import datetime, timezone

from services.vk.models import VKGroup, VKUser, VKPost


def map_group(raw: dict) -> VKGroup:
    alt_screen_name = f"club{raw['id']}"
    return VKGroup(
        id=raw["id"],
        name=raw.get("name", ""),
        screen_name=raw.get("screen_name", ""),
        url=f"https://vk.com/{raw.get('screen_name') or alt_screen_name}",
        is_closed=raw.get("is_closed", 0)
    )


def map_user(raw: dict) -> VKUser:
    return VKUser(
        id=raw["id"],
        first_name=raw.get("first_name", ""),
        last_name=raw.get("last_name", ""),
        url=f"https://vk.com/id{raw['id']}",
        is_closed=raw.get("is_closed")
    )


def resolve_author(
    author_id: int | None,
    profiles: dict,
    groups: dict,
):
    if not author_id:
        return None
    
    if author_id < 0:
        group_raw = groups.get(abs(author_id))
        if group_raw:
            return map_group(group_raw)
        return None
    
    user_raw = profiles.get(author_id)
    if user_raw:
        return map_user(user_raw)
    
    return None


def map_posts(raw: dict) -> list[VKPost]:
    items = raw.get("items", [])
    
    profiles = {
        profile["id"]: profile
        for profile in raw.get("profiles", [])
    }
    
    groups = {
        group["id"]: group
        for group in raw.get("groups", [])
    }
    
    posts: list[VKPost] = []
    
    for item in items:
        signer_id = item.get("signer_id")
        from_id = item.get("from_id")
        
        author_id = signer_id or from_id
        
        author = resolve_author(
            author_id=author_id,
            profiles=profiles,
            groups=groups,
        )
        
        photos = []
        for attachment in item.get("attachments", []):
            if attachment.get("type") != "photo":
                continue
            
            photo = attachment["photo"]
            
            if photo.get("orig_photo"):
                photos.append(photo["orig_photo"]["url"])
            else:
                largest = max(photo["sizes"], key=lambda x: x["width"] * x["height"])
                photos.append(largest["url"])
            
        posts.append(
            VKPost(
                id=item["id"],
                owner_id=item["owner_id"],
                text=item.get("text", ""),
                date=datetime.fromtimestamp(item["date"], tz=timezone.utc),
                is_pinned=item.get("is_pinned", False),
                
                signer_id=signer_id,
                from_id=from_id,
                
                author=author,
                
                photos=photos,
                
                url=f"https://vk.com/wall{item['owner_id']}_{item['id']}",
            )
        )
    
    return posts