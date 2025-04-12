import os
import getpass
import secrets
import string
import pyperclip
import time
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich import box
from questionary import select, prompt, Style
from crypto import derive_key, clear_password
from db import (
    init_db, add_password, get_password, backup_db,
    export_data, import_data, get_all_services,
    update_password, delete_password
)

SALT_FILE = os.path.join(os.path.expanduser("~"), ".passman_salt.bin")
console = Console()

# Кастомный стиль для questionary
custom_style = Style([
    ('qmark', 'fg:#00ffff bold'),
    ('selected', 'fg:#00ff00 bold'),
    ('pointer', 'fg:#ff00ff bold'),
    ('highlighted', 'fg:#ffff00 bold'),
])


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
    master_password = getpass.getpass("🔑 Введите мастер-пароль: ")
    return derive_key(master_password, get_salt())


def generate_password(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))


def check_password_strength(password):
    if len(password) < 8:
        return "слабый"
    elif not (any(c.isupper() for c in password) and any(c.isdigit() for c in password)):
        return "средний"
    return "сильный"


def print_banner():
    banner = """
    ██████╗  █████╗ ███████╗███████╗███╗   ███╗ █████╗ ███╗   ██╗
    ██╔══██╗██╔══██╗██╔════╝██╔════╝████╗ ████║██╔══██╗████╗  ██║
    ██████╔╝███████║███████╗███████╗██╔████╔██║███████║██╔██╗ ██║
    ██╔═══╝ ██╔══██║╚════██║╚════██║██║╚██╔╝██║██╔══██║██║╚██╗██║
    ██║     ██║  ██║███████║███████║██║ ╚═╝ ██║██║  ██║██║ ╚████║
    ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
    """
    console.print(Panel.fit(
        f"[bold cyan]{banner}[/bold cyan]",
        border_style="bright_yellow",
        padding=(1, 4),
        subtitle="[blink]v2.2[/blink] [white]Secure Password Management[/white]"
    ))


def animated_loading(text="Загрузка..."):
    with Progress(transient=True) as progress:
        task = progress.add_task(f"[cyan]{text}", total=10)
        while not progress.finished:
            progress.update(task, advance=0.5)
            time.sleep(0.04)


def print_info():
    info_text = """
    [bold cyan]Password Manager v2.2[/bold cyan]
    🔒 Безопасное хранение паролей с военным уровнем шифрования

    [bold yellow]Основные возможности:[/bold yellow]
    • Навигация стрелками
    • AES-256-GCM шифрование
    • Интерактивные формы ввода
    • Генератор сложных паролей
    • Автоматическое копирование в буфер

    [bold green]Управление:[/bold green]
    ↑/↓ - Выбор пункта
    Enter - Подтвердить
    Ctrl+C - Выход
    """
    console.print(Panel.fit(info_text, title="ℹ️ Информация", border_style="cyan"))


def main_menu():
    return select(
        message="Выберите действие:",
        choices=[
            {"name": "🗝  Добавить пароль", "value": "1"},
            {"name": "🔍  Получить пароль", "value": "2"},
            {"name": "🎲  Сгенерировать пароль", "value": "3"},
            {"name": "✏️  Редактировать запись", "value": "4"},
            {"name": "🗑️  Удалить запись", "value": "5"},
            {"name": "💾 Бэкап данных", "value": "6"},
            {"name": "📤 Экспорт данных", "value": "7"},
            {"name": "📥 Импорт данных", "value": "8"},
            {"name": "ℹ️  Информация", "value": "9"},
            {"name": "🚪 Выход", "value": "0"}
        ],
        qmark="➤",
        style=custom_style,
        use_arrow_keys=True
    )


