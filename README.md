# Discord Server Cloner
![Github All Releases](https://img.shields.io/github/downloads/seregonwar/DiscordServerCloner/total.svg)

An application that allows you to easily clone a Discord server, including roles, categories, text channels, voice channels, and messages.

---

## Preview
![video preview](https://github.com/user-attachments/assets/6e558e11-bd05-4ab6-83d6-2c1d2b61e9f2)
---
Thanks to @Aadiwrth for the preview.

---

## ⚠️ IMPORTANT: Anti-Virus / False Positives

> **PLEASE READ BEFORE DOWNLOADING**

If your antivirus (Windows Defender, Chrome, etc.) flags this application as malicious/virus, **it is a False Positive**.

This usually happens because the application is compiled using **PyInstaller**. Antivirus software often flags software created with PyInstaller that hasn't been digitally signed (which costs money) as a potential threat.

**🚫 PLEASE DO NOT OPEN GITHUB ISSUES REGARDING VIRUS DETECTIONS.**

These issues will be closed immediately. If you do not trust the pre-compiled executable, please follow **"Option 2: From source code"** below to run the clean Python code yourself.

---

## Features

- **Intuitive graphical interface**: Easy to use thanks to the modern user interface  
- **Selective cloning**: Select exactly what you want to clone
  - Roles
  - Categories
  - Text channels
  - Voice channels
  - Messages (with customizable limit)  
- **Multilingual**: Support for IT, EN, ES, FR, NP
- **Customizable**: Light and dark themes  

---

## Prerequisites

- Python 3.8 or higher  
- Internet connection to download dependencies  
- Valid Discord token with appropriate permissions  

---

## Installation

### Option 1: Pre-compiled executable
1. Download the latest version from the [Releases](https://github.com/seregonwar/DiscordServerCloner/releases) section  
2. Extract the ZIP file  
3. Run `Discord Server Cloner.exe`  
   *(If Windows SmartScreen prevents the startup, click on "More info" -> "Run anyway")*

### Option 2: From source code
1. Clone the repository:
   ```bash
   git clone [https://github.com/seregonwar/DiscordServerCloner.git](https://github.com/seregonwar/DiscordServerCloner.git)
   cd DiscordServerCloner


2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:

   ```bash
   python main.py
   ```

---

## How to use

1. Start the application
2. Enter your Discord token and click on “verify”
3. Search the list for the server you want to clone (based on the server ID, not just the name).
4. Enter the destination server ID (must be an empty server)
5. Select the elements you want to clone (roles, channels, etc.)
6. Click on **Start Cloning**
7. Wait for the process to complete
8. For security reasons, be sure to log out once you have completed the cloning process in order to invalidate your token and render it unusable! Anyone who comes into possession of your still-valid token could have full access to it, and you would never know!

---

## Building the executable

To create a standalone executable:

1. Make sure you have PyInstaller installed:

   ```bash
   pip install pyinstaller
   ```
2. Run the build script:

   ```bash
   python build.py
   ```
3. The executable file will be created in the `dist` folder and a ZIP archive containing the distribution will be created in the main directory.

---

## Troubleshooting

* **Authentication error**: Verify that the Discord token is valid and has the necessary permissions
* **Cloning error**: Make sure the source and destination servers exist and that you have the necessary permissions for both
* **"Same server" error**: The source and destination server IDs cannot be the same

---

## GUI

![Main interface](https://github.com/user-attachments/assets/82ab4bda-9501-4dd5-824b-133571bb2be0)
![Settings panel](https://github.com/user-attachments/assets/3f3ab413-d641-4d9b-a9c4-78696a229752)
![Server Searchbar](https://github.com/user-attachments/assets/dafe5bb0-a599-44af-9e27-87fd2178ef4e)
---

## Contributing

Contributions, bug reports, and feature requests are welcome! Feel free to open an issue or a pull request.

---

## License

This project is licensed under the Apache-2.0 license - see the [LICENSE](LICENSE) file for details.

---

## Disclaimer

This tool is provided for **educational purposes only**. The authors are not responsible for any misuse of the software.
