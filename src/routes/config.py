# routes/config.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from database import db
from models import Usuario
from models import Tarjeta
from services import (
    esta_autenticado,
    obtener_usuario_actual,
    registrada_tarjeta,
    guardar_tarjeta_en_db,
)
from werkzeug.security import generate_password_hash, check_password_hash

from services import obtener_tarjetas_por_usuario
from utils import validar_datos_tarjeta_form

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


# =================================== OPCIONES DE PAGO ================================= #


@config_bp.route("opciones-de-pago")
def opciones_de_pago():
    usuario_actual = obtener_usuario_actual()
    print(
        f"DEBUG: Buscando tarjetas para el usuario ID: {usuario_actual.id}"  # type: ignore
    )  # Revisa tu consola
    tarjetas = obtener_tarjetas_por_usuario(usuario_actual.id)  # type: ignore
    print(f"DEBUG: Tarjetas encontradas: {len(tarjetas) if tarjetas else 0}")

    return render_template("configuracion/opciones-de-pago.html", tarjetas=tarjetas)


@config_bp.route("/anadir-tarjeta", methods=["POST"])
def anadir_tarjeta():
    # Recogemos todos los datos
    form_data = {
        "propietario": request.form.get("propietario_tarjeta"),
        "numero": request.form.get("numero_tarjeta"),
        "dia": request.form.get("caducidad_tarjeta_dia"),
        "mes": request.form.get("caducidad_tarjeta_mes"),
        "cvc": request.form.get("cvc_tarjeta"),
    }

    usuario_actual = obtener_usuario_actual()

    # Validar masivamente
    es_valida, mensaje = validar_datos_tarjeta_form(**form_data)

    if not es_valida:
        flash(mensaje, "danger")  # type: ignore
        # Obtenemos las tarjetas de nuevo para recargar la página correctamente
        usuario_actual = obtener_usuario_actual()
        tarjetas = obtener_tarjetas_por_usuario(usuario_actual.id)  # type: ignore

        # IMPORTANTE: Pasamos 'form_data' de vuelta al HTML
        return render_template(
            "configuracion/opciones-de-pago.html",
            tarjetas=tarjetas,
            datos_previos=form_data,
        )

    # Formateamos la fecha para guardarla (ejemplo: "DD/MM")
    fecha_full = f"{form_data['dia']}/{form_data['mes']}"

    nueva_tarjeta = Tarjeta(
        propietario_nombre=form_data["propietario"],  # type: ignore
        numero=form_data["numero"],  # type: ignore
        caducidad=fecha_full,  # type: ignore
        cvc=form_data["cvc"],  # type: ignore
        id_usuario=usuario_actual.id,  # type: ignore
    )

    guardar_tarjeta_en_db(nueva_tarjeta)
    flash("Tarjeta añadida con éxito", "success")

    return redirect(url_for("config.opciones_de_pago"))


# =================================== OPCIONES DE PAGO ================================= #


@config_bp.route("configuracion-avanzada")
def configuracion_avanzada():
    return render_template("configuracion/configuracion-avanzada.html")