def interactive_manager():
    print_banner()
    animated_loading("Инициализация системы...")
    init_db()
    key = get_key()

    while True:
        action = main_menu().ask()

        if action == "1":
            answers = prompt([
                {
                    'type': 'text',
                    'name': 'service',
                    'message': '🌐 Введите название сервиса:',
                    'qmark': '➤',
                    'style': custom_style
                },
                {
                    'type': 'text',
                    'name': 'username',
                    'message': '👤 Введите имя пользователя:',
                    'qmark': '➤',
                    'style': custom_style
                },
                {
                    'type': 'password',
                    'name': 'password',
                    'message': '🔒 Введите пароль:',
                    'qmark': '➤',
                    'style': custom_style
                }
            ], style=custom_style)

            strength = check_password_strength(answers['password'])
            console.print(
                f"🛡️ Уровень защиты: [bold {'red' if strength == 'слабый' else 'yellow' if strength == 'средний' else 'green'}]{strength.upper()}[/]")

            with console.status("[bold green]Шифрование данных...[/]", spinner="bouncingBall"):
                add_password(answers['service'], answers['username'], answers['password'], key)
                clear_password(answers['password'])
                time.sleep(1)
            console.print(Panel.fit("✅ [bold green]Запись успешно сохранена![/]", border_style="green"))

        elif action == "2":
            services = get_all_services()
            if not services:
                console.print(Panel("[red]⚠️ Нет сохранённых сервисов[/red]", border_style="red"))
                continue

            selected_service = select(
                message="📋 Выберите сервис:",
                choices=services,
                style=custom_style,
                use_arrow_keys=True,
                qmark="➤"
            ).ask()

            with console.status("[cyan]Поиск записи...[/]", spinner="dots"):
                result = get_password(selected_service, key)
                time.sleep(0.5)

            if result:
                pyperclip.copy(result['password'].decode())
                console.print(
                    Panel.fit(
                        f"🔑 [bold green]{selected_service}[/]\n"
                        f"👤 Логин: [yellow]{result['username']}[/]\n"
                        f"📋 Пароль скопирован в буфер!",
                        border_style="green"
                    )
                )
                clear_password(result['password'])
            else:
                console.print(Panel("[red]⚠️ Запись не найдена[/red]", border_style="red"))

        elif action == "3":
            answers = prompt([
                {
                    'type': 'text',
                    'name': 'service',
                    'message': '🌐 Введите название сервиса:',
                    'qmark': '➤',
                    'style': custom_style
                },
                {
                    'type': 'text',
                    'name': 'username',
                    'message': '👤 Введите имя пользователя:',
                    'qmark': '➤',
                    'style': custom_style
                }
            ], style=custom_style)

            password = generate_password()
            with console.status("[yellow]Генерация пароля...[/]", spinner="dots12"):
                add_password(answers['service'], answers['username'], password, key)
                pyperclip.copy(password)
                time.sleep(1)

            console.print(
                Panel.fit(
                    f"🔢 [bold]{password}[/]\n"
                    f"📋 Пароль скопирован в буфер!",
                    title="🎉 Новый пароль",
                    border_style="yellow"
                )
            )
            clear_password(password)

        elif action == "4":
            service = select(
                message="🌐 Выберите сервис для редактирования:",
                choices=get_all_services(),
                style=custom_style,
                use_arrow_keys=True,
                qmark="➤"
            ).ask()

            new_password = prompt([{
                'type': 'password',
                'name': 'password',
                'message': '🔒 Введите новый пароль:',
                'qmark': '➤',
                'style': custom_style
            }], style=custom_style)['password']

            with console.status("[blue]Обновление записи...[/]", spinner="toggle"):
                update_password(service, new_password, key)
                time.sleep(1)
            console.print(Panel.fit("✅ [bold green]Пароль успешно обновлён[/]", border_style="green"))
            clear_password(new_password)

        elif action == "5":
            service = select(
                message="🌐 Выберите сервис для удаления:",
                choices=get_all_services(),
                style=custom_style,
                use_arrow_keys=True,
                qmark="➤"
            ).ask()

            with console.status("[red]Удаление...[/]", spinner="bouncingBar"):
                delete_password(service)
                time.sleep(0.7)
            console.print(Panel.fit("🗑️ [bold red]Запись удалена[/]", border_style="red"))

        elif action == "6":
            with console.status("[magenta]Создание бэкапа...[/]", spinner="moon"):
                backup_db()
                time.sleep(1)
            console.print(Panel.fit("💾 [bold green]Бэкап успешно создан[/]", border_style="green"))

        elif action == "7":
            export_data()
            console.print(Panel.fit("📤 [bold green]Данные экспортированы в export.json[/]", border_style="green"))

        elif action == "8":
            import_data()
            console.print(Panel.fit("📥 [bold green]Данные успешно импортированы[/]", border_style="green"))

        elif action == "9":
            print_info()

        elif action == "0":
            console.print(Panel.fit("[bold magenta]👋 До новых встреч![/]", border_style="magenta"))
            break


if __name__ == "__main__":
    interactive_manager()