import os
import shutil
import subprocess
import sys
from src.core.utils.version import CURRENT_VERSION

def create_version_info():
    """Generates a version info file for PyInstaller."""
    version_tuple = tuple(map(int, CURRENT_VERSION.split('.'))) + (0,)
    version_str = CURRENT_VERSION
    
    content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_tuple},
    prodvers={version_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Aadiwrth'),
        StringStruct(u'FileDescription', u'Discord Server Manager - Clone and Manage Servers'),
        StringStruct(u'FileVersion', u'{version_str}'),
        StringStruct(u'InternalName', u'Discord Server Manager'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2026 Aadiwrth & Seregon '),
        StringStruct(u'OriginalFilename', u'Discord Server Manager.exe'),
        StringStruct(u'ProductName', u'Discord Server Manager'),
        StringStruct(u'ProductVersion', u'{version_str}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    with open("file_version_info.txt", "w", encoding="utf-8") as f:
        f.write(content)
    return "file_version_info.txt"

def build():
    """
    Builds the Discord Server Manager into a standalone EXE.
    """
    print("====================================================")
    print("   Discord Server Manager - Build System (V3)     ")
    print("====================================================")
    
    # 1. Configuration
    app_name = "Discord Server Manager"
    main_script = "main.py"
    dist_zip_name = "Discord_Server_Manager"
    
    # 2. Sync Dependencies
    print("\n[1/5] Syncing dependencies with requirements.txt...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        # Ensure PyInstaller is installed in the current environment
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("  - Dependencies synced successfully.")
    except subprocess.CalledProcessError as e:
        print(f"  - Warning: Failed to sync dependencies: {e}")
    
    # Generate version info file
    version_file = create_version_info()
    
    # Data files to bundle: (source_path, dest_relative_to_exe_root)
    # Using format expected by PyInstaller --add-data
    # Note: On Windows, use ';' separator, on others use ':'
    sep = ';' if sys.platform == 'win32' else ':'
    data_to_include = [
        (os.path.join("src", "core", "language"), os.path.join("src", "core", "language")),
        ("community_templates", "community_templates"),
    ]
    
    # Optional assets if they exist
    optional_assets = [
        (os.path.join("src", "interface", "assets"), os.path.join("src", "interface", "assets")),
    ]
    
    for src, dst in optional_assets:
        if os.path.exists(src):
            data_to_include.append((src, dst))
    
    # 3. Cleanup
    print("\n[2/5] Cleaning up previous build artifacts...")
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"  - Removed {folder}/")
            except Exception as e:
                print(f"  - Warning: Could not remove {folder}: {e}")
                
    if os.path.exists(f"{dist_zip_name}.zip"):
        os.remove(f"{dist_zip_name}.zip")
        print(f"  - Removed existing {dist_zip_name}.zip")

    # 4. PyInstaller Command Construction
    print("\n[3/5] Constructing PyInstaller command...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", app_name,
        "--version-file", version_file,
        # Ensure flet is bundled correctly
        "--hidden-import", "flet",
        "--collect-all", "flet",
    ]
    
    for src, dst in data_to_include:
        cmd.extend(["--add-data", f"{src}{sep}{dst}"])
        
    cmd.append(main_script)
    
    # 5. Execution
    print("\n[4/5] Running PyInstaller (this may take a few minutes)...")
    try:
        subprocess.run(cmd, check=True)
        print("\nSUCCESS: Executable created in 'dist/' folder.")
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Build failed with exit code {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print("\nERROR: PyInstaller not found. Please run 'pip install pyinstaller' first.")
        sys.exit(1)

    # 6. Packaging
    print("\n[5/5] Creating distribution ZIP package...")
    dist_dir = 'dist'
    try:
        # Include necessary metadata files in the distribution
        metadata_files = ['LICENSE', 'README.md']
        for file in metadata_files:
            if os.path.exists(file):
                shutil.copy(file, dist_dir)
                print(f"  - Added {file} to distribution")
        
        # Create ZIP
        shutil.make_archive(dist_zip_name, 'zip', dist_dir)
        print(f"\nSUCCESS: Distribution package created: {dist_zip_name}.zip")
    except Exception as e:
        print(f"\nWARNING: Failed to create ZIP package: {e}")

    print("\n====================================================")
    print("Build Process Complete!")
    print("====================================================")

if __name__ == "__main__":
    # Ensure current directory is project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    build()
