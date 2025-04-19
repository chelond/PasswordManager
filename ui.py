import time
import yaml
import os
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table
from questionary import select, prompt, Style, autocomplete
import pyperclip
from config import CONFIG_FILE, DEFAULT_CONFIG


class UI:
    """Управляет пользовательским интерфейсом менеджера паролей с использованием rich и questionary."""

    def __init__(self):
        self.console = Console()
        # Load configuration
        self.config = DEFAULT_CONFIG
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                self.config.update(yaml.safe_load(f) or {})
        self.messages = {
            "ru": {
                "enter_master_password": "🔑 Введите мастер-пароль: ",
                "password_copied": "📋 [green]Пароль скопирован![/green]",
                "saved_success": "✅ [green]Сохранено![/green]",
                "error": "[red]Ошибка: {error}[/red]",
                "no_data": "[red]⚠️ Данные отсутствуют[/red]",
                "not_found": "[red]⚠️ Запись не найдена[/red]",
                "confirm_delete_all": "❌ [red]УДАЛИТЬ ВСЕ ДАННЫЕ?[/red]",
                "confirm_new_db": "♻️ Создать новую базу данных?",
                "backup_success": "💾 [green]Резервная копия создана: {file}[/green]",
                "export_success": "📤 [green]Данные экспортированы в {file}[/green]",
                "import_success": "📥 [green]Данные импортированы из {file}[/green]",
                "goodbye": "[magenta]👋 До свидания![/magenta]",
                "invalid_master_password": "[red]Неверный мастер-пароль![/red]",
                "change_master_password": "🔄 Сменить мастер-пароль",
                "new_master_password": "🔑 Введите новый мастер-пароль: ",
                "confirm_master_password": "🔑 Подтвердите новый мастер-пароль: ",
                "password_mismatch": "[red]Пароли не совпадают![/red]",
                "select_category": "📁 Выберите категорию (или оставьте пустым): ",
                "category_prompt": "📁 Введите категорию (или оставьте пустым): "
            }
        }[self.config["ui"]["language"]]
        self.set_theme(self.config["ui"]["theme"])

    def set_theme(self, theme: str):
        """Sets the color theme for the UI."""
        themes = {
            "default": Style([
                ('qmark', 'fg:#00ffff bold'),
                ('selected', 'fg:#00ff00 bold'),
                ('pointer', 'fg:#ff00ff bold'),
                ('highlighted', 'fg:#ffff00 bold'),
            ]),
            "dark": Style([
                ('qmark', 'fg:#ffffff bold'),
                ('selected', 'fg:#00aa00 bold'),
                ('pointer', 'fg:#aa00aa bold'),
                ('highlighted', 'fg:#aaaaaa bold'),
            ])
        }
        self.style = themes.get(theme, themes["default"])

    def print_banner(self):
        """Отображает баннер приложения."""
        banner = """
        ███╗   ███╗███████╗███╗   ██╗███████╗██████╗     ██████╗  █████╗ ██████╗  ██████╗ ██╗     ███████╗██╗   ██╗
        ████╗ ████║██╔════╝████╗  ██║██╔════╝██╔══██╗    ██╔══██╗██╔══██╗██╔══██╗██╔═══██╗██║     ██╔════╝╚██╗ ██╔╝
        ██╔████╔██║█████╗  ██╔██╗ ██║█████╗  ██████╔╝    ██████╔╝███████║██████╔╝██║   ██║██║     █████╗   ╚████╔╝ 
        ██║╚██╔╝██║██╔══╝  ██║╚██╗██║██╔══╝  ██╔═══╝     ██╔═══╝ ██╔══██║██╔═══╝ ██║   ██║██║     ██╔══╝    ╚██╔╝  
        ██║ ╚═╝ ██║███████╗██║ ╚████║███████╗██║         ██║     ██║  ██║██║     ╚██████╔╝███████╗███████╗   ██║   
        ╚═╝     ╚═╝╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝         ╚═╝     ╚═╝  ╚═╝╚═╝      ╚═════╝ ╚══════╝╚══════╝   ╚═╝   
        """
        self.console.print(Panel.fit(
            f"[bold cyan]{banner}[/bold cyan]",
            border_style="bright_yellow",
            padding=(1, 4),
            subtitle="[blink]v3.0[/blink] [white]Ультимативный Менеджер Паролей[/white]"
        ))

    def animated_loading(self, text: str = "Загрузка...", enabled: bool = True):
        """Отображает анимированную полосу загрузки."""
        if not enabled:
            return
        with Progress(transient=True) as progress:
            task = progress.add_task(f"[cyan]{text}", total=10)
            while not progress.finished:
                progress.update(task, advance=0.5)
                time.sleep(0.04)

    def get_action(self) -> str:
        """Запрашивает у пользователя выбор действия из главного меню."""
        return select(
            message="[bold]Выберите действие (введите ? для справки):[/bold]",
            choices=[
                {"name": "🗝  Добавить пароль (сохранить новый пароль) [1]", "value": "add_password", "key": "1"},
                {"name": "🔍  Получить пароль (просмотреть существующий пароль) [2]", "value": "get_password",
                 "key": "2"},
                {"name": "🎲  Сгенерировать пароль (создать новый случайный пароль) [3]", "value": "generate_password",
                 "key": "3"},
                {"name": "✏️  Редактировать пароль (изменить существующий пароль) [4]", "value": "edit_password",
                 "key": "4"},
                {"name": "🗑️  Удалить пароль (удалить данные сервиса) [5]", "value": "delete_password", "key": "5"},
                {"name": "💾 Создать резервную копию (сохранить базу данных) [6]", "value": "backup_data", "key": "6"},
                {"name": "📤 Экспортировать данные (сохранить в JSON) [7]", "value": "export_data", "key": "7"},
                {"name": "📥 Импортировать данные (загрузить из JSON) [8]", "value": "import_data", "key": "8"},
                {"name": "ℹ️  Информация (показать справку) [9]", "value": "info", "key": "9"},
                {"name": "🔥 Удалить все данные (очистить базу) [0]", "value": "delete_all", "key": "0"},
                {"name": "♻️ Новая база данных (пересоздать базу) [n]", "value": "new_db", "key": "n"},
                {"name": f"{self.messages['change_master_password']} [c]", "value": "change_master_password",
                 "key": "c"},
                {"name": "🚪 Выход (закрыть приложение) [q]", "value": "exit", "key": "q"}
            ],
            style=self.style,
            qmark="➤",
            use_shortcuts=True
        ).ask()

    def get_password_data(self, generate: bool = False) -> Optional[dict]:
        """Запрашивает данные пароля (сервис, имя пользователя, пароль, категория)."""
        questions = [
            {
                'type': 'text',
                'name': 'service',
                'message': '🌐 Название сервиса:',
                'validate': lambda x: len(x.strip()) > 0 or "Сервис не может быть пустым"
            },
            {
                'type': 'text',
                'name': 'username',
                'message': '👤 Имя пользователя:',
                'validate': lambda x: len(x.strip()) > 0 or "Имя пользователя не может быть пустым"
            },
            {
                'type': 'text',
                'name': 'category',
                'message': self.messages["category_prompt"],
                'default': ""
            }
        ]
        if not generate:
            questions.append({
                'type': 'password',
                'name': 'password',
                'message': '🔒 Пароль:',
                'validate': lambda x: len(x) >= 8 or "Пароль должен содержать не менее 8 символов"
            })
        data = prompt(questions, style=self.style)
        if not generate and data:
            strength = self.check_password_strength(data["password"])
            self.console.print(f"Сила пароля: {strength}")
        return data

    def get_new_master_password(self) -> Optional[str]:
        """Запрашивает новый мастер-пароль и его подтверждение."""
        questions = [
            {
                'type': 'password',
                'name': 'new_password',
                'message': self.messages["new_master_password"],
                'validate': lambda x: len(x) >= 8 or "Пароль должен содержать не менее 8 символов"
            },
            {
                'type': 'password',
                'name': 'confirm_password',
                'message': self.messages["confirm_master_password"]
            }
        ]
        data = prompt(questions, style=self.style)
        if not data or data["new_password"] != data["confirm_password"]:
            self.display_error(self.messages["password_mismatch"])
            return None
        return data["new_password"]

    def check_password_strength(self, password: str) -> str:
        """Проверяет силу пароля и возвращает цветной результат."""
        score = 0
        if len(password) >= 8:
            score += 1
        if any(c.isupper() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in "!@#$%^&*" for c in password):
            score += 1
        if score == 1:
            return "[red]Слабый[/red]"
        elif score == 2:
            return "[yellow]Средний[/yellow]"
        return "[green]Сильный[/green]"

    def display_services(self, services: List[str], usernames: List[str], categories: List[str]):
        """Отображает список сервисов в виде таблицы."""
        table = Table(title="Доступные сервисы", show_header=True, header_style="bold cyan")
        table.add_column("Сервис", style="cyan")
        table.add_column("Имя пользователя", style="green")
        table.add_column("Категория", style="magenta")
        for service, username, category in zip(services, usernames, categories):
            table.add_row(service, username, category or "Без категории")
        self.console.print(table)

    def select_service(self, services: List[str], usernames: List[str], categories: List[str]) -> Optional[str]:
        """Запрашивает у пользователя выбор сервиса с использованием автодополнения."""
        if not services:
            self.console.print(Panel(self.messages["no_data"], border_style="red"))
            return None
        self.display_services(services, usernames, categories)
        return autocomplete(
            message="📋 Введите название сервиса:",
            choices=services,
            style=self.style,
            qmark="➤"
        ).ask()

    def service_menu(self, service: str) -> str:
        """Отображает контекстное меню для выбранного сервиса."""
        return select(
            message=f"[bold]Действия с {service}:[/bold]",
            choices=[
                {"name": "🔍 Просмотреть", "value": "view"},
                {"name": "✏️ Редактировать", "value": "edit"},
                {"name": "🗑️ Удалить", "value": "delete"},
                {"name": "⬅️ Назад", "value": "back"}
            ],
            style=self.style,
            qmark="➤"
        ).ask()

    def select_category(self, categories: List[str]) -> Optional[str]:
        """Запрашивает выбор категории."""
        categories = ["Без категории"] + categories
        return autocomplete(
            message=self.messages["select_category"],
            choices=categories,
            style=self.style,
            qmark="➤"
        ).ask()

    def confirm_action(self, message: str) -> bool:
        """Запрашивает подтверждение для опасных действий."""
        return select(
            message=message,
            choices=["Нет", "Да"],
            style=self.style
        ).ask() == "Да"

    def display_success(self, message: str):
        """Отображает сообщение об успешной операции."""
        self.console.print(Panel.fit(message, border_style="green"))

    def display_error(self, error: str):
        """Отображает сообщение об ошибке."""
        self.console.print(Panel(self.messages["error"].format(error=error), border_style="red"))

    def display_password(self, service: str, username: str, password: str, category: str = None):
        """Отображает информацию о пароле и копирует его в буфер обмена."""
        pyperclip.copy(password)
        category_text = f"\n📁 {category}" if category else ""
        self.console.print(Panel.fit(
            f"🔑 [bold]{service}[/bold]\n👤 {username}{category_text}\n{self.messages['password_copied']}",
            border_style="blue"
        ))