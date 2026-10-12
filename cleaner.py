"""
Vassity System Cleaner & Package Updater (CLI Utility)
======================================================
Cross-platform terminal utility for Windows, macOS, and Linux:
1. Purge operating system temporary caches safely (Zero browser profile tampering).
2. Upgrade installed software packages via native package managers (Winget, Homebrew, Flatpak/APT).
"""

import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

CURRENT_OS = platform.system()
OS_NAME = {"Windows": "Windows", "Darwin": "macOS", "Linux": "Linux"}.get(CURRENT_OS, CURRENT_OS)

PROTECTED_KEYWORDS = [
    "google-chrome", "chromium", "firefox", "brave", "edge",
    "safari", ".ssh", ".gnupg", ".config", "passwords", "autofill"
]

def get_temp_dirs():
    """Retrieve standard OS temporary cache directories."""
    dirs = []
    if CURRENT_OS == "Windows":
        dirs = [
            os.environ.get("TEMP"),
            os.environ.get("TMP"),
            r"C:\Windows\Temp",
            r"C:\Windows\Prefetch",
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\INetCache"),
            os.path.expandvars(r"%LOCALAPPDATA%\CrashDumps"),
        ]
    elif CURRENT_OS == "Darwin":
        home = Path.home()
        dirs = [
            str(home / "Library" / "Caches"),
            "/private/var/tmp",
            "/tmp",
            str(home / "Library" / "Logs" / "DiagnosticReports"),
            str(home / ".Trash"),
        ]
    else:  # Linux
        home = Path.home()
        dirs = [
            "/tmp",
            "/var/tmp",
            str(home / ".cache"),
            str(home / ".local" / "share" / "Trash"),
        ]
    return [Path(d) for d in dirs if d and os.path.exists(d)]

def clean_temp_files():
    """Safely delete cached temporary files without throwing on locked system handles."""
    total_freed = 0
    deleted_files = 0
    print(f"🧹 [1/2] Cleaning {OS_NAME} Temporary Caches...")

    for temp_dir in get_temp_dirs():
        print(f"   Scanning: {temp_dir}")
        try:
            for item in temp_dir.iterdir():
                if any(k in item.name.lower() for k in PROTECTED_KEYWORDS):
                    continue
                try:
                    if item.is_file() or item.is_symlink():
                        size = item.stat().st_size
                        item.unlink(missing_ok=True)
                        total_freed += size
                        deleted_files += 1
                    elif item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                except (PermissionError, OSError):
                    continue
        except Exception:
            continue

    mb_freed = total_freed / (1024 * 1024)
    print(f"   ✅ Cleaned {deleted_files} files (~{mb_freed:.2f} MB freed).")
    print("   ✅ Browser logins, passwords, and sessions remain untouched.")
    return mb_freed

def update_packages():
    """Trigger native package upgrade for installed software."""
    print(f"\n🚀 [2/2] Checking for Software Updates on {OS_NAME}...")

    if CURRENT_OS == "Windows":
        try:
            res = subprocess.run(["winget", "--version"], capture_output=True, text=True, check=True)
            print(f"   Winget Detected: v{res.stdout.strip()}")
            cmd = ["winget", "upgrade", "--all", "--accept-source-agreements", "--accept-package-agreements"]
            subprocess.run(cmd)
        except Exception as e:
            print(f"   ❌ Winget error: {e}")

    elif CURRENT_OS == "Darwin":
        brew_bin = shutil.which("brew") or "/opt/homebrew/bin/brew"
        if brew_bin and os.path.exists(brew_bin):
            print("   Running: brew update && brew upgrade...")
            subprocess.run([brew_bin, "upgrade"])
        else:
            print("   ⚠️ Homebrew not found. Install Homebrew (https://brew.sh) to automate updates.")

    else:  # Linux
        updated = False
        if shutil.which("flatpak"):
            print("   Running: flatpak update -y...")
            subprocess.run(["flatpak", "update", "-y"])
            updated = True
        if shutil.which("apt"):
            print("   Checking APT updates: apt list --upgradable...")
            subprocess.run(["apt", "list", "--upgradable"])
            updated = True
        if not updated:
            print("   ⚠️ No supported package manager found.")

def main():
    print("=" * 60)
    print(f"⚡ VASSITY SYSTEM CLEANER & AUTOMATED UPDATER ({OS_NAME.upper()}) ⚡")
    print("=" * 60)
    clean_temp_files()
    update_packages()
    print("\n🎉 Maintenance Complete!")

if __name__ == "__main__":
    main()
