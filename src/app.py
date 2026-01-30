import os
from flask import Flask
from routes.config import config_bp  # Importa tu nuevo archivo
from routes.main import main_bp  # Importa tu nuevo archivo
from routes.auth import auth_bp  # Importa tu nuevo archivo

from sqlalchemy import func
from database import db
from datetime import datetime
from services import esta_autenticado, obtener_usuario_actual


app = Flask(__name__)
app.secret_key = "dw2"  # Necesaria para session y flash

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
# Asegúrate de tener una URI configurada, de lo contrario dará error
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///proyecto.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializar la extensión con la app


db.init_app(app)
app.register_blueprint(config_bp)
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)

# --- SOLUCIÓN AL ERROR: Crear tablas dentro del contexto de la app ---


with app.app_context():
    # Esto ahora funcionará porque tiene el contexto de la aplicación activo
    db.create_all()


@app.context_processor
def inject_user():
    # Esto hace que 'usuario' y 'autenticado' funcionen en CUALQUIER HTML
    # sin tener que ponerlos en el return render_template(...)
    return dict(
        usuario=obtener_usuario_actual(),
        autenticado=esta_autenticado(),
        # hoy=datetime.now(),
    )


if __name__ == "__main__":
    app.run(debug=True)
    print(app.url_map)
