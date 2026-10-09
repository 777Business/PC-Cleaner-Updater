"""
Vassity PC Maintenance & Software Updater
=========================================
Architected for precision, transparency, and safety.
- Zero browser data tampering (passwords, logins, autofill remain untouched).
- Purges system temporary files, prefetch cache, and error dumps.
- Upgrades desktop software silently using native Microsoft Winget.
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
from PySide6.QtGui import QFont, QCursor

class WorkerSignals(QObject):
    log = Signal(str)
    queue_update = Signal(int, int, str)  # current, total, app_name
    status_text = Signal(str)
    progress_val = Signal(int)
    finished = Signal()

class CleanerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vassity PC Maintenance — Open Source")
        self.setFixedSize(700, 580)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b0f17;
            }
            QWidget#central {
                background-color: #0b0f17;
            }
            QLabel {
                color: #f1f5f9;
                font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
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
                font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
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
            QPushButton:disabled {
                background-color: #1f2937;
                color: #64748b;
            }
            QTextEdit {
                background-color: #080c14;
                color: #94a3b8;
                border: 1px solid #1e293b;
                border-radius: 8px;
                font-family: 'Cascadia Mono', 'Cascadia Code', 'Consolas', monospace;
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
        main_layout.setContentsMargins(24, 22, 24, 22)
        main_layout.setSpacing(16)

        # Header Section
        header_layout = QHBoxLayout()
        header_text_box = QVBoxLayout()
        header_text_box.setSpacing(3)

        title = QLabel("Vassity PC Maintenance")
        title.setFont(QFont("Segoe UI", 17, QFont.Bold))
        subtitle = QLabel("Lightweight, zero-telemetry system cleaner and silent package updater.")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px;")
        
        header_text_box.addWidget(title)
        header_text_box.addWidget(subtitle)
        header_layout.addLayout(header_text_box)
        header_layout.addStretch()

        version_pill = QLabel("v1.0 • MIT Open Source")
        version_pill.setStyleSheet("""
            color: #38bdf8;
            background-color: #0c233c;
            border: 1px solid #0369a1;
            border-radius: 12px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        header_layout.addWidget(version_pill)
        main_layout.addLayout(header_layout)

        # Action Cards Layout
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)

        # Card 1: Safe Temp Purge
        card_clean = QFrame()
        card_clean.setProperty("class", "action-card")
        clean_vbox = QVBoxLayout(card_clean)
        clean_vbox.setSpacing(8)

        clean_title = QLabel("Safe Cache Purge")
        clean_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        
        clean_desc = QLabel("Sweeps %TEMP%, Windows Temp, Prefetch, and crash logs to free drive space.")
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

        # Card 2: Winget Package Updater
        card_update = QFrame()
        card_update.setProperty("class", "action-card")
        update_vbox = QVBoxLayout(card_update)
        update_vbox.setSpacing(8)

        update_title = QLabel("Software Updater")
        update_title.setFont(QFont("Segoe UI", 13, QFont.Bold))

        update_desc = QLabel("Bypasses Windows Update by checking installed desktop apps via native Winget.")
        update_desc.setWordWrap(True)
        update_desc.setStyleSheet("color: #94a3b8; font-size: 11px; line-height: 1.4;")

        update_assurance = QLabel("✓ Official Microsoft package manager automation")
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

        # Ultra-slim Hairline Progress Indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Stream Terminal Console
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setPlaceholderText("Ready. Select an action above to start...")
        main_layout.addWidget(self.console)

        # Signals
        self.signals = WorkerSignals()
        self.signals.log.connect(self.append_log)
        self.signals.queue_update.connect(self.on_queue_update)
        self.signals.status_text.connect(self.on_status_update)
        self.signals.progress_val.connect(self.on_progress_update)
        self.signals.finished.connect(self.on_finished)

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

    def start_clean(self):
        self.set_buttons_enabled(False)
        self.console.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        self.lbl_status.setText("● Purging system temporary caches...")
        self.append_log("[CLEAN] Scanning Windows temp paths...")
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
            self.signals.log.emit(f"  • Checking: {p}")
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
        self.signals.progress_val.emit(100)
        self.signals.log.emit(f"\n✓ Safely cleaned {total_files} junk files.")
        self.signals.log.emit(f"✓ Reclaimed {mb:.2f} MB of disk space.")
        self.signals.log.emit("✓ Browser profiles, logins, and passwords remained untouched.")
        self.signals.finished.emit()

    def start_update(self):
        self.set_buttons_enabled(False)
        self.console.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(5)
        self.lbl_status.setText("● Querying Microsoft Winget for package upgrades...")
        self.append_log("[WINGET] Scanning installed applications...")
        threading.Thread(target=self._run_update, daemon=True).start()

    def _run_update(self):
        try:
            check_cmd = ["winget", "upgrade", "--accept-source-agreements"]
            check_proc = subprocess.run(
                check_cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
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
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CleanerApp()
    window.show()
    sys.exit(app.exec())
