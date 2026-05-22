import json
import os
import asyncio
import aiohttp
from datetime import datetime

class SnapshotManager:
    def __init__(self):
        self.snapshot_dir = "snapshots"
        os.makedirs(self.snapshot_dir, exist_ok=True)

    async def capture_server(self, guild_id, token, description=""):
        """Fetches all server structure and returns a JSON-ready dict"""
        print(f"[SNAPSHOT] Capturing guild ID: {guild_id}")
        headers = {"Authorization": token}
        async with aiohttp.ClientSession(headers=headers) as session:
            # 1. Fetch Roles
            async with session.get(f"https://discord.com/api/v10/guilds/{guild_id}/roles") as resp:
                roles = await resp.json() if resp.status == 200 else []
                print(f"[SNAPSHOT] Captured {len(roles)} roles")

            # 2. Fetch Channels
            async with session.get(f"https://discord.com/api/v10/guilds/{guild_id}/channels") as resp:
                channels = await resp.json() if resp.status == 200 else []
                cats = [c for c in channels if c.get('type') == 4]
                chans = [c for c in channels if c.get('type') != 4]
                print(f"[SNAPSHOT] Captured {len(cats)} categories and {len(chans)} channels")

            # 3. Fetch Guild Info
            async with session.get(f"https://discord.com/api/v10/guilds/{guild_id}") as resp:
                guild_info = await resp.json() if resp.status == 200 else {}

        snapshot = {
            "metadata": {
                "captured_at": datetime.now().isoformat(),
                "guild_name": guild_info.get("name", "Unknown"),
                "guild_id": guild_id,
                "description": description,
                "version": "1.0"
            },
            "data": {
                "name": guild_info.get("name"),
                "icon": guild_info.get("icon"),
                "roles": roles,
                "channels": channels
            }
        }
        return snapshot

    def save_snapshot(self, snapshot_data):
        """Saves snapshot to a JSON file"""
        gname = snapshot_data["metadata"]["guild_name"].replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{gname}_{timestamp}.json"
        filepath = os.path.join(self.snapshot_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, indent=4)
        return filename

    def list_snapshots(self):
        """Returns a list of all saved snapshots"""
        snapshots = []
        if not os.path.exists(self.snapshot_dir):
            return []
            
        for filename in os.listdir(self.snapshot_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.snapshot_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        snapshots.append({
                            "filename": filename,
                            "guild_name": data["metadata"]["guild_name"],
                            "description": data["metadata"].get("description", ""),
                            "captured_at": data["metadata"]["captured_at"],
                            "roles_count": len(data["data"]["roles"]),
                            "channels_count": len(data["data"]["channels"])
                        })
                except:
                    continue
        return sorted(snapshots, key=lambda x: x["captured_at"], reverse=True)

    def update_description(self, filename, new_description):
        """Updates the description of an existing snapshot file"""
        filepath = os.path.join(self.snapshot_dir, filename)
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            data["metadata"]["description"] = new_description
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error updating description: {e}")
            return False
