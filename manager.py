import os
import getpass
import secrets
import string
import pyperclip
from rich.console import Console
from rich.table import Table
from crypto import derive_key, clear_password
from db import init_db, add_password, get_password, backup_db, export_data, import_data, get_all_services, get_users_by_service

SALT_FILE = os.path.join(os.path.expanduser("~"), ".passman_salt.bin")
console = Console()

def get_salt():
    if not os.path.exists(SALT_FILE):
        salt = os.urandom(16)
        with open(SALT_FILE, "wb") as f:
            f.write(salt)
    else:
        with open(SALT_FILE, "rb") as f:
            salt = f.read()
    return salt

def get_key():
    master_password = getpass.getpass("Введите мастер-пароль: ")
    return derive_key(master_password, get_salt())

def generate_password(length=16):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(chars) for _ in range(length))

def print_info():
    info_text = """
    [cyan]Password Manager[/cyan] - консольный менеджер паролей.

    Версия: 1.0  
    Автор: Пользователь Arch Linux  
    Описание:  
    - Безопасное хранение паролей с шифрованием AES-256-GCM  
    - Генерация паролей  
    - Бэкапы базы данных  
    - Импорт/экспорт в JSON  
    - Копирование пароля в буфер обмена  
    """
    console.print(info_text, style="bold")

def print_menu():
    console.print("\n[bold yellow]Меню:[/bold yellow]")
    console.print("1. Добавить пароль")
    console.print("2. Получить пароль")
    console.print("3. Сгенерировать и сохранить пароль")
    console.print("4. Бэкап базы данных")
    console.print("5. Экспорт данных")
    console.print("6. Импорт данных")
    console.print("7. Информация об утилите")
    console.print("0. Выход")

def interactive_manager(print_inf=None):
    init_db()
    key = get_key()

    while True:
        print_menu()
        choice = input("Выберите пункт: ").strip()

        if choice == "1":
            service = input("Сервис: ").strip()
            username = input("Имя пользователя: ").strip()
            password = getpass.getpass("Пароль: ")
            add_password(service, username, password, key)
            clear_password(password)
            console.print("[green]Пароль сохранён.[/green]")

        elif choice == "2":
            services = get_all_services()
            if not services:
                console.print("[red]Нет сохранённых сервисов.[/red]")
                continue

            console.print("\n[bold yellow]Выберите сервис:[/bold yellow]")
            for i, service in enumerate(services, 1):
                console.print(f"{i}. {service}")

            try:
                index = int(input("Введите номер сервиса: ")) - 1
                service = services[index]
            except (ValueError, IndexError):
                console.print("[red]Неверный выбор сервиса.[/red]")
                continue

            users = get_users_by_service(service)
            if not users:
                console.print("[red]Нет пользователей для выбранного сервиса.[/red]")
                continue

            console.print(f"\n[bold cyan]Пользователи в {service}:[/bold cyan]")
            for i, user in enumerate(users, 1):
                console.print(f"{i}. {user}")

            try:
                user_index = int(input("Введите номер пользователя: ")) - 1
                username = users[user_index]
            except (ValueError, IndexError):
                console.print("[red]Неверный выбор пользователя.[/red]")
                continue

            password = get_password(service, username, key)
            if password:
                pyperclip.copy(password.decode())
                clear_password(password)
                console.print("[green]Пароль скопирован в буфер обмена.[/green]")
            else:
                console.print("[red]Пароль не найден.[/red]")

        elif choice == "3":
            service = input("Сервис: ").strip()
            username = input("Имя пользователя: ").strip()
            password = generate_password()
            add_password(service, username, password, key)
            pyperclip.copy(password)
            clear_password(password)
            console.print(f"[green]Сгенерирован и сохранён. Скопировано в буфер обмена:[/green] {password}")

        elif choice == "4":
            backup_db()

        elif choice == "5":
            export_data()

        elif choice == "6":
            import_data()

        elif choice == "7":
            print_inf

        elif choice == "0":
            console.print("[bold]Выход.[/bold]")
            break

        else:
            console.print("[red]Неверный выбор. Попробуйте снова.[/red]")

if __name__ == "__main__":
    interactive_manager()