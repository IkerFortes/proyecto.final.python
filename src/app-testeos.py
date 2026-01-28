import os
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from sqlalchemy import func
from database import db
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash # Importamos para hashear contraseñas

# Importa todos tus modelos para que db.create_all() los detecte
from models.models import Usuario, Cartera, Tarjeta, Recargar, Transaccion

# Importa tus servicios si los necesitas (ej. login_usuario, obtener_usuario_actual, etc.)
from services import obtener_datos_grafico_ingresos, esta_autenticado, obtener_usuario_actual, crear_usuario, login_usuario, logout_usuario

# Importar el módulo decimal y convertir los números, o bien trabajar con objetos Decimal.
from decimal import Decimal


app = Flask(__name__)
app.secret_key = "dw2" # Necesaria para session y flash

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
# Asegúrate de tener una URI configurada, de lo contrario dará error
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///proyecto.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializar la extensión con la app
db.init_app(app)

# --- SOLUCIÓN AL ERROR: Crear tablas dentro del contexto de la app ---
with app.app_context():
    # Esto ahora funcionará porque tiene el contexto de la aplicación activo
    db.create_all()




# --- FUNCIÓN PARA CREAR DATOS FICTICIOS -------------------------------------------------------------------------------------- #
def crear_datos_ficticios():
    # Limpiar tablas existentes
    db.session.query(Transaccion).delete()
    db.session.query(Recargar).delete()
    db.session.query(Tarjeta).delete()
    db.session.query(Cartera).delete()
    db.session.query(Usuario).delete()
    db.session.commit()
    print("Base de datos limpia.")

    # 1. Crear 2 usuarios
    u1 = Usuario(dni="11111111A", nombre="Alice", apellidos="Smith", usuario="alice_s",
                 contrasena=generate_password_hash("pass123"), gmail="alice@example.com")
    u2 = Usuario(dni="22222222B", nombre="Bob", apellidos="Johnson", usuario="bob_j",
                 contrasena=generate_password_hash("pass123"), gmail="bob@example.com")

    # 2. CREAR LAS CARTERAS MANUALMENTE (Evita el AttributeError: 'NoneType')
    u1.cartera = Cartera(cantidad=Decimal('0.0'))
    u2.cartera = Cartera(cantidad=Decimal('0.0'))

    # Guardamos para generar IDs
    db.session.add_all([u1, u2])
    db.session.commit()

    # Referencias a las carteras ya creadas
    c1 = u1.cartera
    c2 = u2.cartera

    # 3. Recargas iniciales (Usando Decimal para evitar TypeError)
    recarga_a = Decimal('500.0')
    recarga_b = Decimal('100.0')

    r1 = Recargar(id_cartera=c1.id, cantidad=recarga_a, fecha=datetime.now() - timedelta(days=35))
    r2 = Recargar(id_cartera=c2.id, cantidad=recarga_b, fecha=datetime.now() - timedelta(days=30))

    c1.cantidad += recarga_a
    c2.cantidad += recarga_b

    db.session.add_all([r1, r2])
    db.session.commit()

    # 4. Transferencias con historial ficticio (Alice envía a Bob)
    # Definimos las cantidades como Decimal
    t_montos = [Decimal('20.0'), Decimal('50.0'), Decimal('15.0'), Decimal('30.0')]

    t1 = Transaccion(cantidad=t_montos[0], id_cartera_enviado=c1.id, id_cartera_recibido=c2.id, fecha=datetime.now() - timedelta(days=28))
    t2 = Transaccion(cantidad=t_montos[1], id_cartera_enviado=c1.id, id_cartera_recibido=c2.id, fecha=datetime.now() - timedelta(days=15))
    t3 = Transaccion(cantidad=t_montos[2], id_cartera_enviado=c1.id, id_cartera_recibido=c2.id, fecha=datetime.now() - timedelta(days=5))
    t4 = Transaccion(cantidad=t_montos[3], id_cartera_enviado=c1.id, id_cartera_recibido=c2.id, fecha=datetime.now())

    # Actualizar saldos sumando la lista de Decimals
    total_transferido = sum(t_montos)
    c1.cantidad -= total_transferido
    c2.cantidad += total_transferido

    db.session.add_all([t1, t2, t3, t4])
    db.session.commit()

    print(f"Datos ficticios creados: Alice tiene {c1.cantidad}€, Bob tiene {c2.cantidad}€.")
