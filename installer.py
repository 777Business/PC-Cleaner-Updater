"""
Vassity PC Maintenance — Official Windows Setup Installer
=========================================================
Installs Vassity PC Maintenance to LocalAppData, creates Desktop
and Start Menu shortcuts with official icons, registers in Windows
Installed Apps (Registry), and launches the application.
"""

import sys
import os
import shutil
import winreg
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QCheckBox, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QCursor, QIcon
import win32com.client

APP_NAME = "Vassity PC Maintenance"
APP_VERSION = "1.1.0"
APP_DIR_NAME = "VassityCleaner"
EXE_NAME = "VassityCleaner.exe"


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return Path(base_path) / relative_path


class InstallWorker(QThread):
    progress = Signal(int, str)
    finished = Signal(bool, str)

    def __init__(self, create_desktop, create_startmenu, launch_app):
        super().__init__()
        self.create_desktop = create_desktop
        self.create_startmenu = create_startmenu
        self.launch_app = launch_app

    def run(self):
        try:
            self.progress.emit(15, "Preparing installation directories...")
            install_dir = Path(os.environ.get("LOCALAPPDATA")) / "Programs" / APP_DIR_NAME
            install_dir.mkdir(parents=True, exist_ok=True)

            self.progress.emit(35, "Copying application binaries and assets...")
            src_exe = get_resource_path("VassityCleaner.exe")
            src_icon_ico = get_resource_path("icon.ico")
            src_icon_png = get_resource_path("icon.png")

            # Fallback for dev mode
            if not src_exe.exists():
                src_exe = Path(__file__).parent / "dist" / "VassityCleaner.exe"
            if not src_icon_ico.exists():
                src_icon_ico = Path(__file__).parent / "icon.ico"
            if not src_icon_png.exists():
                src_icon_png = Path(__file__).parent / "icon.png"

            dest_exe = install_dir / EXE_NAME
            dest_ico = install_dir / "icon.ico"
            dest_png = install_dir / "icon.png"

            shutil.copy2(src_exe, dest_exe)
            if src_icon_ico.exists():
                shutil.copy2(src_icon_ico, dest_ico)
            if src_icon_png.exists():
                shutil.copy2(src_icon_png, dest_png)

            self.progress.emit(65, "Creating system shortcuts...")
            shell = win32com.client.Dispatch("WScript.Shell")

            # Desktop Shortcut
            if self.create_desktop:
                desktop_dir = Path(os.environ.get("USERPROFILE")) / "Desktop"
                if desktop_dir.exists():
                    lnk = shell.CreateShortCut(str(desktop_dir / f"{APP_NAME}.lnk"))
                    lnk.TargetPath = str(dest_exe)
                    lnk.WorkingDirectory = str(install_dir)
                    if dest_ico.exists():
                        lnk.IconLocation = f"{dest_ico},0"
                    lnk.Description = "Safe PC cleaner & silent software updater"
                    lnk.save()

            # Start Menu Shortcut
            if self.create_startmenu:
                start_menu = Path(os.environ.get("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
                start_menu.mkdir(parents=True, exist_ok=True)
                lnk = shell.CreateShortCut(str(start_menu / f"{APP_NAME}.lnk"))
                lnk.TargetPath = str(dest_exe)
                lnk.WorkingDirectory = str(install_dir)
                if dest_ico.exists():
                    lnk.IconLocation = f"{dest_ico},0"
                lnk.Description = "Safe PC cleaner & silent software updater"
                lnk.save()

            self.progress.emit(85, "Registering in Windows Installed Apps...")
            # Create Uninstall batch script
            uninstall_bat = install_dir / "uninstall.bat"
            desktop_lnk_path = Path(os.environ.get("USERPROFILE")) / "Desktop" / f"{APP_NAME}.lnk"
            startmenu_lnk_path = Path(os.environ.get("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / f"{APP_NAME}.lnk"
            uninstall_script = f"""@echo off
timeout /t 1 /nobreak >nul
del /f /q "{desktop_lnk_path}" >nul 2>&1
del /f /q "{startmenu_lnk_path}" >nul 2>&1
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_DIR_NAME}" /f >nul 2>&1
taskkill /f /im {EXE_NAME} >nul 2>&1
cd "%TEMP%"
rmdir /s /q "{install_dir}" >nul 2>&1
echo Vassity PC Maintenance has been uninstalled.
del "%~f0"
"""
            with open(uninstall_bat, "w", encoding="utf-8") as f:
                f.write(uninstall_script)

            # Registry entry for Add/Remove Programs
            reg_key = f"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_DIR_NAME}"
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_key) as key:
                    winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
                    winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
                    winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Vassity Ecosystem")
                    winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(dest_ico) if dest_ico.exists() else str(dest_exe))
                    winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
                    winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'cmd.exe /c "{uninstall_bat}"')
                    winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
                    winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            except Exception:
                pass

            self.progress.emit(100, "Installation completed successfully!")

            if self.launch_app:
                os.startfile(str(dest_exe))

            self.finished.emit(True, "Installation complete!")
        except Exception as e:
            self.finished.emit(False, str(e))


class InstallerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vassity PC Maintenance Setup")
        self.setFixedSize(540, 420)

        icon_path = get_resource_path("icon.png")
        if not icon_path.exists():
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
            QFrame.card {
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 12px;
                padding: 18px;
            }
            QCheckBox {
                color: #cbd5e1;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #374151;
                background-color: #080c14;
            }
            QCheckBox::indicator:checked {
                background-color: #10b981;
                border-color: #10b981;
            }
            QPushButton.install-btn {
                background-color: #10b981;
                color: #042f2e;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-size: 14px;
                font-weight: 700;
                border-radius: 8px;
                padding: 12px 24px;
                border: none;
            }
            QPushButton.install-btn:hover {
                background-color: #34d399;
            }
            QPushButton.install-btn:pressed {
                background-color: #059669;
            }
            QPushButton.install-btn:disabled {
                background-color: #1f2937;
                color: #64748b;
            }
            QProgressBar {
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 6px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 5px;
            }
        """)

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.setSpacing(3)

        title = QLabel(f"Install {APP_NAME}")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        subtitle = QLabel(f"Version {APP_VERSION} • Open Source System Maintenance")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px;")

        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        header.addLayout(header_text)
        header.addStretch()

        pill = QLabel("v1.1.0")
        pill.setStyleSheet("""
            color: #34d399;
            background-color: #064e3b;
            border: 1px solid #059669;
            border-radius: 12px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 700;
        """)
        header.addWidget(pill)
        layout.addLayout(header)

        # Options Card
        card = QFrame()
        card.setProperty("class", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        info_title = QLabel("Installation Options")
        info_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        card_layout.addWidget(info_title)

        dest_info = QLabel(f"Install Path: %LOCALAPPDATA%\\Programs\\{APP_DIR_NAME}")
        dest_info.setStyleSheet("color: #64748b; font-size: 11px; font-family: monospace;")
        card_layout.addWidget(dest_info)

        card_layout.addSpacing(4)

        self.chk_desktop = QCheckBox("Add Shortcut to Desktop")
        self.chk_desktop.setChecked(True)
        self.chk_desktop.setCursor(QCursor(Qt.PointingHandCursor))
        card_layout.addWidget(self.chk_desktop)

        self.chk_startmenu = QCheckBox("Add Shortcut to Start Menu")
        self.chk_startmenu.setChecked(True)
        self.chk_startmenu.setCursor(QCursor(Qt.PointingHandCursor))
        card_layout.addWidget(self.chk_startmenu)

        self.chk_launch = QCheckBox("Launch Vassity PC Maintenance when finished")
        self.chk_launch.setChecked(True)
        self.chk_launch.setCursor(QCursor(Qt.PointingHandCursor))
        card_layout.addWidget(self.chk_launch)

        layout.addWidget(card)

        # Progress bar (Hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Ready to install.")
        self.lbl_status.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(self.lbl_status)

        # Bottom Actions
        actions = QHBoxLayout()
        actions.addStretch()

        self.btn_install = QPushButton("Install Now")
        self.btn_install.setProperty("class", "install-btn")
        self.btn_install.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_install.clicked.connect(self.start_install)
        actions.addWidget(self.btn_install)

        layout.addLayout(actions)

    def start_install(self):
        self.btn_install.setEnabled(False)
        self.chk_desktop.setEnabled(False)
        self.chk_startmenu.setEnabled(False)
        self.chk_launch.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(5)
        self.lbl_status.setText("Starting installation...")

        self.worker = InstallWorker(
            create_desktop=self.chk_desktop.isChecked(),
            create_startmenu=self.chk_startmenu.isChecked(),
            launch_app=self.chk_launch.isChecked()
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_progress(self, val, msg):
        self.progress_bar.setValue(val)
        self.lbl_status.setText(msg)

    def on_finished(self, success, msg):
        self.progress_bar.setValue(100)
        if success:
            self.lbl_status.setText("✓ Vassity PC Maintenance has been installed successfully!")
            self.lbl_status.setStyleSheet("color: #34d399; font-size: 12px; font-weight: bold;")
            self.btn_install.setText("Finished")
            self.btn_install.setEnabled(True)
            self.btn_install.clicked.disconnect()
            self.btn_install.clicked.connect(self.close)
        else:
            self.lbl_status.setText(f"❌ Error: {msg}")
            self.lbl_status.setStyleSheet("color: #f87171; font-size: 11px;")
            self.btn_install.setText("Close")
            self.btn_install.setEnabled(True)
            self.btn_install.clicked.disconnect()
            self.btn_install.clicked.connect(self.close)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = InstallerWindow()
    win.show()
    sys.exit(app.exec())
