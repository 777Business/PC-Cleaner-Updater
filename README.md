# ⚡ Vassity PC Cleaner & Updater

> A lightweight, open-source Windows maintenance utility built with Python & PySide6. Clean system caches safely and update all installed applications with zero browser tampering.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg)](https://microsoft.com)
[![Open Source](https://img.shields.io/badge/Open%20Source-100%25-brightgreen.svg)]()

---

## 💡 Why Vassity Cleaner?

Most third-party PC cleaners are bloated, show intrusive ads, or dangerously wipe browser databases—deleting your saved autofill logins, cookies, and pinned sessions.

**Vassity PC Cleaner is built on two core principles:**
1. **Safety First**: Only purges true operating system temp dumps (`%TEMP%`, `C:\Windows\Temp`, `Prefetch`, crash logs). It **never touches** browser profiles, autofill, passwords, or personal documents.
2. **Real Updates**: Windows Update often fails to update your daily desktop software (Discord, Spotify, VS Code, Git, Chrome, etc.). Vassity Cleaner taps into Microsoft's official Windows Package Manager (`winget`) to update all installed apps silently in a clean, discreet queue.

---

## ✨ Features

- 🧹 **Safe Temporary Cleaner**:
  - Sweeps user temporary caches (`%TEMP%`, `%TMP%`).
  - Cleans Windows system temporary files (`C:\Windows\Temp`).
  - Cleans Windows Prefetch cache and application crash dumps.
  - Zero browser history or password deletion.
- 🚀 **Automated Software Updater**:
  - Leverages native Microsoft Windows Package Manager (`winget`).
  - Scans installed software and queues upgrades automatically.
  - Discreet queue badge (`Queue: 1/4`) and micro progress tracker.
  - Runs silent, automated package installations.
- 🎨 **Modern Dark UI**:
  - Built with PySide6 (Qt) in a responsive, clean dark aesthetic.
  - Real-time live log console.

---

## 🚀 Quick Start (Pre-built Executable)

1. Download the latest **`VassityCleaner.exe`** from [Releases](https://github.com/777Business/PC-Cleaner-Updater/releases).
2. Double-click to launch (no Python installation or command line required).
3. Click **Clean PC Temp Junk** or **Update All Software**.

---

## 🛠️ Running from Source

If you prefer running from Python source or contributing:

```bash
# Clone the repository
git clone https://github.com/777Business/PC-Cleaner-Updater.git
cd PC-Cleaner-Updater

# Install requirements
pip install PySide6

# Run the app
python app.py
```

### Building the Executable Yourself

```bash
pip install pyinstaller
python -m PyInstaller --noconsole --onefile --windowed --name="VassityCleaner" app.py
```
The compiled binary will be placed inside the `dist/` folder.

---

## 🔒 Privacy & Safety Guarantee

- **No Telemetry**: No background telemetry, tracking, or network calls to external servers.
- **No Registry Tweaks**: Does not modify Windows registry or delete critical system binaries.
- **Open Source**: 100% transparent codebase under the MIT License.

---

## 📄 License

Distributed under the [MIT License](LICENSE). Copyright (c) 2026 Vassity.
