import asyncio
import aiohttp
import json
import time
import re
from typing import Callable, Optional, Dict, Any

class RestoreManager:
    def __init__(self, debug_callback=None):
        self.debug_callback = debug_callback
        self.progress_callback = None
        self.roles_map = {}
        self.categories_map = {}
        self.channels_map = {}
        self.stats = {
            "roles_created": 0,
            "categories_created": 0,
            "text_channels_created": 0,
            "voice_channels_created": 0,
            "messages_cloned": 0,
            "errors": 0,
            "start_time": None,
            "elapsed_time": 0
        }

    def get_stats(self) -> dict:
        if self.stats["start_time"]:
            self.stats["elapsed_time"] = time.time() - self.stats["start_time"]
        self.stats["channels_created"] = self.stats["categories_created"] + self.stats["text_channels_created"] + self.stats["voice_channels_created"]
        return self.stats

    def _sanitize_name(self, name: str, c_type: int) -> str:
        """Sanitizes channel names while preserving as much as possible"""
        if not name or not name.strip():
            return "restored-channel"
            
        # Clean up whitespace
        name = name.strip()
        
        if c_type in (0, 5, 15): # Text-like
            # Replace spaces with hyphens and lowercase
            s_name = name.lower().replace(" ", "-")
            # Discord API allows emojis and most fancy text in text channel names
            # The client sanitizes them, but the API is more permissive.
            # We ONLY remove characters that are GUARANTEED to cause a 400.
            s_name = re.sub(r'[@#:\"`]', '', s_name)
            # Remove multiple hyphens
            s_name = re.sub(r'-+', '-', s_name).strip("-")
            return s_name if s_name else "text-channel"
            
        # Categories and Voice allow almost everything including spaces/caps
        return name

    def set_progress_callback(self, callback: Callable[[float], None]):
        self.progress_callback = callback

    def _update_progress(self, progress: float):
        if self.progress_callback:
            self.progress_callback(max(0.0, min(1.0, progress)))

    def _log(self, message, level="INFO"):
        if self.debug_callback:
            self.debug_callback(message, level)

    async def _request(self, session: aiohttp.ClientSession, method: str, url: str, **kwargs) -> tuple[int, Any]:
        """Unified request handler with rate limit handling and retries"""
        max_retries = 3
        max_429_retries = 5
        retry_count = 0
        rate_limit_retries = 0
        
        while retry_count < max_retries and rate_limit_retries < max_429_retries:
            try:
                async with session.request(method, url, **kwargs) as resp:
                    if resp.status == 429:
                        rate_limit_retries += 1
                        try:
                            data = await resp.json()
                            retry_after = data.get("retry_after", 5)
                        except:
                            retry_after = 5
                        
                        self._log(f"Rate limited (429), waiting {retry_after}s... (Attempt {rate_limit_retries}/{max_429_retries})", "WARNING")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    rate_limit_retries = 0
                    
                    try:
                        if resp.status != 204: # No Content
                            data = await resp.json()
                        else:
                            data = None
                    except:
                        data = await resp.text()
                        
                    return resp.status, data
            except Exception as e:
                retry_count += 1
                self._log(f"Request error: {str(e)}. Retrying {retry_count}/{max_retries}...", "WARNING")
                await asyncio.sleep(2 * retry_count)
                
        return 0, None

    async def restore_snapshot(self, snapshot_data, dest_guild_id, token, options):
        """Pushes snapshot data to a destination server"""
        self._log(f"Initializing restoration for {snapshot_data['metadata']['guild_name']}...")
        self._update_progress(0.05)
        
        self.stats = {
            "roles_created": 0,
            "categories_created": 0,
            "text_channels_created": 0,
            "voice_channels_created": 0,
            "messages_cloned": 0,
            "errors": 0,
            "start_time": time.time(),
            "elapsed_time": 0
        }
        
        self.roles_map = {}
        self.categories_map = {}
        self.channels_map = {}
        
        headers = {"Authorization": token}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                # 1. Map @everyone
                source_guild_id = snapshot_data['metadata']['guild_id']
                self.roles_map[source_guild_id] = dest_guild_id

                # 2. Clear destination
                if options.get("clear_roles"):
                    await self._clear_roles(session, dest_guild_id)
                
                if options.get("clear_channels") or options.get("clear_categories"):
                    await self._clear_channels(session, dest_guild_id, options)
                
                self._update_progress(0.20)

                # 3. Create Roles
                if options.get("clone_roles"):
                    self._log("Restoring roles...")
                    roles = snapshot_data['data']['roles']
                    sorted_roles = sorted([r for r in roles if r['name'] != "@everyone"], key=lambda x: x.get('position', 0))
                    
                    for i, role in enumerate(sorted_roles):
                        payload = {
                            "name": role['name'],
                            "permissions": role['permissions'],
                            "color": role['color'],
                            "hoist": role['hoist'],
                            "mentionable": role['mentionable']
                        }
                        status, data = await self._request(session, "POST", f"https://discord.com/api/v10/guilds/{dest_guild_id}/roles", json=payload)
                        if status in (200, 201):
                            self.roles_map[role['id']] = data['id']
                            self.stats["roles_created"] += 1
                            self._log(f"Role restored: {role['name']}")
                        else:
                            self.stats["errors"] += 1
                            self._log(f"Failed to restore role {role['name']}: HTTP {status}", "WARNING")
                        
                        self._update_progress(0.20 + (0.20 * (i + 1) / len(sorted_roles)))
                        await asyncio.sleep(0.5)
                
                self._update_progress(0.40)

                # 4. Create Categories
                if options.get("clone_categories"):
                    self._log("Restoring categories...")
                    categories = [c for c in snapshot_data['data']['channels'] if c['type'] == 4]
                    sorted_cats = sorted(categories, key=lambda x: x.get('position', 0))
                    
                    for i, cat in enumerate(sorted_cats):
                        payload = {
                            "name": self._sanitize_name(cat["name"], 4),
                            "type": 4,
                            "position": cat.get("position", 0),
                            "permission_overwrites": self._map_overwrites(cat.get("permission_overwrites", []))
                        }
                        status, data = await self._request(session, "POST", f"https://discord.com/api/v10/guilds/{dest_guild_id}/channels", json=payload)
                        if status in (200, 201):
                            self.categories_map[cat["id"]] = data["id"]
                            self.stats["categories_created"] += 1
                            self._log(f"Category restored: {cat['name']}")
                        else:
                            self.stats["errors"] += 1
                            error_detail = ""
                            if status == 400 and isinstance(data, dict):
                                error_detail = f" - {json.dumps(data)}"
                            self._log(f"Failed to restore category {cat['name']}: HTTP {status}{error_detail}", "WARNING")
                        
                        self._update_progress(0.40 + (0.20 * (i + 1) / len(sorted_cats)))
                        await asyncio.sleep(1.0)

                self._update_progress(0.60)

                # 5. Create Channels
                self._log("Restoring channels...")
                channels = [c for c in snapshot_data['data']['channels'] if c['type'] != 4]
                sorted_channels = sorted(channels, key=lambda x: x.get('position', 0))
                
                for i, chan in enumerate(sorted_channels):
                    try:
                        c_type = int(chan.get('type', 0))
                    except:
                        c_type = 0
                        
                    # Validate type (choices are 0, 2, 4, 5, 13, 14, 15, 16)
                    if c_type not in (0, 2, 4, 5, 6, 13, 14, 15, 16):
                        c_type = 0 # Default to text
                    
                    if c_type in (0, 5) and not options.get("clone_text_channels"): continue 
                    if c_type == 2 and not options.get("clone_voice_channels"): continue 
                    
                    payload = {
                        "name": self._sanitize_name(chan["name"], c_type),
                        "type": c_type,
                        "position": chan.get("position", 0),
                        "parent_id": self.categories_map.get(chan.get("parent_id")),
                        "permission_overwrites": self._map_overwrites(chan.get("permission_overwrites", []))
                    }
                    
                    if c_type in (0, 5, 15):
                        payload.update({
                            "topic": chan.get("topic"), 
                            "nsfw": chan.get("nsfw", False),
                            "rate_limit_per_user": chan.get("rate_limit_per_user", 0)
                        })
                    elif c_type in (2, 13):
                        payload.update({
                            "bitrate": chan.get("bitrate", 64000),
                            "user_limit": chan.get("user_limit", 0)
                        })
                    
                    status, data = await self._request(session, "POST", f"https://discord.com/api/v10/guilds/{dest_guild_id}/channels", json=payload)
                    if status in (200, 201):
                        self.channels_map[chan["id"]] = data["id"]
                        if c_type in (0, 5, 15): self.stats["text_channels_created"] += 1
                        else: self.stats["voice_channels_created"] += 1
                        self._log(f"Channel restored: {chan['name']}")
                    else:
                        self.stats["errors"] += 1
                        error_detail = ""
                        if status == 400 and isinstance(data, dict):
                            error_detail = f" - {json.dumps(data)}"
                        self._log(f"Failed to restore channel {chan['name']}: HTTP {status}{error_detail}", "WARNING")
                    
                    self._update_progress(0.60 + (0.40 * (i + 1) / len(sorted_channels)))
                    await asyncio.sleep(1.0)

                self._update_progress(1.0)
                self._log("Restoration Complete!", "SUCCESS")
                return True

            except Exception as e:
                self._log(f"Restoration critical failure: {str(e)}", "ERROR")
                import traceback
                self._log(traceback.format_exc(), "DEBUG")
                return False

    def _map_overwrites(self, old_overwrites):
        new_overwrites = []
        for ov in old_overwrites:
            new_id = self.roles_map.get(ov.get("id"))
            if new_id:
                new_overwrites.append({
                    "id": new_id,
                    "type": ov.get("type", 0),
                    "allow": ov.get("allow", "0"),
                    "deny": ov.get("deny", "0")
                })
        return new_overwrites

    async def _clear_roles(self, session, guild_id):
        self._log("Checking destination roles...")
        status, roles = await self._request(session, "GET", f"https://discord.com/api/v10/guilds/{guild_id}/roles")
        if status == 200:
            for r in roles:
                if r['name'] == "@everyone" or r.get("managed"): continue
                await self._request(session, "DELETE", f"https://discord.com/api/v10/guilds/{guild_id}/roles/{r['id']}")
                await asyncio.sleep(0.5)

    async def _clear_channels(self, session, guild_id, options):
        self._log("Checking destination channels...")
        status, chans = await self._request(session, "GET", f"https://discord.com/api/v10/guilds/{guild_id}/channels")
        if status == 200:
            sorted_chans = sorted(chans, key=lambda x: x['type'] == 4)
            for c in sorted_chans:
                is_cat = (c['type'] == 4)
                if (is_cat and options.get("clear_categories")) or (not is_cat and options.get("clear_channels")):
                    await self._request(session, "DELETE", f"https://discord.com/api/v10/channels/{c['id']}")
                    await asyncio.sleep(0.5)
