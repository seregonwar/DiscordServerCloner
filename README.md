# Discord Server Manager
![Github All Releases](https://img.shields.io/github/downloads/seregonwar/DiscordServerManager/total.svg)
![Version](https://img.shields.io/badge/version-3.0.0-blue)
![License](https://img.shields.io/badge/license-Apache--2.0-green)

A fork of [DiscordServerCloner](https://github.com/seregonwar/DiscordServerCloner)  and a comprehensive, high-performance Python-based suite for Discord server management, cloning, and structural backups. Built with **Flet (Material 3)** and powered by Discord's REST API, this tool offers a modular approach to server replication and restoration.

---

## 🚀 Key Modules

*   **Cloning Engine:** High-fidelity live server replication, including roles, categories, channels, and messages.
*   **Snapshot Engine:** Capture entire server structures into local JSON "snapshots" for offline storage.
*   **Restore Engine:** Deploy local snapshots or community templates back to live servers in seconds.
*   **Analytics Dashboard:** Visualize your management history with advanced charts and summary metrics.
*   **Template Marketplace:** Explore, preview, and apply curated community templates.

---

## ✨ Features

*   **Modern UI/UX:** Sleek Material 3 interface with dynamic theming and responsive layouts.
*   **Selective Cloning:** Choose exactly what to replicate—roles, permissions, categories, text/voice channels, or message history.
*   **Structure Explorer:** Preview a template's channel tree and role hierarchy *before* applying changes.
*   **Message Engine V2:** Robust handling of embeds, attachments, and complex message structures with rate-limit awareness.
*   **Multi-lingual Support:** Native support for English (US), Spanish (ES), French (FR), Italian (IT), and Nepali (NP).
*   **Update Checker:** Automatic notification for new releases directly within the application.

---

## 🖼️ Preview

[![Watch the tutorial](https://img.youtube.com/vi/Cq0BEA91mSY/maxresdefault.jpg)](https://youtu.be/Cq0BEA91mSY)

*Click the image above to watch the full video tutorial.*


---

## ⚠️ Critical: Anti-Virus / False Positives

> **PLEASE READ BEFORE DOWNLOADING**

If your antivirus flags this application (e.g., Windows Defender), it is a **False Positive**. This occurs because the application is compiled using **PyInstaller** and is not digitally signed.

**🚫 PLEASE DO NOT OPEN GITHUB ISSUES REGARDING VIRUS DETECTIONS.**
If you do not trust the binary, please follow the **"Run from Source"** instructions below.

---

## 🛠️ Installation

### Option 1: Executable (Recommended)
1. Download the latest version from [Releases](https://github.com/seregonwar/DiscordServerManager/releases).
2. Extract the archive and run `Discord Server Manager.exe`.
   *(If Windows SmartScreen appears, click "More info" -> "Run anyway")*

### Option 2: Run from Source
1. **Clone the Repo:**
   ```bash
   git clone https://github.com/seregonwar/DiscordServerManager.git
   cd DiscordServerManager
   ```
2. **Setup Environment:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Execute:**
   ```bash
   python main.py
   ```

---

## 📖 How to Use

1.  **Authentication:** Enter your Discord token and click **Verify**.
2.  **Dashboard:** Monitor your recent activity and global stats.
3.  **Operation:**
    *   **Clone:** Select a source server and a destination (target server must be empty).
    *   **Snapshot:** Save a server's structure to a local file.
    *   **Restore:** Load a previous snapshot or browse the **Community Marketplace** for templates.
4.  **Validation:** Use the **Explorer** to verify the structure before finalizing any operation.
5.  **Security:** Log out once finished to clear session data.

---

## 🔒 Security & Privacy

*   **No Token Persistence:** Your Discord token is never logged or stored outside the active session.
*   **Rate-Limit Handling:** Built-in exponential backoff to prevent account flagging and 429 errors.
*   **Open Source:** Auditable code for full transparency.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.
1.  Fork the project.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

---

## 📜 License & Disclaimer

Distributed under the **Apache-2.0 License**. See `LICENSE` for more information.

**Disclaimer:** This tool is for **educational purposes only**. The authors are not responsible for any misuse of this software or violations of Discord's Terms of Service.
