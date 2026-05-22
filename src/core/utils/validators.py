import re

def is_token_valid(token: str) -> bool:
    # Accetta qualsiasi token purché non sia vuoto
    return bool(token)

def is_guild_id_valid(guild_id: str) -> bool:
    return guild_id.isdigit() and len(guild_id) > 16 