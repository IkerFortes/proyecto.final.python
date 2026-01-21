import os
from flask import ( Flask, jsonify, request, render_template)

from database import db
from services import *
from models import *

app = Flask(__name__)

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
# Asegúrate de tener una URI configurada, de lo contrario dará error
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///proyecto.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializar la extensión con la app
db.init_app(app)

# --- SOLUCIÓN AL ERROR: Crear tablas dentro del contexto de la app ---
# with app.app_context():
    # Esto ahora funcionará porque tiene el contexto de la aplicación activo
    # db.create_all()



# --- --- --- --- --- --- --- --- --- RUTAS DE LA APP --- --- --- --- --- --- --- --- --- #


@app.route("/")
def index():
    # Renderiza el archivo src/templates/index.html
    return render_template("index.html")








# Aquí puedes añadir el resto de tus rutas de la API...

if __name__ == "__main__":
    app.run(debug=True)
