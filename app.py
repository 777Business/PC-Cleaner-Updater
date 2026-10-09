"""
Vassity PC Cleaner & Updater
============================
Open-Source Windows Utility by Vassity.
- Safely cleans temporary caches, Prefetch, and crash dumps without touching browser passwords or autofill.
- Updates all installed applications cleanly via the Windows Package Manager (Winget).
"""

import sys
import os
import re
import shutil
import subprocess
import threading
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont

class WorkerSignals(QObject):
    log = Signal(str)
    queue_update = Signal(int, int, str)  # current, total, app_name
    status_text = Signal(str)
    finished = Signal()

class CleanerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vassity PC Cleaner & Updater (Open Source)")
        self.setFixedSize(680, 560)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0d1117;
            }
            QLabel {
                color: #e2e8f0;
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            }
            QFrame.card {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 16px;
            }
            QPushButton {
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: 600;
                border-radius: 6px;
                padding: 10px 16px;
                border: none;
            }
            QPushButton.clean-btn {
                background-color: #06b6d4;
                color: #042f2e;
            }
            QPushButton.clean-btn:hover {
                background-color: #22d3ee;
            }
            QPushButton.update-btn {
                background-color: #8b5cf6;
                color: #ffffff;
            }
            QPushButton.update-btn:hover {
                background-color: #a78bfa;
            }
            QPushButton:disabled {
                background-color: #21262d;
                color: #6e7681;
            }
            QTextEdit {
                background-color: #090d16;
                color: #7dd3fc;
                border: 1px solid #21262d;
                border-radius: 8px;
                font-family: 'Consolas', 'Cascadia Code', monospace;
                font-size: 12px;
                padding: 10px;
            }
            QProgressBar {
                background-color: #21262d;
                border-radius: 2px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #8b5cf6;
                border-radius: 2px;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("⚡ Vassity PC Maintenance")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        subtitle = QLabel("Safe junk purge & Winget software updater. Zero browser autofill or personal data touched.")
        subtitle.setStyleSheet("color: #8b949e; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        badge = QLabel(" v1.0 • OPEN SOURCE ")
        badge.setStyleSheet("color: #38bdf8; background: #0c2d48; border: 1px solid #0284c7; border-radius: 10px; padding: 4px 8px; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(badge)
        main_layout.addLayout(header_layout)

        # 2 Feature Action Cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)

        # Card 1: Safe Cleaner
        card_clean = QFrame()
        card_clean.setProperty("class", "card")
        clean_vbox = QVBoxLayout(card_clean)
        clean_title = QLabel("🧹 Safe Temporary Cleaner")
        clean_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        clean_desc = QLabel("Safely purges %TEMP%, Windows Temp, Prefetch, and crash logs. Preserves all browser logins, autofill, passwords, and cache.")
        clean_desc.setWordWrap(True)
        clean_desc.setStyleSheet("color: #8b949e; font-size: 11px; line-height: 1.4;")
        
        self.btn_clean = QPushButton("Clean PC Temp Junk")
        self.btn_clean.setProperty("class", "clean-btn")
        self.btn_clean.setCursor(Qt.PointingHandCursor)
        self.btn_clean.clicked.connect(self.start_clean)
        
        clean_vbox.addWidget(clean_title)
        clean_vbox.addWidget(clean_desc)
        clean_vbox.addStretch()
        clean_vbox.addWidget(self.btn_clean)
        cards_layout.addWidget(card_clean)

        # Card 2: Winget Updater
        card_update = QFrame()
        card_update.setProperty("class", "card")
        update_vbox = QVBoxLayout(card_update)
        update_title = QLabel("🚀 Real Software Updates")
        update_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        update_desc = QLabel("Bypasses buggy Windows Update. Uses native Windows Package Manager (Winget) to silently upgrade installed software.")
        update_desc.setWordWrap(True)
        update_desc.setStyleSheet("color: #8b949e; font-size: 11px; line-height: 1.4;")
        
        self.btn_update = QPushButton("Update All Software")
        self.btn_update.setProperty("class", "update-btn")
        self.btn_update.setCursor(Qt.PointingHandCursor)
        self.btn_update.clicked.connect(self.start_update)

        update_vbox.addWidget(update_title)
        update_vbox.addWidget(update_desc)
        update_vbox.addStretch()
        update_vbox.addWidget(self.btn_update)
        cards_layout.addWidget(card_update)

        main_layout.addLayout(cards_layout)

        # Discreet Status & Queue Bar
        status_bar_layout = QHBoxLayout()
        status_bar_layout.setContentsMargins(4, 0, 4, 0)
        
        self.lbl_status = QLabel("● Ready")
        self.lbl_status.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 500;")
        status_bar_layout.addWidget(self.lbl_status)
        status_bar_layout.addStretch()

        self.lbl_queue = QLabel("")
        self.lbl_queue.setStyleSheet("color: #a78bfa; font-size: 11px; font-weight: 600; background: #2e1065; padding: 2px 8px; border-radius: 6px;")
        self.lbl_queue.setVisible(False)
        status_bar_layout.addWidget(self.lbl_queue)
        
        main_layout.addLayout(status_bar_layout)

        # Subtle 3px Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Log Output Console
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setPlaceholderText("Output log will appear here when an action starts...")
        main_layout.addWidget(self.console)

        # Signals
        self.signals = WorkerSignals()
        self.signals.log.connect(self.append_log)
        self.signals.queue_update.connect(self.on_queue_update)
        self.signals.status_text.connect(self.on_status_update)
        self.signals.finished.connect(self.on_finished)

    def append_log(self, text):
        self.console.append(text)

    def on_status_update(self, text):
        self.lbl_status.setText(text)

    def on_queue_update(self, current, total, app_name):
        if total > 0:
            self.lbl_queue.setVisible(True)
            self.lbl_queue.setText(f"Queue: {current}/{total}")
            self.progress_bar.setVisible(True)
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
            if app_name:
                self.lbl_status.setText(f"● Updating: {app_name}")
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
        self.append_log("\n✨ Completed successfully!\n")

    def start_clean(self):
        self.set_buttons_enabled(False)
        self.console.clear()
        self.lbl_status.setText("● Cleaning junk files...")
        self.append_log("🧹 Starting Safe PC Cleaning...")
        threading.Thread(target=self._run_clean, daemon=True).start()

    def _run_clean(self):
        temp_paths = [
            os.environ.get("TEMP"),
            os.environ.get("TMP"),
            r"C:\Windows\Temp",
            r"C:\Windows\Prefetch",
            os.path.expandvars(r"%LOCALAPPDATA%\CrashDumps")
        ]
        total_freed = 0
        total_files = 0
        
        for p in temp_paths:
            if not p or not os.path.exists(p):
                continue
            path_obj = Path(p)
            self.signals.log.emit(f"   Scanning: {p}")
            try:
                for item in path_obj.iterdir():
                    try:
                        if item.is_file() or item.is_symlink():
                            size = item.stat().st_size
                            item.unlink(missing_ok=True)
                            total_freed += size
                            total_files += 1
                        elif item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                    except (PermissionError, OSError):
                        continue
            except Exception:
                continue

        mb = total_freed / (1024 * 1024)
        self.signals.log.emit(f"✅ Successfully deleted {total_files} junk files.")
        self.signals.log.emit(f"🎉 Freed ~{mb:.2f} MB of disk space safely.")
        self.signals.finished.emit()

    def start_update(self):
        self.set_buttons_enabled(False)
        self.console.clear()
        self.lbl_status.setText("● Checking for updates via Winget...")
        self.append_log("🚀 Checking installed software via Windows Package Manager...")
        threading.Thread(target=self._run_update, daemon=True).start()

    def _run_update(self):
        try:
            # First, check available updates list
            check_cmd = ["winget", "upgrade", "--accept-source-agreements"]
            check_proc = subprocess.run(
                check_cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Find upgradeable package count
            upgradeable = []
            for line in check_proc.stdout.splitlines():
                # Typical line: Name Id Version Available Source
                match = re.match(r"^([\w\s\.\-]+?)\s{2,}([A-Za-z0-9\.\-_]+)\s+(\S+)\s+(\S+)\s+(\S+)", line)
                if match:
                    name = match.group(1).strip()
                    pkg_id = match.group(2).strip()
                    if pkg_id.lower() not in ["id", "version", "available"]:
                        upgradeable.append((name, pkg_id))
            
            total = len(upgradeable)
            if total == 0:
                self.signals.log.emit("✅ All packages are currently up to date! Nothing to install.")
                self.signals.finished.emit()
                return

            self.signals.log.emit(f"📦 Found {total} package(s) ready to update.")
            for idx, (name, pkg_id) in enumerate(upgradeable, start=1):
                self.signals.queue_update.emit(idx, total, name)
                self.signals.log.emit(f"\n▶ [{idx}/{total}] Updating {name} ({pkg_id})...")
                
                cmd = ["winget", "upgrade", "--id", pkg_id, "--silent", "--accept-source-agreements", "--accept-package-agreements"]
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                if proc.returncode == 0:
                    self.signals.log.emit(f"  ✓ {name} updated successfully.")
                else:
                    self.signals.log.emit(f"  ⚠ {name} finished (exit code {proc.returncode}).")
            
            self.signals.log.emit("\n🎉 All queued package updates processed!")
        except Exception as e:
            self.signals.log.emit(f"❌ Error during update: {e}")
        self.signals.finished.emit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CleanerApp()
    window.show()
    sys.exit(app.exec())
