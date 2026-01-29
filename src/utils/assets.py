
import os
import sys

def get_base_path():
    """
    Get the base path of the project.
    If running within Blacksmith, use BLACKSMITH_WORKSPACE_ROOT.
    Otherwise, use the current working directory.
    """
    if "BLACKSMITH_WORKSPACE_ROOT" in os.environ:
        return os.environ["BLACKSMITH_WORKSPACE_ROOT"]
    return os.getcwd()

def get_asset_path(relative_path):
    """
    Get the absolute path for a given asset relative path.
    Example: get_asset_path("src/interface/assets/icon.png")
    """
    # Normalize path separators for the current OS
    normalized_path = os.path.normpath(relative_path)
    return os.path.join(get_base_path(), normalized_path)
