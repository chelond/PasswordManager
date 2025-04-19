import getpass
import json
import os
import secrets
import string
import logging
import yaml
from typing import Optional, Tuple, List

from rich.panel import Panel

from db import Database
from crypto import Crypto
from ui import UI
from config import GENERATED_PASSWORD_LENGTH, CONFIG_FILE, DEFAULT_CONFIG, LOG_FILE
from rich.progress import Progress

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PasswordManager:
    """Управляет операциями с паролями и координирует работу базы данных, шифрования и интерфейса."""

    def __init__(self):
        self.db = Database()
        self.crypto = Crypto()
        self.ui = UI()
        self.db.init_db()
        # Ensure config file exists
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w") as f:
                yaml.dump(DEFAULT_CONFIG, f)

    def generate_password(self, length: int = GENERATED_PASSWORD_LENGTH) -> str:
        """Генерирует случайный безопасный пароль."""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(chars) for _ in range(length))
        strength = self.ui.check_password_strength(password)
        self.ui.console.print(f"Сила сгенерированного пароля: {strength}")
        return password

    def change_master_password(self, old_key: bytes, salt: bytes) -> Tuple[bool, Optional[str]]:
        """Меняет мастер-пароль и перешифровывает все пароли."""
        new_password = self.ui.get_new_master_password()
        if not new_password:
            return False, None

        # Generate new key
        new_key = self.crypto.derive_key(new_password, salt)

        # Re-encrypt all passwords
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT service, username, encrypted_password, category FROM passwords")
            entries = cursor.fetchall()

            for service, username, encrypted_password, category in entries:
                try:
                    # Decrypt with old key
                    password = self.crypto.decrypt_password(encrypted_password, old_key)
                    # Encrypt with new key
                    new_encrypted_password = self.crypto.encrypt_password(password, new_key)
                    # Update database
                    cursor.execute(
                        "UPDATE passwords SET encrypted_password=? WHERE service=? AND (category=? OR category IS NULL)",
                        (new_encrypted_password, service, category)
                    )
                except Exception as e:
                    self.ui.display_error(f"Не удалось перешифровать {service}: {e}")
                    return False, None

            conn.commit()

        # Save new master password hash
        self.crypto.save_master_hash(new_password, salt)
        self.ui.display_success("🔄 [green]Мастер-пароль изменен![/green]")
        return True, new_password

    def get_services_and_metadata(self, category: str = None) -> Tuple[List[str], List[str], List[str]]:
        """Получает список сервисов, имен пользователей и категорий."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute(
                    "SELECT service, username, category FROM passwords WHERE category=?",
                    (category,)
                )
            else:
                cursor.execute("SELECT service, username, category FROM passwords")
            rows = cursor.fetchall()
            services = [row[0] for row in rows]
            usernames = [row[1] for row in rows]
            categories = [row[2] for row in rows]
            return services, usernames, categories

    def run(self):
        """Запускает основной цикл приложения."""
        self.ui.print_banner()
        self.ui.animated_loading("Инициализация системы безопасности...")

        salt = self.crypto.get_salt()
        max_attempts = 3
        attempts = 0

        while attempts < max_attempts:
            try:
                master_password = getpass.getpass(self.ui.messages["enter_master_password"])
                if not master_password.strip():
                    raise ValueError("Мастер-пароль не может быть пустым")

                # Verify master password
                if not self.crypto.verify_master_password(master_password, salt):
                    attempts += 1
                    remaining = max_attempts - attempts
                    self.ui.display_error(
                        f"{self.ui.messages['invalid_master_password']} Осталось попыток: {remaining}")
                    if remaining == 0:
                        self.ui.display_error("Слишком много неудачных попыток")
                        return
                    continue

                key = self.crypto.derive_key(master_password, salt)
                break
            except Exception as e:
                self.ui.display_error(str(e))
                return

        while True:
            action = self.ui.get_action()
            try:
                # Select category for relevant actions
                category = None
                if action in ["get_password", "edit_password", "delete_password"]:
                    categories = self.db.get_all_categories()
                    category = self.ui.select_category(categories)
                    if category == "Без категории":
                        category = None

                if action == "add_password":
                    data = self.ui.get_password_data()
                    if not data:
                        continue
                    encrypted_password = self.crypto.encrypt_password(data["password"], key)
                    category = data["category"] if data["category"] else None
                    if self.db.add_password(data["service"], data["username"], encrypted_password, category):
                        self.ui.display_success(self.ui.messages["saved_success"])
                    else:
                        self.ui.display_error(f"Сервис '{data['service']}' уже существует в категории")

                elif action == "get_password":
                    services, usernames, categories = self.get_services_and_metadata(category)
                    service = self.ui.select_service(services, usernames, categories)
                    if not service:
                        continue
                    while True:
                        sub_action = self.ui.service_menu(service)
                        if sub_action == "back":
                            break
                        elif sub_action == "view":
                            result = self.db.get_password(service, category)
                            if result:
                                try:
                                    password = self.crypto.decrypt_password(result["encrypted_password"], key)
                                    self.ui.display_password(service, result["username"], password, category)
                                except Exception as e:
                                    self.ui.display_error(f"Не удалось расшифровать: вероятно, неверный мастер-пароль")
                            else:
                                self.ui.display_error(self.ui.messages["not_found"])
                        elif sub_action == "edit":
                            data = self.ui.get_password_data()
                            if not data:
                                continue
                            encrypted_password = self.crypto.encrypt_password(data["password"], key)
                            if self.db.update_password(service, encrypted_password, category):
                                self.ui.display_success(self.ui.messages["saved_success"])
                            else:
                                self.ui.display_error(f"Сервис '{service}' не найден")
                        elif sub_action == "delete":
                            if self.ui.confirm_action(f"🗑️ Удалить {service}?"):
                                if self.db.delete_password(service, category):
                                    self.ui.display_success(f"🗑️ [green]{service} удален![/green]")
                                    break
                                else:
                                    self.ui.display_error(f"Сервис '{service}' не найден")

                elif action == "generate_password":
                    data = self.ui.get_password_data(generate=True)
                    if not data:
                        continue
                    password = self.generate_password()
                    encrypted_password = self.crypto.encrypt_password(password, key)
                    category = data["category"] if data["category"] else None
                    if self.db.add_password(data["service"], data["username"], encrypted_password, category):
                        self.ui.display_password(data["service"], data["username"], password, category)
                    else:
                        self.ui.display_error(f"Сервис '{data['service']}' уже существует в категории")

                elif action == "edit_password":
                    services, usernames, categories = self.get_services_and_metadata(category)
                    service = self.ui.select_service(services, usernames, categories)
                    if not service:
                        continue
                    data = self.ui.get_password_data()
                    if not data:
                        continue
                    encrypted_password = self.crypto.encrypt_password(data["password"], key)
                    if self.db.update_password(service, encrypted_password, category):
                        self.ui.display_success(self.ui.messages["saved_success"])
                    else:
                        self.ui.display_error(f"Сервис '{service}' не найден")

                elif action == "delete_password":
                    services, usernames, categories = self.get_services_and_metadata(category)
                    service = self.ui.select_service(services, usernames, categories)
                    if not service:
                        continue
                    if self.ui.confirm_action(f"🗑️ Удалить {service}?"):
                        if self.db.delete_password(service, category):
                            self.ui.display_success(f"🗑️ [green]{service} удален![/green]")
                        else:
                            self.ui.display_error(f"Сервис '{service}' не найден")

                elif action == "backup_data":
                    backup_file = self.db.backup_db()
                    self.ui.display_success(self.ui.messages["backup_success"].format(file=backup_file))

                elif action == "export_data":
                    export_file = self.db.export_data()
                    self.ui.display_success(self.ui.messages["export_success"].format(file=export_file))

                elif action == "import_data":
                    with open("export.json", "r") as f:
                        data = json.load(f)
                    with Progress() as progress:
                        task = progress.add_task("[cyan]Импорт данных...", total=len(data))
                        with self.db.connect() as conn:
                            cursor = conn.cursor()
                            for entry in data:
                                cursor.execute(
                                    "INSERT OR IGNORE INTO passwords (service, username, encrypted_password, category) VALUES (?, ?, ?, ?)",
                                    (entry["service"], entry["username"], entry["encrypted_password"],
                                     entry.get("category"))
                                )
                                progress.update(task, advance=1)
                            conn.commit()
                    self.ui.display_success(self.ui.messages["import_success"].format(file="export.json"))

                elif action == "info":
                    self.ui.console.print(Panel.fit(
                        "[bold cyan]Менеджер паролей v3.0[/bold cyan]\n\n"
                        "🔒 [bold green]Возможности:[/bold green]\n"
                        "- Шифрование AES-256-GCM\n"
                        "- Генератор безопасных паролей\n"
                        "- Полное управление базой данных\n"
                        "- Резервное копирование и экспорт/импорт\n"
                        "- Поддержка категорий\n\n"
                        "⚠️ [bold red]Опасные операции:[/bold red]\n"
                        "- Удаление всех данных\n"
                        "- Пересоздание базы данных",
                        title="ℹ️ Информация",
                        border_style="cyan"
                    ))

                elif action == "delete_all":
                    if self.ui.confirm_action(self.ui.messages["confirm_delete_all"]):
                        if self.db.delete_db():
                            self.ui.display_success("🔥 [red]Все данные удалены![/red]")
                        else:
                            self.ui.display_error("Не удалось удалить базу данных")

                elif action == "new_db":
                    if self.ui.confirm_action(self.ui.messages["confirm_new_db"]):
                        self.db.delete_db()
                        self.db.init_db()
                        self.ui.display_success("🆕 [green]Новая база данных создана![/green]")

                elif action == "change_master_password":
                    success, new_password = self.change_master_password(key, salt)
                    if success and new_password:
                        key = self.crypto.derive_key(new_password, salt)
                        logger.info("Мастер-пароль успешно изменен")
                        new_password = " " * len(new_password)  # Очистка памяти

                elif action == "exit":
                    self.ui.display_success(self.ui.messages["goodbye"])
                    break

            except Exception as e:
                self.ui.display_error(str(e))
                logger.error(f"Ошибка в действии {action}: {e}")

        self.db.close()


if __name__ == "__main__":
    manager = PasswordManager()
    manager.run()