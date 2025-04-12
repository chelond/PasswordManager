import os
import subprocess
import glob

KEY_FILENAME = "keyfile.pmk"


def find_usb_mounts():
    """Находит все смонтированные USB-устройства"""
    mounts = []
    try:
        # Используем lsblk для поиска USB-устройств
        result = subprocess.run(
            ['lsblk', '-o', 'MOUNTPOINT,TRAN'],
            capture_output=True,
            text=True,
            check=True
        )

        # Проверка вывода lsblk и фильтрация USB-устройств
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and "*" in parts[1].lower():
                mounts.append(parts[0])

        # Дополнительно проверяем стандартные пути монтирования
        standard_paths = [
            f"/media/{os.getenv('USER')}/*",
            "/run/media/*/*",
            "/mnt/*"
        ]

        for path in standard_paths:
            for mount in glob.glob(path):
                if os.path.ismount(mount) and mount not in mounts:
                    mounts.append(mount)

        return list(set(mounts))  # Убираем дубликаты

    except Exception as e:
        print(f"Ошибка при поиске USB: {e}")
        return []


def save_key_to_usb(mount_path, key, filename=KEY_FILENAME):
    """Сохраняет ключ на USB-устройство"""
    try:
        key_path = os.path.join(mount_path, filename)
        with open(key_path, 'w') as f:
            f.write(key)
        print(f"Ключ сохранён в {key_path}")
        return True
    except PermissionError:
        print(f"Ошибка: Нет прав для записи на устройство {mount_path}")
    except Exception as e:
        print(f"Ошибка сохранения ключа: {e}")
    return False


def read_key_from_usb(filename=KEY_FILENAME):
    """Читает ключ с USB-устройства"""
    try:
        for mount in find_usb_mounts():
            key_path = os.path.join(mount, filename)
            if os.path.isfile(key_path):
                with open(key_path, 'r') as f:
                    return f.read().strip()
    except Exception as e:
        print(f"Ошибка чтения ключа: {e}")
    return None
