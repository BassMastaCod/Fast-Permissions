import os

DB = None
DB_PATH = os.environ.get('CONTROLLER_DB', 'database.db')
TOKEN_EXPIRE_MINUTES = int(os.environ.get('PERM_TOKEN_EXPIRE_MINUTES', 60 * 24))
TOKEN_REMEMBER_ME_DAYS = int(os.environ.get('PERM_TOKEN_REMEMBER_ME_DAYS', 365 * 10))
