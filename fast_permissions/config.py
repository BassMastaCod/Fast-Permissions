import os

DB = os.environ.get('DB', 'database.db')
SECRET_KEY = os.environ.get('PERM_SECRET_KEY', None)
ALGORITHM = os.environ.get('PERM_ALGORITHM', 'HS256')
TOKEN_EXPIRE_MINUTES = int(os.environ.get('PERM_TOKEN_EXPIRE_MINUTES', 60 * 24))
TOKEN_REMEMBER_ME_DAYS = int(os.environ.get('PERM_TOKEN_REMEMBER_ME_DAYS', 365 * 10))
