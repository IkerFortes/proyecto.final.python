# database.py
from flask_sqlalchemy import SQLAlchemy
import os

# Instancia de SQLAlchemy vacía por ahora.
db = SQLAlchemy()

# Ruta para la carpeta 'data' (útil para referencia en otros scripts)
DATA_DIR = "data"
DB_FILE_NAME = "proyecto.db"
DB_PATH = os.path.join(os.getcwd(), DATA_DIR, DB_FILE_NAME)
