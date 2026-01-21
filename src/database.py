from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import create_engine  # Importa esto

# Creamos una instancia de SQLAlchemy vacía por ahora
# Se inicializará más tarde en app.py con los parámetros de la app Flask
db = SQLAlchemy()

# Define la ruta de la base de datos para que main.py pueda importarla
# Asegúrate de que esta ruta coincida con la que usarás en app.py si es diferente
DB_PATH = "proyecto.db"

# Crea el motor de SQLAlchemy manualmente para que main.py pueda usarlo
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(DATABASE_URL)
