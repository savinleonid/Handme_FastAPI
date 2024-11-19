# config.py
from starlette.templating import Jinja2Templates

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

templates = Jinja2Templates(directory="app/templates")