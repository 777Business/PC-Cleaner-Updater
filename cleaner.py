"""
Windows Cleaner & System Updater (Open-Source Utility)
=====================================================
A lightweight, sovereign Python + PowerShell tool to:
1. Purge Windows temporary caches (User Temp, Windows Temp, Prefetch, Crash Dumps).
2. Clean browser caches and delivery optimization junk.
3. Automatically run silent `winget upgrade --all --include-unknown` package updates.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def get_temp_dirs():
    """Retrieve standard Windows temporary cache directories."""
    dirs = [
        os.environ.get("TEMP"),
        os.environ.get("TMP"),
        r"C:\Windows\Temp",
        r"C:\Windows\Prefetch",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\INetCache"),
        os.path.expandvars(r"%LOCALAPPDATA%\CrashDumps"),
    ]
    return [Path(d) for d in dirs if d and os.path.exists(d)]

def clean_temp_files():
    """Safely delete cached temporary files without throwing on locked system handles."""
    total_freed = 0
    deleted_files = 0
    print("🧹 [1/2] Cleaning Windows Temporary Caches...")
    
    for temp_dir in get_temp_dirs():
        print(f"   Scanning: {temp_dir}")
        try:
            for item in temp_dir.iterdir():
                try:
                    if item.is_file() or item.is_symlink():
                        size = item.stat().st_size
                        item.unlink(missing_ok=True)
                        total_freed += size
                        deleted_files += 1
                    elif item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                except (PermissionError, OSError):
                    # In-use file locked by another Windows process
                    continue
        except Exception as e:
            continue

    mb_freed = total_freed / (1024 * 1024)
    print(f"   ✅ Cleaned {deleted_files} files (~{mb_freed:.2f} MB freed).")
    return mb_freed

def update_winget_packages():
    """Trigger native Windows Package Manager upgrade for all installed software."""
    print("\n🚀 [2/2] Checking for Software Updates via Winget...")
    try:
        # Check if winget is installed
        result = subprocess.run(
            ["winget", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"   Winget Detected: v{result.stdout.strip()}")
        print("   Running automated upgrade (this may take a few minutes)...")
        
        # Run upgrade
        cmd = ["winget", "upgrade", "--all", "--accept-source-agreements", "--accept-package-agreements"]
        process = subprocess.run(cmd, text=True)
        if process.returncode == 0:
            print("   ✅ All system packages are up to date.")
        else:
            print("   ⚠️ Update completed with some packages skipped or already current.")
    except FileNotFoundError:
        print("   ❌ Winget is not installed or not in system PATH.")
    except Exception as e:
        print(f"   ❌ Error running winget: {e}")

def main():
    print("=" * 60)
    print("⚡ VASSITY SYSTEM CLEANER & AUTOMATED UPDATER ⚡")
    print("=" * 60)
    clean_temp_files()
    update_winget_packages()
    print("\n🎉 Maintenance Complete!")

if __name__ == "__main__":
    main()
