import asyncio
import aiohttp
from typing import Optional

# Current application version
CURRENT_VERSION = "3.0.0"

GITHUB_RELEASES_LATEST = (
    "https://api.github.com/repos/Aadiwrth/Discord-Server-Manger/releases/latest"
)


def _parse_version(v: str) -> tuple:
    v = v.strip()
    if v.lower().startswith('v'):
        v = v[1:]
    parts = v.split('.')
    nums = []
    for p in parts:
        try:
            nums.append(int(p))
        except ValueError:
            # Strip any suffix like -beta, -rc
            num = ''.join(ch for ch in p if ch.isdigit())
            nums.append(int(num) if num else 0)
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums[:3])


def is_newer(latest: str, current: str) -> bool:
    return _parse_version(latest) > _parse_version(current)


async def fetch_latest_version(session: Optional[aiohttp.ClientSession] = None) -> Optional[str]:
    created = False
    sess = session
    if sess is None:
        sess = aiohttp.ClientSession()
        created = True
    try:
        async with sess.get(GITHUB_RELEASES_LATEST, headers={"Accept": "application/vnd.github+json"}) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            tag = data.get("tag_name")
            if isinstance(tag, str) and tag.strip():
                return tag.strip()
            return None
    except Exception:
        return None
    finally:
        if created:
            await sess.close()


def get_latest_version_sync(timeout: float = 6.0) -> Optional[str]:
    async def runner():
        return await fetch_latest_version()
    try:
        return asyncio.run(asyncio.wait_for(runner(), timeout=timeout))
    except Exception:
        return None
