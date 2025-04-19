import os

HOME_DIR = os.path.expanduser("~")
DB_PATH = os.path.join(HOME_DIR, ".passman.db")
SALT_FILE = os.path.join(HOME_DIR, ".passman_salt.bin")
MASTER_HASH_FILE = os.path.join(HOME_DIR, ".passman_master.hash")
CONFIG_FILE = os.path.join(HOME_DIR, ".passman_config.yaml")
LOG_FILE = os.path.join(HOME_DIR, ".passman.log")
ARGON2_PARAMS = {
    "time_cost": 4,
    "memory_cost": 65536,
    "parallelism": 2,
    "hash_len": 32
}
GENERATED_PASSWORD_LENGTH = 16
DEFAULT_CONFIG = {
    "ui": {
        "language": "ru",
        "theme": "default"
    }
}