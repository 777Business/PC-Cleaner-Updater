"""
Vassity PC Maintenance & Software Updater
=========================================
Architected for precision, transparency, safety, and sovereignty.
- Zero browser data tampering (passwords, logins, autofill remain untouched).
- Purges system temporary files, prefetch cache, and error dumps across Windows, macOS, and Linux.
- Upgrades desktop software silently using native package managers (Winget, Homebrew, Flatpak/APT).
- Built-in GitHub Releases checker with 1-click self-updating engine.
"""

import sys
import os
import re
import json
import shutil
import platform
import subprocess
import threading
import urllib.request
import webbrowser
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont, QCursor, QIcon

# Application Configuration
APP_VERSION = "1.1.0"
GITHUB_REPO = "777Business/PC-Cleaner-Updater"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"

# OS Detection
CURRENT_OS = platform.system()  # 'Windows', 'Darwin' (macOS), 'Linux'
OS_NAME = {
    "Windows": "Windows",
    "Darwin": "macOS",
    "Linux": "Linux"
}.get(CURRENT_OS, CURRENT_OS)


def parse_version_tuple(v_str):
    """Convert version string like 'v1.2.0' to (1, 2, 0) for safe comparison."""
    parts = re.findall(r"\d+", str(v_str))
    return tuple(map(int, parts)) if parts else (0,)


class WorkerSignals(QObject):
    log = Signal(str)
    queue_update = Signal(int, int, str)  # current, total, app_name
    status_text = Signal(str)
    progress_val = Signal(int)
    finished = Signal()

    # Self-update signals
    update_available = Signal(str, str, str)  # new_version, release_page_url, asset_download_url
    update_progress = Signal(int, str)        # percent, status message
    update_done = Signal(bool, str)           # success, error or success message


class CleanerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Vassity PC Maintenance — Open Source ({OS_NAME})")
        self.setFixedSize(720, 620)

        # Set Application & Window Icon
        icon_path = Path(__file__).parent / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b0f17;
            }
            QWidget#central {
                background-color: #0b0f17;
            }
            QLabel {
                color: #f1f5f9;
                font-family: 'Segoe UI Variable Display', 'Segoe UI', system-ui, sans-serif;
            }
            QFrame.action-card {
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 12px;
                padding: 16px;
            }
            QFrame.action-card:hover {
                border: 1px solid #374151;
            }
            QPushButton {
                font-family: 'Segoe UI Variable Display', 'Segoe UI', system-ui, sans-serif;
                font-size: 13px;
                font-weight: 600;
                border-radius: 8px;
                padding: 11px 18px;
                border: none;
            }
            QPushButton.clean-btn {
                background-color: #059669;
                color: #ffffff;
            }
            QPushButton.clean-btn:hover {
                background-color: #10b981;
            }
            QPushButton.clean-btn:pressed {
                background-color: #047857;
            }
            QPushButton.update-btn {
                background-color: #2563eb;
                color: #ffffff;
            }
            QPushButton.update-btn:hover {
                background-color: #3b82f6;
            }
            QPushButton.update-btn:pressed {
                background-color: #1d4ed8;
            }
            QPushButton.banner-btn-primary {
                background-color: #10b981;
                color: #042f2e;
                font-size: 11px;
                font-weight: 700;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton.banner-btn-primary:hover {
                background-color: #34d399;
            }
            QPushButton.banner-btn-secondary {
                background-color: #1e293b;
                color: #cbd5e1;
                font-size: 11px;
                font-weight: 600;
                padding: 6px 10px;
                border-radius: 6px;
                border: 1px solid #334155;
            }
            QPushButton.banner-btn-secondary:hover {
                background-color: #334155;
                color: #ffffff;
            }
            QPushButton.banner-btn-close {
                background-color: transparent;
                color: #94a3b8;
                font-size: 12px;
                font-weight: bold;
                padding: 4px 8px;
            }
            QPushButton.banner-btn-close:hover {
                color: #f87171;
            }
            QPushButton:disabled {
                background-color: #1f2937;
                color: #64748b;
            }
            QTextEdit {
                background-color: #080c14;
                color: #94a3b8;
                border: 1px solid #1e293b;
                border-radius: 8px;
                font-family: 'Cascadia Mono', 'Cascadia Code', 'Consolas', 'JetBrains Mono', monospace;
                font-size: 12px;
                line-height: 1.5;
                padding: 12px;
            }
            QProgressBar {
                background-color: #111827;
                border: none;
                height: 2px;
            }
            QProgressBar::chunk {
                background-color: #38bdf8;
            }
        """)

        central_widget = QWidget()
        central_widget.setObjectName("central")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # Header Section
        header_layout = QHBoxLayout()
        header_text_box = QVBoxLayout()
        header_text_box.setSpacing(3)

        title = QLabel(f"Vassity PC Maintenance")
        title.setFont(QFont("Segoe UI", 17, QFont.Bold))
        subtitle = QLabel(f"Lightweight system cleaner & package updater for {OS_NAME}.")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px;")

        header_text_box.addWidget(title)
        header_text_box.addWidget(subtitle)
        header_layout.addLayout(header_text_box)
        header_layout.addStretch()

        self.version_pill = QLabel(f"v{APP_VERSION} • {OS_NAME}")
        self.version_pill.setCursor(QCursor(Qt.PointingHandCursor))
        self.version_pill.setToolTip("Click to manually check for updates")
        self.version_pill.setStyleSheet("""
            color: #38bdf8;
            background-color: #0c233c;
            border: 1px solid #0369a1;
            border-radius: 12px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        self.version_pill.mousePressEvent = lambda e: self.check_updates_interactive()
        header_layout.addWidget(self.version_pill)
        main_layout.addLayout(header_layout)

        # Self-Update In-App Notification Banner (Initially hidden)
        self.update_banner = QFrame()
        self.update_banner.setObjectName("updateBanner")
        self.update_banner.setStyleSheet("""
            QFrame#updateBanner {
                background: #0f1f33;
                border: 1px solid #0284c7;
                border-radius: 10px;
                padding: 10px 14px;
            }
        """)
        self.update_banner.setVisible(False)
        banner_layout = QHBoxLayout(self.update_banner)
        banner_layout.setContentsMargins(4, 2, 4, 2)
        banner_layout.setSpacing(10)

        self.lbl_update_banner = QLabel("🚀 Update available!")
        self.lbl_update_banner.setStyleSheet("color: #e0f2fe; font-size: 12px; font-weight: 600;")
        banner_layout.addWidget(self.lbl_update_banner)
        banner_layout.addStretch()

        self.btn_banner_update = QPushButton("⚡ Update Now")
        self.btn_banner_update.setProperty("class", "banner-btn-primary")
        self.btn_banner_update.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_banner_update.clicked.connect(self.start_self_update)
        banner_layout.addWidget(self.btn_banner_update)

        self.btn_banner_notes = QPushButton("Changelog")
        self.btn_banner_notes.setProperty("class", "banner-btn-secondary")
        self.btn_banner_notes.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_banner_notes.clicked.connect(self.open_release_notes)
        banner_layout.addWidget(self.btn_banner_notes)

        self.btn_banner_close = QPushButton("✕")
        self.btn_banner_close.setProperty("class", "banner-btn-close")
        self.btn_banner_close.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_banner_close.clicked.connect(lambda: self.update_banner.setVisible(False))
        banner_layout.addWidget(self.btn_banner_close)

        main_layout.addWidget(self.update_banner)

        # Action Cards Layout
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)

        # Card 1: Safe Temp Purge
        card_clean = QFrame()
        card_clean.setProperty("class", "action-card")
        clean_vbox = QVBoxLayout(card_clean)
        clean_vbox.setSpacing(8)

        clean_title = QLabel(f"Safe Cache Purge ({OS_NAME})")
        clean_title.setFont(QFont("Segoe UI", 13, QFont.Bold))

        if CURRENT_OS == "Windows":
            clean_desc_text = "Sweeps %TEMP%, Windows Temp, Prefetch, and crash logs to free drive space."
        elif CURRENT_OS == "Darwin":
            clean_desc_text = "Purges ~/Library/Caches, temporary dumps, and diagnostic error reports."
        else:
            clean_desc_text = "Sweeps /tmp, /var/tmp, user ~/.cache junk, and error logs safely."

        clean_desc = QLabel(clean_desc_text)
        clean_desc.setWordWrap(True)
        clean_desc.setStyleSheet("color: #94a3b8; font-size: 11px; line-height: 1.4;")

        clean_assurance = QLabel("✓ Browser logins, cookies & passwords untouched")
        clean_assurance.setStyleSheet("color: #34d399; font-size: 10px; font-weight: 500;")

        self.btn_clean = QPushButton("Run Safe Clean")
        self.btn_clean.setProperty("class", "clean-btn")
        self.btn_clean.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_clean.clicked.connect(self.start_clean)

        clean_vbox.addWidget(clean_title)
        clean_vbox.addWidget(clean_desc)
        clean_vbox.addWidget(clean_assurance)
        clean_vbox.addStretch()
        clean_vbox.addWidget(self.btn_clean)
        cards_layout.addWidget(card_clean)

        # Card 2: Software Package Updater
        card_update = QFrame()
        card_update.setProperty("class", "action-card")
        update_vbox = QVBoxLayout(card_update)
        update_vbox.setSpacing(8)

        if CURRENT_OS == "Windows":
            updater_name = "Software Updater (Winget)"
            updater_desc_text = "Checks installed desktop apps via native Microsoft Winget without telemetry."
            updater_tag = "✓ Official Microsoft package manager automation"
        elif CURRENT_OS == "Darwin":
            updater_name = "Software Updater (Homebrew)"
            updater_desc_text = "Checks installed applications and formulas using native macOS Homebrew."
            updater_tag = "✓ Official Homebrew package ecosystem"
        else:
            updater_name = "Software Updater (Flatpak & Native)"
            updater_desc_text = "Scans desktop apps via Flatpak and queries distribution package managers."
            updater_tag = "✓ Sovereign open-source package ecosystem"

        update_title = QLabel(updater_name)
        update_title.setFont(QFont("Segoe UI", 13, QFont.Bold))

        update_desc = QLabel(updater_desc_text)
        update_desc.setWordWrap(True)
        update_desc.setStyleSheet("color: #94a3b8; font-size: 11px; line-height: 1.4;")

        update_assurance = QLabel(updater_tag)
        update_assurance.setStyleSheet("color: #60a5fa; font-size: 10px; font-weight: 500;")

        self.btn_update = QPushButton("Check & Update All")
        self.btn_update.setProperty("class", "update-btn")
        self.btn_update.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_update.clicked.connect(self.start_update)

        update_vbox.addWidget(update_title)
        update_vbox.addWidget(update_desc)
        update_vbox.addWidget(update_assurance)
        update_vbox.addStretch()
        update_vbox.addWidget(self.btn_update)
        cards_layout.addWidget(card_update)

        main_layout.addLayout(cards_layout)

        # Minimalist Telemetry & Queue Strip
        telemetry_layout = QHBoxLayout()
        telemetry_layout.setContentsMargins(2, 4, 2, 0)

        self.lbl_status = QLabel("● Ready")
        self.lbl_status.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600;")
        telemetry_layout.addWidget(self.lbl_status)
        telemetry_layout.addStretch()

        self.lbl_queue = QLabel("")
        self.lbl_queue.setStyleSheet("""
            color: #93c5fd;
            background-color: #1e293b;
            border-radius: 8px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 600;
        """)
        self.lbl_queue.setVisible(False)
        telemetry_layout.addWidget(self.lbl_queue)

        main_layout.addLayout(telemetry_layout)

        # Hairline Progress Indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Stream Terminal Console
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setPlaceholderText(f"Ready on {OS_NAME}. Select an action above to start...")
        main_layout.addWidget(self.console)

        # Signals
        self.signals = WorkerSignals()
        self.signals.log.connect(self.append_log)
        self.signals.queue_update.connect(self.on_queue_update)
        self.signals.status_text.connect(self.on_status_update)
        self.signals.progress_val.connect(self.on_progress_update)
        self.signals.finished.connect(self.on_finished)

        # Self-Update Signals
        self.signals.update_available.connect(self.on_update_available)
        self.signals.update_progress.connect(self.on_update_progress)
        self.signals.update_done.connect(self.on_update_done)

        # State for latest release found
        self.pending_update_version = None
        self.pending_release_url = None
        self.pending_asset_url = None

        # Check for GitHub updates silently on startup
        threading.Thread(target=self._check_for_updates, args=(False,), daemon=True).start()

    def append_log(self, text):
        self.console.append(text)

    def on_status_update(self, text):
        self.lbl_status.setText(text)

    def on_progress_update(self, value):
        self.progress_bar.setValue(value)

    def on_queue_update(self, current, total, app_name):
        if total > 0:
            self.lbl_queue.setVisible(True)
            self.lbl_queue.setText(f"Queue {current}/{total}")
            self.progress_bar.setVisible(True)
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
            if app_name:
                self.lbl_status.setText(f"● Upgrading: {app_name}")
        else:
            self.lbl_queue.setVisible(False)
            self.progress_bar.setVisible(False)

    def set_buttons_enabled(self, enabled):
        self.btn_clean.setEnabled(enabled)
        self.btn_update.setEnabled(enabled)

    def on_finished(self):
        self.set_buttons_enabled(True)
        self.lbl_status.setText("● Ready")
        self.lbl_queue.setVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.append_log("\n✓ Operation complete.\n")

    # =========================================================================
    # GITHUB AUTO-UPDATE SYSTEM
    # =========================================================================
    def check_updates_interactive(self):
        """User clicked the version pill to manually trigger an update check."""
        self.append_log("[UPDATE CHECK] Checking GitHub for new version...")
        threading.Thread(target=self._check_for_updates, args=(True,), daemon=True).start()

    def _check_for_updates(self, interactive=False):
        """Queries GitHub Releases API in background with timeout safety."""
        try:
            req = urllib.request.Request(
                RELEASES_API,
                headers={"User-Agent": f"VassityCleaner/{APP_VERSION} (Python)"}
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    latest_tag = data.get("tag_name", "").strip()
                    html_url = data.get("html_url", GITHUB_RELEASES_URL)
                    assets = data.get("assets", [])

                    latest_ver = latest_tag.lstrip("v")
                    current_ver = APP_VERSION.lstrip("v")

                    if parse_version_tuple(latest_ver) > parse_version_tuple(current_ver):
                        # Match asset for current OS
                        download_url = None
                        for asset in assets:
                            name = asset.get("name", "").lower()
                            url = asset.get("browser_download_url")
                            if CURRENT_OS == "Windows" and name.endswith(".exe"):
                                download_url = url
                                break
                            elif CURRENT_OS == "Darwin" and (name.endswith(".dmg") or "macos" in name or "mac" in name):
                                download_url = url
                                break
                            elif CURRENT_OS == "Linux" and ("linux" in name or name.endswith(".appimage") or name.endswith(".tar.gz")):
                                download_url = url
                                break

                        # Fallback to direct download URL or release page
                        if not download_url and assets:
                            download_url = assets[0].get("browser_download_url")

                        self.signals.update_available.emit(latest_tag, html_url, download_url or html_url)
                        return

            if interactive:
                self.signals.log.emit(f"✓ Vassity Cleaner is already up to date (v{APP_VERSION}).")
        except Exception as e:
            if interactive:
                self.signals.log.emit(f"• Could not reach GitHub update server: {e}")

    def on_update_available(self, new_ver, release_url, asset_url):
        self.pending_update_version = new_ver
        self.pending_release_url = release_url
        self.pending_asset_url = asset_url

        self.lbl_update_banner.setText(f"🚀 New version {new_ver} available!")
        self.btn_banner_update.setEnabled(True)
        self.btn_banner_update.setText("⚡ Update Now")
        self.update_banner.setVisible(True)
        self.append_log(f"\n📢 [UPDATE AVAILABLE] Version {new_ver} is available on GitHub!")

    def open_release_notes(self):
        url = self.pending_release_url or GITHUB_RELEASES_URL
        webbrowser.open(url)

    def start_self_update(self):
        """Starts the 1-click download and replacement process."""
        if not self.pending_asset_url:
            self.open_release_notes()
            return

        self.btn_banner_update.setEnabled(False)
        self.btn_banner_update.setText("Downloading...")
        self.lbl_update_banner.setText(f"⬇️ Downloading {self.pending_update_version}...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        threading.Thread(target=self._run_self_update, daemon=True).start()

    def _run_self_update(self):
        """Downloads the binary and executes one-click swap."""
        try:
            url = self.pending_asset_url
            self.signals.log.emit(f"[SELF-UPDATE] Downloading latest release from:\n  {url}")

            req = urllib.request.Request(
                url,
                headers={"User-Agent": f"VassityCleaner/{APP_VERSION}"}
            )

            # Determine temp file name
            filename = Path(url).name
            if not filename or "?" in filename:
                filename = "VassityCleaner.exe" if CURRENT_OS == "Windows" else "VassityCleaner-updated"

            temp_dest = Path(os.environ.get("TEMP", os.environ.get("TMP", "/tmp"))) / f"vassity_update_{filename}"

            with urllib.request.urlopen(req, timeout=30) as resp, open(temp_dest, "wb") as out_file:
                total_size = int(resp.headers.get("content-length", 0))
                downloaded = 0
                chunk_size = 64 * 1024

                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = int((downloaded / total_size) * 100)
                        self.signals.update_progress.emit(pct, f"Downloading: {pct}%")

            self.signals.update_progress.emit(100, "Applying update...")
            self.signals.log.emit("✓ Download complete. Initiating automatic update swap...")

            # Check if running as compiled executable (PyInstaller)
            is_frozen = getattr(sys, "frozen", False)
            current_exe = Path(sys.executable).resolve()

            if CURRENT_OS == "Windows":
                if is_frozen:
                    # Windows executable file locking workaround:
                    # Spawn detached batch script to wait 1 second, replace file, and restart
                    updater_bat = temp_dest.parent / "vassity_apply_update.bat"
                    batch_script = f"""@echo off
chcp 65001 >nul
timeout /t 1 /nobreak >nul
move /y "{str(temp_dest)}" "{str(current_exe)}" >nul
start "" "{str(current_exe)}"
del "%~f0"
"""
                    with open(updater_bat, "w", encoding="utf-8") as f:
                        f.write(batch_script)

                    subprocess.Popen(
                        ["cmd.exe", "/c", str(updater_bat)],
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                    )
                    self.signals.update_done.emit(True, "Restarting application...")
                    QApplication.quit()
                    return
                else:
                    self.signals.update_done.emit(
                        True,
                        f"Downloaded update to {temp_dest}. (Running in Python source mode)."
                    )
            elif CURRENT_OS in ["Darwin", "Linux"]:
                # Make executable
                os.chmod(temp_dest, 0o755)
                if is_frozen:
                    # Linux/macOS allow unlinking/overwriting running binary
                    shutil.move(str(temp_dest), str(current_exe))
                    subprocess.Popen([str(current_exe)])
                    self.signals.update_done.emit(True, "Restarting application...")
                    QApplication.quit()
                    return
                else:
                    self.signals.update_done.emit(
                        True,
                        f"Updated binary downloaded to: {temp_dest}"
                    )
        except Exception as e:
            self.signals.update_done.emit(False, f"Update failed: {e}")

    def on_update_progress(self, pct, msg):
        self.progress_bar.setValue(pct)
        self.lbl_update_banner.setText(f"⬇️ {msg}")

    def on_update_done(self, success, message):
        self.progress_bar.setVisible(False)
        self.lbl_update_banner.setText(message)
        self.signals.log.emit(f"\n{message}")
        if not success:
            self.btn_banner_update.setEnabled(True)
            self.btn_banner_update.setText("Retry Update")

    # =========================================================================
    # SAFE CACHE PURGE (CROSS-PLATFORM)
    # =========================================================================
    def start_clean(self):
        self.set_buttons_enabled(False)
        self.console.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        self.lbl_status.setText(f"● Purging {OS_NAME} temporary caches...")
        self.append_log(f"[CLEAN] Initiating safe cache purge on {OS_NAME}...")
        threading.Thread(target=self._run_clean, daemon=True).start()

    def _run_clean(self):
        temp_paths = []

        if CURRENT_OS == "Windows":
            temp_paths = [
                os.environ.get("TEMP"),
                os.environ.get("TMP"),
                r"C:\Windows\Temp",
                r"C:\Windows\Prefetch",
                os.path.expandvars(r"%LOCALAPPDATA%\CrashDumps"),
                os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\INetCache")
            ]
        elif CURRENT_OS == "Darwin":
            home = Path.home()
            temp_paths = [
                str(home / "Library" / "Caches"),
                "/private/var/tmp",
                "/tmp",
                str(home / "Library" / "Logs" / "DiagnosticReports"),
                str(home / ".Trash")
            ]
        else:  # Linux
            home = Path.home()
            temp_paths = [
                "/tmp",
                "/var/tmp",
                str(home / ".cache"),
                str(home / ".local" / "share" / "Trash")
            ]

        # Sensitive folders that must NEVER be deleted to protect user credentials
        PROTECTED_KEYWORDS = [
            "google-chrome", "chromium", "firefox", "brave", "edge",
            "safari", ".ssh", ".gnupg", ".config", "passwords", "autofill"
        ]

        total_freed = 0
        total_files = 0

        for p in temp_paths:
            if not p or not os.path.exists(p):
                continue
            path_obj = Path(p)
            self.signals.log.emit(f"  • Checking: {p}")
            try:
                for item in path_obj.iterdir():
                    # Safety check
                    item_name_lower = item.name.lower()
                    if any(prot in item_name_lower for prot in PROTECTED_KEYWORDS):
                        continue

                    try:
                        if item.is_file() or item.is_symlink():
                            size = item.stat().st_size
                            item.unlink(missing_ok=True)
                            total_freed += size
                            total_files += 1
                        elif item.is_dir():
                            # If cleaning ~/.cache or Library/Caches, only sweep sub-items
                            for sub in item.rglob("*"):
                                if sub.is_file() or sub.is_symlink():
                                    try:
                                        s = sub.stat().st_size
                                        sub.unlink(missing_ok=True)
                                        total_freed += s
                                        total_files += 1
                                    except Exception:
                                        continue
                            shutil.rmtree(item, ignore_errors=True)
                    except (PermissionError, OSError):
                        continue
            except Exception:
                continue

        mb = total_freed / (1024 * 1024)
        self.signals.progress_val.emit(100)
        self.signals.log.emit(f"\n✓ Safely cleaned {total_files} junk files.")
        self.signals.log.emit(f"✓ Reclaimed {mb:.2f} MB of disk space.")
        self.signals.log.emit("✓ Browser profiles, logins, cookies, and passwords remained untouched.")
        self.signals.finished.emit()

    # =========================================================================
    # SILENT SOFTWARE UPDATER (CROSS-PLATFORM)
    # =========================================================================
    def start_update(self):
        self.set_buttons_enabled(False)
        self.console.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(5)
        self.lbl_status.setText(f"● Checking for desktop application upgrades on {OS_NAME}...")
        self.append_log(f"[UPDATER] Scanning applications on {OS_NAME}...")
        threading.Thread(target=self._run_update, daemon=True).start()

    def _run_update(self):
        if CURRENT_OS == "Windows":
            self._run_update_windows()
        elif CURRENT_OS == "Darwin":
            self._run_update_macos()
        else:
            self._run_update_linux()

    def _run_update_windows(self):
        try:
            check_cmd = ["winget", "upgrade", "--accept-source-agreements"]
            check_proc = subprocess.run(
                check_cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )

            upgradeable = []
            for line in check_proc.stdout.splitlines():
                match = re.match(r"^([\w\s\.\-]+?)\s{2,}([A-Za-z0-9\.\-_]+)\s+(\S+)\s+(\S+)\s+(\S+)", line)
                if match:
                    name = match.group(1).strip()
                    pkg_id = match.group(2).strip()
                    if pkg_id.lower() not in ["id", "version", "available"]:
                        upgradeable.append((name, pkg_id))

            total = len(upgradeable)
            if total == 0:
                self.signals.progress_val.emit(100)
                self.signals.log.emit("\n✓ All desktop applications are up to date.")
                self.signals.finished.emit()
                return

            self.signals.log.emit(f"\nFound {total} package(s) available for upgrade:")
            for idx, (name, pkg_id) in enumerate(upgradeable, start=1):
                self.signals.log.emit(f"  {idx}. {name} ({pkg_id})")

            for idx, (name, pkg_id) in enumerate(upgradeable, start=1):
                self.signals.queue_update.emit(idx, total, name)
                self.signals.log.emit(f"\n[{idx}/{total}] Upgrading {name}...")

                cmd = ["winget", "upgrade", "--id", pkg_id, "--silent", "--accept-source-agreements", "--accept-package-agreements"]
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                )
                if proc.returncode == 0:
                    self.signals.log.emit(f"  ✓ {name} updated.")
                else:
                    self.signals.log.emit(f"  • {name} completed (code {proc.returncode}).")

            self.signals.progress_val.emit(100)
            self.signals.log.emit("\n✓ All queued updates finished.")
        except Exception as e:
            self.signals.log.emit(f"\n❌ Error executing Winget: {e}")
        self.signals.finished.emit()

    def _run_update_macos(self):
        """macOS updater using Homebrew."""
        brew_bin = shutil.which("brew") or "/opt/homebrew/bin/brew" or "/usr/local/bin/brew"
        if not os.path.exists(brew_bin) and not shutil.which("brew"):
            self.signals.log.emit("⚠️ Homebrew ('brew') is not installed or not in PATH.")
            self.signals.log.emit("💡 To enable macOS package management, install Homebrew at https://brew.sh")
            self.signals.finished.emit()
            return

        try:
            self.signals.log.emit("[HOMEBREW] Checking for outdated formulas and casks...")
            check_proc = subprocess.run([brew_bin, "outdated"], capture_output=True, text=True)
            outdated_lines = [line.strip() for line in check_proc.stdout.splitlines() if line.strip()]

            if not outdated_lines:
                self.signals.progress_val.emit(100)
                self.signals.log.emit("\n✓ All macOS applications and packages are up to date.")
                self.signals.finished.emit()
                return

            total = len(outdated_lines)
            self.signals.log.emit(f"\nFound {total} package(s) available for upgrade:")
            for idx, pkg in enumerate(outdated_lines, start=1):
                self.signals.log.emit(f"  {idx}. {pkg}")

            for idx, pkg in enumerate(outdated_lines, start=1):
                pkg_name = pkg.split()[0]
                self.signals.queue_update.emit(idx, total, pkg_name)
                self.signals.log.emit(f"\n[{idx}/{total}] Upgrading {pkg_name}...")
                proc = subprocess.run([brew_bin, "upgrade", pkg_name], capture_output=True, text=True)
                if proc.returncode == 0:
                    self.signals.log.emit(f"  ✓ {pkg_name} updated.")
                else:
                    self.signals.log.emit(f"  • {pkg_name} completed (code {proc.returncode}).")

            self.signals.progress_val.emit(100)
            self.signals.log.emit("\n✓ All macOS packages updated.")
        except Exception as e:
            self.signals.log.emit(f"\n❌ Error running Homebrew: {e}")
        self.signals.finished.emit()

    def _run_update_linux(self):
        """Linux updater using Flatpak and native package managers."""
        updated_any = False

        # 1. Flatpak (Universal desktop app manager on Linux)
        if shutil.which("flatpak"):
            try:
                self.signals.log.emit("[FLATPAK] Scanning installed Flatpak applications...")
                proc = subprocess.run(["flatpak", "update", "-y"], capture_output=True, text=True)
                if proc.returncode == 0:
                    self.signals.log.emit("✓ Flatpak desktop applications upgraded successfully.")
                    updated_any = True
                else:
                    self.signals.log.emit(f"• Flatpak update status code: {proc.returncode}")
            except Exception as e:
                self.signals.log.emit(f"• Flatpak check skipped: {e}")

        # 2. Distribution Package Managers (APT, DNF, Pacman)
        if shutil.which("apt"):
            self.signals.log.emit("\n[APT] Checking Debian/Ubuntu system packages...")
            try:
                proc = subprocess.run(["apt", "list", "--upgradable"], capture_output=True, text=True)
                lines = [l for l in proc.stdout.splitlines() if "/" in l]
                if lines:
                    self.signals.log.emit(f"Found {len(lines)} system package(s) available for upgrade.")
                    self.signals.log.emit("💡 To upgrade system binaries with root privileges, run: sudo apt upgrade -y")
                else:
                    self.signals.log.emit("✓ APT packages are up to date.")
                updated_any = True
            except Exception as e:
                self.signals.log.emit(f"• APT check error: {e}")
        elif shutil.which("pacman"):
            self.signals.log.emit("\n[PACMAN] Arch Linux detected.")
            self.signals.log.emit("💡 Run 'sudo pacman -Syu' to upgrade rolling distribution packages.")
            updated_any = True
        elif shutil.which("dnf"):
            self.signals.log.emit("\n[DNF] Fedora/RHEL detected.")
            self.signals.log.emit("💡 Run 'sudo dnf upgrade' to upgrade system packages.")
            updated_any = True

        if not updated_any:
            self.signals.log.emit("\n⚠️ No recognized desktop package manager found (Flatpak, APT, DNF, Pacman).")

        self.signals.progress_val.emit(100)
        self.signals.finished.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CleanerApp()
    window.show()
    sys.exit(app.exec())
