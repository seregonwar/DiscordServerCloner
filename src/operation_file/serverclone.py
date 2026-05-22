import discord
from src.operation_file.logger import Logger
from typing import Optional, Callable
import asyncio
import time
import io
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import json
import re
from datetime import datetime
import base64
import os


def load_or_create_config(file_path="config.json"):
    # Default settings
    defaults = {
        "CLONE_UPDATE_NAME_ICON": False
    }

    # Create file if it doesn't exist
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump(defaults, f, indent=4)
        print(f"[INFO] {file_path} created with default values.")

    # Load JSON
    with open(file_path, "r") as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError:
            print(f"[ERROR] Invalid JSON in {file_path}, using defaults.")
            config = defaults

    # Ensure all default keys exist
    for key, value in defaults.items():
        if key not in config:
            config[key] = value

    return config

class Clone:
    def __init__(self, debug_callback=None):
        self.logger = Logger(debug_callback)
        self.total_roles = 0
        self.total_channels = 0
        self.total_messages = 0
        self.roles_created = 0
        self.channels_created = 0
        self.messages_copied = 0
        self.errors = 0
        self.start_time = None
        self.channel_map = {}  # Map to track old->new channels
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.progress_callback = None
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
        self.total_operations = 0
        self.completed_operations = 0
        self.roles_map = {}
        self.categories_map = {}
        self.channels_map = {}

    def set_progress_callback(self, callback: Callable[[float], None]):
        self.progress_callback = callback

    def _update_progress(self, progress: float):
        if self.progress_callback:
            progress = max(0.0, min(1.0, progress))
            self.progress_callback(progress)

    def _sanitize_name(self, name: str, c_type: int) -> str:
        """Sanitizes channel names while preserving as much as possible"""
        if not name or not name.strip():
            return "cloned-channel"
            
        # Clean up whitespace
        name = name.strip()
        
        if c_type in (0, 5, 15): # Text-like
            # Replace spaces with hyphens and lowercase
            s_name = name.lower().replace(" ", "-")
            # Only remove characters that are strictly forbidden by Discord API
            s_name = re.sub(r'[@#:\"`]', '', s_name)
            # Remove multiple hyphens
            s_name = re.sub(r'-+', '-', s_name).strip("-")
            return s_name if s_name else "text-channel"
            
        # Categories and Voice allow almost anything
        return name

    async def _request(self, session, method, url, **kwargs):
        """Wrapper for aiohttp requests with rate limit and connection retry handling"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                resp = await session.request(method, url, **kwargs)
                if resp.status == 429:
                    try:
                        data = await resp.json()
                        retry_after = data.get("retry_after", 5)
                    except Exception:
                        retry_after = 5
                    self._safe_log(f"Rate limited on {url}, waiting {retry_after}s", "WARNING")
                    await asyncio.sleep(retry_after)
                    continue
                return resp
            except (aiohttp.ClientOSError, aiohttp.ServerDisconnectedError, asyncio.TimeoutError) as e:
                retry_count += 1
                self._safe_log(f"Connection error: {str(e)}. Retry {retry_count}/{max_retries}...", "WARNING")
                await asyncio.sleep(2 * retry_count)
                
        raise Exception("Max retries exceeded due to connection issues.")

    async def start_clone(self, guild_from, guild_to, session, options=None) -> bool:
        try:
            self.start_time = time.time()
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
            
            # Map @everyone role automatically
            self.roles_map[guild_from["id"]] = guild_to["id"]

            if options is None:
                options = {
                    "clone_roles": True,
                    "clone_categories": True,
                    "clone_text_channels": True,
                    "clone_voice_channels": True,
                    "clear_roles": True,
                    "clear_categories": True,
                    "clear_channels": True,
                    "clone_messages": False,
                    "messages_limit": 0,
                    "clone_name_icon": False
                }
         
            source_id = guild_from.get("id")
            dest_id = guild_to.get("id")
            
            self._safe_log(f"Starting cloning process from {guild_from.get('name')} to {guild_to.get('name')}")

            # 1. Fetch data
            roles_url = f"https://discord.com/api/v10/guilds/{source_id}/roles"
            roles_data = []
            async with await self._request(session, "GET", roles_url) as resp:
                if resp.status == 200:
                    roles_data = await resp.json()
                    self.total_roles = len([r for r in roles_data if r.get("name") != "@everyone"])
                    self._safe_log(f"Found {self.total_roles} roles")
                else:
                    self._safe_log(f"Error fetching roles: {resp.status}", "ERROR")

            channels_url = f"https://discord.com/api/v10/guilds/{source_id}/channels"
            all_channels = []
            async with await self._request(session, "GET", channels_url) as resp:
                if resp.status == 200:
                    all_channels = await resp.json()
                else:
                    self._safe_log(f"Error fetching channels: {resp.status}", "ERROR")

            categories_data = [c for c in all_channels if c.get("type") == 4]
            text_channels_data = [c for c in all_channels if c.get("type") in (0, 5, 15)] # Text, News, Forum
            voice_channels_data = [c for c in all_channels if c.get("type") in (2, 13)] # Voice, Stage
            self.total_channels = len(categories_data) + len(text_channels_data) + len(voice_channels_data)

            # 2. Start modifications
            self._update_progress(0.05)
            await self._edit_guild_rest(guild_to, guild_from, session, options)
            
            if options.get("clear_roles", True):
                await self._delete_existing_roles_rest(guild_to, session)
            
            if options.get("clone_roles", True):
                await self._create_roles_rest(guild_to, roles_data, session)
                everyone_source = next((r for r in roles_data if r.get("name") == "@everyone"), None)
                if everyone_source:
                    await self._sync_everyone_permissions(guild_to, everyone_source, session)
            self._update_progress(0.30)

            if options.get("clear_channels", True) or options.get("clear_categories", True):
                await self._delete_existing_channels_rest(
                    guild_to, 
                    session, 
                    clear_categories=options.get("clear_categories", True),
                    clear_channels=options.get("clear_channels", True)
                )

            if any([options.get("clone_categories"), options.get("clone_text_channels"), options.get("clone_voice_channels")]):
                await self._create_categories_and_channels_rest(
                    guild_to,
                    categories_data if options.get("clone_categories") else [],
                    text_channels_data if options.get("clone_text_channels") else [],
                    voice_channels_data if options.get("clone_voice_channels") else [],
                    session
                )
            self._update_progress(0.70)

            if options.get("clone_messages", False):
                await self._copy_messages_rest(text_channels_data, session, options.get("messages_limit", 100))
            
            self._update_progress(1.0)
            elapsed = time.time() - self.start_time
            self._safe_log(f"Cloning completed in {elapsed:.2f} seconds", "SUCCESS")
            return True

        except Exception as e:
            self.logger.error(f"Critical error during cloning: {str(e)}")
            return False

    async def _sync_everyone_permissions(self, guild_to, everyone_source, session):
        self._safe_log("Syncing @everyone permissions...")
        url = f"https://discord.com/api/v10/guilds/{guild_to['id']}/roles/{guild_to['id']}"
        payload = {"permissions": everyone_source.get("permissions")}
        async with await self._request(session, "PATCH", url, json=payload) as resp:
            if resp.status != 200:
                self._safe_log(f"Failed to sync @everyone permissions: {resp.status}", "ERROR")

    async def _edit_guild_rest(self, guild_to, guild_from, session, options):
        if not options.get("clone_name_icon"):
            return
        self._safe_log("Updating guild name/icon...")
        payload = {"name": guild_from.get("name")}
        icon_hash = guild_from.get("icon")
        if icon_hash:
            icon_url = f"https://cdn.discordapp.com/icons/{guild_from['id']}/{icon_hash}.png"
            async with await self._request(session, "GET", icon_url) as resp:
                if resp.status == 200:
                    icon_bytes = await resp.read()
                    payload["icon"] = f"data:image/png;base64,{base64.b64encode(icon_bytes).decode()}"

        await self._request(session, "PATCH", f"https://discord.com/api/v10/guilds/{guild_to['id']}", json=payload)

    async def _delete_existing_roles_rest(self, guild_to, session):
        self._safe_log("Deleting existing roles...")
        roles_url = f"https://discord.com/api/v10/guilds/{guild_to['id']}/roles"
        async with await self._request(session, "GET", roles_url) as resp:
            if resp.status == 200:
                roles = await resp.json()
                for role in roles:
                    if role["name"] == "@everyone" or role.get("managed"):
                        continue
                    await self._request(session, "DELETE", f"{roles_url}/{role['id']}")
                    await asyncio.sleep(0.5)

    async def _create_roles_rest(self, guild_to, roles_data, session):
        self._safe_log("Creating new roles...")
        sorted_roles = sorted([r for r in roles_data if r["name"] != "@everyone"], key=lambda r: r.get("position", 0))
        for role in sorted_roles:
            payload = {
                "name": role.get('name'),
                "permissions": role.get('permissions'),
                "color": role.get('color'),
                "hoist": role.get('hoist'),
                "mentionable": role.get('mentionable')
            }
            async with await self._request(session, "POST", f"https://discord.com/api/v10/guilds/{guild_to['id']}/roles", json=payload) as resp:
                if resp.status in (200, 201):
                    created = await resp.json()
                    self.roles_map[role['id']] = created['id']
                    self.roles_created += 1
                    self.stats["roles_created"] += 1
                    self._safe_log(f"Role created: {role['name']}")
            await asyncio.sleep(0.5)

    async def _delete_existing_channels_rest(self, guild_to, session, clear_categories=True, clear_channels=True):
        self._safe_log(f"Clearing existing data (Categories: {clear_categories}, Channels: {clear_channels})...")
        async with await self._request(session, "GET", f"https://discord.com/api/v10/guilds/{guild_to['id']}/channels") as resp:
            if resp.status == 200:
                all_items = await resp.json()
                to_delete = []
                for item in all_items:
                    is_cat = (item.get("type") == 4)
                    if (is_cat and clear_categories) or (not is_cat and clear_channels):
                        to_delete.append(item)

                to_delete.sort(key=lambda c: c.get("type") == 4)
                for item in to_delete:
                    await self._request(session, "DELETE", f"https://discord.com/api/v10/channels/{item['id']}")
                    await asyncio.sleep(0.5)

    def _map_overwrites(self, old_overwrites):
        new_overwrites = []
        if not old_overwrites:
            return new_overwrites
        for ov in old_overwrites:
            old_id = ov.get("id")
            new_id = self.roles_map.get(old_id)
            if new_id:
                new_overwrites.append({
                    "id": new_id,
                    "type": ov.get("type", 0),
                    "allow": ov.get("allow", "0"),
                    "deny": ov.get("deny", "0")
                })
        return new_overwrites

    async def _create_categories_and_channels_rest(self, guild_to, categories, text_channels, voice_channels, session):
        # 1. Categories
        self._safe_log("Creating categories...")
        for cat in sorted(categories, key=lambda c: c.get("position", 0)):
            payload = {
                "name": self._sanitize_name(cat["name"], 4),
                "type": 4,
                "position": cat.get("position", 0),
                "permission_overwrites": self._map_overwrites(cat.get("permission_overwrites"))
            }
            async with await self._request(session, "POST", f"https://discord.com/api/v10/guilds/{guild_to['id']}/channels", json=payload) as resp:
                if resp.status in (200, 201):
                    created = await resp.json()
                    self.categories_map[cat["id"]] = created["id"]
                    self.channels_map[cat["id"]] = created["id"]
                    self.stats["categories_created"] += 1
                    self._safe_log(f"Category created: {cat['name']}")
            await asyncio.sleep(1.0)

        # 2. Text, Voice, News, Stage, Forum Channels
        self._safe_log("Creating channels...")
        all_chans = text_channels + voice_channels

        for chan in sorted(all_chans, key=lambda c: c.get("position", 0)):
            try:
                c_type = int(chan.get('type', 0))
            except:
                c_type = 0
            
            # Validate type
            if c_type not in (0, 2, 4, 5, 6, 13, 14, 15, 16):
                c_type = 0

            payload = {
                "name": self._sanitize_name(chan["name"], c_type),
                "type": c_type,
                "position": chan.get("position", 0),
                "parent_id": self.categories_map.get(chan.get("parent_id")),
                "permission_overwrites": self._map_overwrites(chan.get("permission_overwrites"))
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

            async with await self._request(session, "POST", f"https://discord.com/api/v10/guilds/{guild_to['id']}/channels", json=payload) as resp:
                if resp.status in (200, 201):
                    created = await resp.json()
                    self.channels_map[chan["id"]] = created["id"]
                    if c_type in (0, 5, 15): self.stats["text_channels_created"] += 1
                    else: self.stats["voice_channels_created"] += 1
                    self._safe_log(f"Channel created: {chan['name']}")
                else:
                    self._safe_log(f"Failed to create channel {chan['name']}: HTTP {resp.status}", "WARNING")
            await asyncio.sleep(1.0)

    async def _copy_messages_rest(self, text_channels, session, limit):
        self._safe_log(f"Copying messages (limit: {limit})...")
        for old_chan in text_channels:
            new_id = self.channels_map.get(old_chan["id"])
            if not new_id:
                continue
            url = f"https://discord.com/api/v10/channels/{old_chan['id']}/messages?limit={limit}"
            async with await self._request(session, "GET", url) as resp:
                if resp.status == 200:
                    messages = await resp.json()
                    for msg in reversed(messages):
                        await self._post_message_rest(new_id, msg, session)
                        await asyncio.sleep(0.8)

    async def _post_message_rest(self, channel_id, msg, session):
        content = msg.get("content", "")
        author = msg.get("author", {}).get("username", "Unknown")
        timestamp = msg.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                timestamp = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass
        
        full_content = f"**{author}** [{timestamp}]:\n{content}"
        if len(full_content) > 2000:
            full_content = full_content[:1997] + "..."
            
        payload = {"content": full_content}
        
        # Handle Embeds
        if msg.get("embeds"):
            # Filtering out 'type' as it can cause issues and is usually 'rich' for user-created embeds
            payload["embeds"] = [
                {k: v for k, v in e.items() if k != "type"} 
                for e in msg["embeds"] if e.get("type") == "rich" or not e.get("type")
            ][:10] # Discord limit is 10 embeds per message

        # Handle Attachments (as links)
        if msg.get("attachments"):
            links = "\n".join([a["url"] for a in msg["attachments"]])
            if len(payload["content"]) + len(links) + 1 <= 2000:
                payload["content"] += "\n" + links
            else:
                # If too long, send content first, then links
                await self._request(session, "POST", f"https://discord.com/api/v10/channels/{channel_id}/messages", json=payload)
                payload = {"content": f"**{author}** Attachments:\n{links}"}
                if len(payload["content"]) > 2000:
                    payload["content"] = payload["content"][:2000]

        async with await self._request(session, "POST", f"https://discord.com/api/v10/channels/{channel_id}/messages", json=payload) as resp:
            if resp.status in (200, 201):
                self.messages_copied += 1
                self.stats["messages_cloned"] += 1
            else:
                self._safe_log(f"Failed to post message in {channel_id}: HTTP {resp.status}", "WARNING")

    def _safe_log(self, message: str, level: str = "INFO"):
        try:
            if level == "ERROR":
                self.logger.error(message)
            elif level == "WARNING":
                self.logger.add(f"[WARN] {message}")
            elif level == "SUCCESS":
                self.logger.add(f"[SUCCESS] {message}")
            else:
                self.logger.add(message)
        except Exception:
            pass

    def get_stats(self) -> dict:
        if self.stats["start_time"]:
            self.stats["elapsed_time"] = time.time() - self.stats["start_time"]
        self.stats["total_roles"] = self.total_roles
        self.stats["total_channels"] = self.total_channels
        self.stats["roles_created"] = self.roles_created
        self.stats["channels_created"] = self.stats["categories_created"] + self.stats["text_channels_created"] + self.stats["voice_channels_created"]
        self.stats["messages_copied"] = self.messages_copied
        return self.stats
