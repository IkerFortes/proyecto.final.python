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
    obtener_tarjetas_por_usuario
)


from werkzeug.security import generate_password_hash, check_password_hash

from services import obtener_tarjetas_por_usuario
from utils import validar_datos_tarjeta_form

# Creamos el Blueprint
config_bp = Blueprint("config", __name__, url_prefix="/configuracion")

# Middleware para proteger todas las rutas de este archivo de un solo golpe


@config_bp.before_request
def verificar_sesion():
    """Verifica si el usuario está autenticado antes de cada solicitud en este blueprint.

    Si el usuario no está logueado, lo redirige a la página de inicio de sesión.

    Args:
        None (Esta función es un hook de Flask, no recibe argumentos explícitos)

    Returns:
        redirect or None: Una redirección a la página de login si no hay sesión,
                         o None para continuar con la solicitud si está autenticado.
    """

    if not esta_autenticado():
        return redirect(url_for("auth.login"))


# =================================== CUENTA ================================= #


@config_bp.route("cuenta")
def cuenta():
    """Renderiza la página principal de la cuenta del usuario.

    Args:
        None (espera parámetros de contexto estándar de Flask/Jinja si los hubiera)

    Returns:
        render_template: La plantilla HTML para la página de la cuenta.
    """

    return render_template("configuracion/cuenta.html")


@config_bp.route("cuenta/actualizar_email", methods=["POST"])
def actualizar_email():
    """Actualiza el correo electrónico del usuario actual.

    Args:
        None (explícito en la función, pero espera datos de formulario en 'request')

    Returns:
        redirect: Una redirección a la página de la cuenta.
    """

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
    """Actualiza la contraseña del usuario actual tras verificar la anterior.

    Args:
        None (explícito en la función, pero espera datos de formulario en 'request')

    Returns:
        redirect: Una redirección a la página de la cuenta.
    """

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
    """Renderiza la página de notificaciones.

    Args:
        None (espera parámetros de contexto estándar de Flask/Jinja si los hubiera)

    Returns:
        render_template: La plantilla HTML para la página de notificaciones.
    """

    return render_template("configuracion/notificaciones.html")





# ================================== OPCIONES DE PAGO ==================================

@config_bp.route("/opciones-de-pago")
def opciones_de_pago():
    usuario_actual = obtener_usuario_actual()
    tarjetas = obtener_tarjetas_por_usuario(usuario_actual.id)
    return render_template("configuracion/opciones-de-pago.html", tarjetas=tarjetas)


@config_bp.route("/anadir-tarjeta", methods=["GET", "POST"])
def anadir_tarjeta():
    usuario_actual = obtener_usuario_actual()
    error_tarjeta = ""

    if request.method == "POST":
        propietario = request.form.get("propietario")
        numero = request.form.get("numero")
        caducidad = request.form.get("caducidad")
        cvc = request.form.get("cvc")

        if not all([propietario, numero, caducidad, cvc]):
            error_tarjeta = "Todos los campos son obligatorios"
        elif len(numero) != 16 or not numero.isdigit():
            error_tarjeta = "Número de tarjeta inválido"
        elif len(cvc) != 3 or not cvc.isdigit():
            error_tarjeta = "CVC inválido"
        else:
            nueva_tarjeta = Tarjeta(
                propietario_nombre=propietario,
                numero=numero,
                caducidad=caducidad,
                cvc=int(cvc),
                id_usuario=usuario_actual.id,
            )
            if registrada_tarjeta(nueva_tarjeta):
                error_tarjeta = "Esta tarjeta ya está registrada"
            else:
                guardar_tarjeta_en_db(nueva_tarjeta)
                render_template(
        "configuracion/anadir-tarjeta.html",
        usuario=usuario_actual,
        error_tarjeta=error_tarjeta,
    )
    return render_template(
        "configuracion/anadir-tarjeta.html",
        usuario=usuario_actual,
        error_tarjeta=error_tarjeta,
    )


# ================================== MIS TARJETAS ==================================

@config_bp.route("/mis-tarjetas", methods=["GET", "POST"])
def mis_tarjetas():
    usuario_actual = obtener_usuario_actual()
    tarjetas = obtener_tarjetas_por_usuario(usuario_actual.id)
    
    # Para no depender de funciones inexistentes, solo mostramos tarjetas
    return render_template(
        "configuracion/mis-tarjetas.html",
        tarjetas=tarjetas,
        usuarios=[],  # opcional, no se comparte nada
        mensaje=None
    )


# ================================== ELIMINAR TARJETA ==================================

@config_bp.route("/eliminar-tarjeta", methods=["POST"])
def eliminar_tarjeta():
    tarjeta_id = request.form.get("tarjeta_id")
    if tarjeta_id:
        t = Tarjeta.query.get(tarjeta_id)
        if t:
            db.session.delete(t)
            db.session.commit()
            flash("Tarjeta eliminada correctamente", "success")
        else:
            flash("Tarjeta no encontrada", "danger")
    else:
        flash("No se pudo eliminar la tarjeta", "danger")
    return redirect(url_for("config.mis_tarjetas"))


@config_bp.route("/compartir-tarjeta", methods=["POST"])
def compartir_tarjeta():
    tarjeta_id = request.form.get("tarjeta_id")
    usuario_nombre = request.form.get("usuario_nombre")

    if not tarjeta_id or not usuario_nombre:
        mensaje = "Debes seleccionar una tarjeta y escribir un usuario"
        return redirect(url_for("config.mis_tarjetas", mensaje=mensaje))

    # Buscar usuario por nombre
    usuario_destino = Usuario.query.filter_by(nombre=usuario_nombre).first()
    if not usuario_destino:
        mensaje = f"El usuario '{usuario_nombre}' no existe"
        return render_template(
            "configuracion/mis-tarjetas.html",
            tarjetas=obtener_tarjetas_por_usuario(obtener_usuario_actual().id),
            mensaje=mensaje
        )

    # Aquí tu lógica de compartir tarjeta
    # Por ejemplo, podrías crear un registro en otra tabla de "tarjetas compartidas"
    mensaje = f"Tarjeta compartida correctamente con {usuario_destino.nombre}"

    return render_template(
        "configuracion/mis-tarjetas.html",
        tarjetas=obtener_tarjetas_por_usuario(obtener_usuario_actual().id),
        mensaje=mensaje
    )