# --------------------------------------------------IFO----------------------------------------------------------------------------------------------------- #





# --- --- --- --- --- --- --- --- --- RUTAS DE LA APP --- --- --- --- --- --- --- --- --- #

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Datos del formulario HTML que pasaste antes
        user_input = request.form.get("nombre_usuario")
        pass_input = request.form.get("contraseña")

        usuario = login_usuario(user_input, pass_input)

        if usuario:
            flash(f"Bienvenido de nuevo, {usuario.nombre}", "success")
            return redirect(url_for("index"))

        flash("Credenciales inválidas. Inténtalo de nuevo.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_usuario()
    return redirect(url_for("login"))

@app.route("/")
def index():
    if not esta_autenticado():
        return redirect(url_for("login"))

    usuario_actual = obtener_usuario_actual()
    hoy = datetime.now()

    # --- INGRESOS DIARIOS ---
    # Suma las transacciones recibidas por el usuario hoy
    ingresos_diarios = db.session.query(func.sum(Transaccion.cantidad)).filter(
        Transaccion.id_cartera_recibido == usuario_actual.cartera.id,
        func.date(Transaccion.fecha) == hoy.date()
    ).scalar() or 0.0

    # --- INGRESOS MENSUALES ---
    # Suma las transacciones recibidas en el mes y año actual
    ingresos_mensuales = db.session.query(func.sum(Transaccion.cantidad)).filter(
        Transaccion.id_cartera_recibido == usuario_actual.cartera.id,
        func.extract('month', Transaccion.fecha) == hoy.month,
        func.extract('year', Transaccion.fecha) == hoy.year
    ).scalar() or 0.0

    return render_template("index.html",
                           usuario=usuario_actual,
                           ingresos_diarios=ingresos_diarios,
                           ingresos_mensuales=ingresos_mensuales)

# NUEVA RUTA para el gráfico (la que llamará el JS)
@app.route("/api/grafico/<rango>")
def api_grafico(rango):
    if not esta_autenticado():
        return jsonify({"error": "No autorizado"}), 401
    usuario_actual = obtener_usuario_actual()
    datos = obtener_datos_grafico_ingresos(usuario_actual.cartera.id, rango)
    return jsonify(datos)


# Aquí puedes añadir el resto de tus rutas de la API...
@app.route("/registrarse", methods=["GET", "POST"])
def registrarse():
    if request.method == "POST":
        # Verificar si las contraseñas coinciden antes de ir al servicio
        pass1 = request.form.get("contrasena")
        pass2 = request.form.get("contrarep")

        if pass1 != pass2:
            flash("Las contraseñas no coinciden", "danger")
            return redirect(url_for("registrarse"))

        # Mapeo de datos para el servicio crear_usuario
        datos = {
            "dni": request.form.get("dni"),
            "nombre": request.form.get("nombre"),
            "apellidos": request.form.get("apellidos"),
            "usuario": request.form.get("usuario"),
            "contrasena": pass1,
            "gmail": request.form.get("gmail")
        }

        exito, mensaje = crear_usuario(datos)

        if exito:
            flash("¡Cuenta creada! Ahora puedes iniciar sesión.", "success")
            return redirect(url_for("login"))
        else:
            flash(mensaje, "danger")

    return render_template("registrarse.html")

# if __name__ == "__main__":
#     app.run(debug=True)


# --- EJECUCIÓN PRINCIPAL TEST ---
if __name__ == "__main__":
    with app.app_context():
        # Crea todas las tablas si no existen
        db.create_all()
        print("Tablas de la base de datos verificadas.")

        # Llama a esta función para rellenar la base de datos con datos de prueba
        # if Usuario.query.count() == 0:
        print("Base de datos vacía, generando datos ficticios...")
        crear_datos_ficticios()

        # Inicia la aplicación Flask
        app.run(debug=True)