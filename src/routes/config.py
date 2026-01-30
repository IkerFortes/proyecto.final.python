# routes/config.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from database import db
from models import Usuario
from services import esta_autenticado, obtener_usuario_actual
from werkzeug.security import generate_password_hash, check_password_hash

from services import obtener_tarjetas_por_usuario

# Creamos el Blueprint
config_bp = Blueprint("config", __name__, url_prefix="/configuracion")

# Middleware para proteger todas las rutas de este archivo de un solo golpe


@config_bp.before_request
def verificar_sesion():
    if not esta_autenticado():
        return redirect(url_for("auth.login"))


# =================================== CUENTA ================================= #


@config_bp.route("cuenta")
def cuenta():
    return render_template("configuracion/cuenta.html")


@config_bp.route("cuenta/actualizar_email", methods=["POST"])
def actualizar_email():

    nuevo_email = request.form.get("nuevo_email")
    usuario_actual = obtener_usuario_actual()

    if nuevo_email and "@" in nuevo_email:
        # Verificar si el email ya lo tiene otro usuario
        existe = Usuario.query.filter_by(gmail=nuevo_email).first()
        if existe:
            if nuevo_email == usuario_actual.gmail:  # type: ignore
                flash("Ese correo ya lo estas usando.", "danger")
            else:
                flash("Ese correo ya está registrado por otro usuario.", "danger")
        else:
            usuario_actual.gmail = nuevo_email  # type: ignore
            db.session.commit()
            flash("Correo electrónico actualizado con éxito.", "success")
    else:
        flash("Formato de correo no válido.", "danger")

    return redirect(url_for(".cuenta"))


@config_bp.route("cuenta/actualizar_contrasena", methods=["POST"])
def actualizar_contrasena():

    pass_actual = request.form.get("pass_actual")
    pass_nuevo = request.form.get("pass_nuevo")
    pass_confirmar = request.form.get("pass_confirmar")
    usuario_actual = obtener_usuario_actual()

    # Verificar la contraseña actual (suponiendo que usaste generate_password_hash al crear al usuario)
    if pass_nuevo == pass_confirmar:
        if check_password_hash(usuario_actual.contrasena, pass_actual):  # type: ignore
            usuario_actual.contrasena = generate_password_hash(pass_nuevo)  # type: ignore
            db.session.commit()
            flash("Contraseña actualizada correctamente.", "success")
        else:
            flash("La contraseña actual es incorrecta.", "danger")
    else:
        flash("La contraseña no cohincide.", "danger")

    return redirect(url_for(".cuenta"))


# =================================== CUENTA ================================= #


@config_bp.route("notificaciones")
def notificaciones():
    return render_template("configuracion/notificaciones.html")


@config_bp.route("opciones-de-pago")
def opciones_de_pago():
    usuario_actual = obtener_usuario_actual()
    tarjetas = obtener_tarjetas_por_usuario(usuario_actual.id)  # type: ignore

    return render_template("configuracion/opciones-de-pago.html", tarjetas=tarjetas)


@config_bp.route("configuracion-avanzada")
def configuracion_avanzada():
    return render_template("configuracion/configuracion-avanzada.html")
