from .cartera import Cartera
from .recargar import Recargar
from .tarjeta import Tarjeta
from .transaccion import Transaccion
from .usuario import Usuario

# ---------------------------- CREAR BASE DE DATOS ------------------------------ #

# app.py
import os
from flask import Flask
from database import db, DATA_DIR, DB_PATH

# import models  # Importa tus modelos para que db.create_all() los conozca

app = Flask(__name__)

# Asegura que la carpeta 'data' exista antes de configurar la URI
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    print(f"Carpeta '{DATA_DIR}' creada.")

# Configura la URI de la base de datos
# Usa DB_PATH que ya apunta a 'data/proyecto.db'
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializa db con la app
db.init_app(app)

# Script para crear la base de datos si se ejecuta app.py directamente
if __name__ == "__main__":
    with app.app_context():
        print(f"Creando base de datos en: {DB_PATH} usando Flask-SQLAlchemy...")
        # db.create_all() crea todas las tablas de los modelos importados
        db.create_all()
        print("Tablas creadas con éxito.")

        # Aquí puedes añadir lógica para empezar a ejecutar tu app Flask normalmente:
        # app.run(debug=True)
