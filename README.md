# PassMan - Password Manager

PassMan is a secure, console-based password manager for Linux, designed for efficient and reliable management of credentials. It enables storing, generating, editing, and organizing passwords into categories, using modern encryption and a fully localized Russian interface. Distributed as a portable AppImage.

## Features

- Secure password storage with encryption (`cryptography`) and master password hashing (`argon2-cffi`).
- Generation of strong, random passwords.
- Organization of passwords into categories.
- Search with autocompletion for quick access to credentials.
- Editing and deletion of records.
- Creation of encrypted database backups.
- Export and import of data in JSON format.
- Localized Russian console interface with colored tables and panels (`rich`).
- Support for light and dark UI themes.
- Automatic copying of passwords to the clipboard.
- Compatibility with most Linux distributions via AppImage.

## Requirements

- Operating System: Linux (Ubuntu, Fedora, Arch Linux, etc.).
- Disk Space: ~50–100 MB for the AppImage and configuration files.
- Permissions: Write access to `~/.passman_*` for storing the database, configuration, and logs.

## Installation and Usage

### Using the AppImage

1. Download `PassMan.AppImage` from [Releases](https://github.com/your-repo/releases).
2. Make the file executable:
   ```bash
   chmod +x PassMan.AppImage
   ```
3. Run the application:
   ```bash
   ./PassMan.AppImage
   ```
4. On first launch, enter a master password to create an encrypted database.

### Running from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/passman.git
   cd passman
   ```
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   Contents of `requirements.txt`:
   ```text
   rich
   questionary
   pyyaml
   pyperclip
   argon2-cffi
   cryptography
   ```
4. Run the application:
   ```bash
   python manager.py
   ```

## Usage

PassMan provides a console menu with the following actions:

- Add Password: Save credentials for a service.
- Get Password: View and copy an existing password.
- Generate Password: Create a random, strong password.
- Edit Password: Modify service credentials.
- Delete Password: Remove a record.
- Create Backup: Save an encrypted database backup.
- Export/Import Data: Work with JSON data.
- Change Master Password: Update the master password.
- Delete All Data: Clear the database (use with caution).
- New Database: Recreate the database.
- Exit: Close the application.

### Hotkeys
- `1`–`9`, `0`: Select an action.
- `c`: Change master password.
- `n`: Create a new database.
- `q`: Exit.

### Files
- `~/.passman_config.yaml`: Configuration (language, theme).
- `~/.passman.db`: Encrypted database.
- `~/.passman_salt.bin`: Salt for hashing.
- `~/.passman_master.hash`: Master password hash.
- `~/.passman.log`: Application logs.

## Security

- All passwords are encrypted using `cryptography`.
- Master password is hashed with `argon2-cffi`.
- Data is stored locally in `~/.passman_*`.
- Encrypted backups are protected by the master password.

**Recommendations**:
- Use a strong master password (at least 12 characters, including letters, numbers, and special characters).
- Regularly back up `~/.passman.db`.
- Store backups on an external drive.

## Troubleshooting

If the application fails to start:

1. Check the logs:
   ```bash
   cat ~/.passman.log
   ```
2. Verify permissions:
   ```bash
   chmod -R u+rw ~/.passman_*
   ```
3. Report issues at [Issues](https://github.com/your-repo/issues) with a description and log contents.

## Contributing

1. Fork the repository.
2. Create a branch: `git checkout -b feature/your-feature`.
3. Commit changes: `git commit -m "Add your feature"`.
4. Push to the repository: `git push origin feature/your-feature`.
5. Create a Pull Request.

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

## Contact

- GitHub: [your-repo](https://github.com/your-repo)
- Issues: [github.com/your-repo/issues](https://github.com/your-repo/issues)