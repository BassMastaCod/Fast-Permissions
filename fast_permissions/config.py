import os

SECRET_KEY = os.environ.get('PERM_SECRET_KEY', None)
ALGORITHM = os.environ.get('PERM_ALGORITHM', 'HS256')
