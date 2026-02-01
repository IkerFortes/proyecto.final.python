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
    tarjetas_query = Tarjeta.query.filter_by(propietario_id=usuario_actual.id).all()
    tarjetas = []

    for t in tarjetas_query:
        propietario = Usuario.query.get(t.propietario_id)
        tarjetas.append({
            "id": t.id,
            "numero": t.numero,
            "caducidad": t.caducidad,
            "cvc": t.cvc,
            "propietario_nombre": t.propietario_nombre,
        })

    return render_template("configuracion/opciones-de-pago.html", tarjetas=tarjetas)



@config_bp.route("/anadir-tarjeta", methods=["POST"])
def anadir_tarjeta():
    usuario_actual = obtener_usuario_actual()
    
    if not usuario_actual:
        flash("Debes iniciar sesión para añadir una tarjeta.", "danger")
        return redirect(url_for("auth.login"))

    numero = request.form.get("numero_tarjeta")
    mes = request.form.get("caducidad_tarjeta_mes")
    ano = request.form.get("caducidad_tarjeta_ano")
    cvc = request.form.get("cvc_tarjeta")
    propietario = request.form.get("propietario_tarjeta")

    if not all([propietario, numero, mes, ano, cvc]):
        flash("Todos los campos son obligatorios.", "danger")
        return redirect(url_for("config.opciones_de_pago"))

    caducidad = f"{mes}/{ano}"

    # Verificar si ya existe tarjeta con ese número
    tarjeta_existente = Tarjeta.query.filter_by(numero=numero).first()
    if tarjeta_existente:
        flash("Esta tarjeta ya está registrada.", "danger")
        return redirect(url_for("config.opciones_de_pago"))

    # Crear tarjeta asociada al usuario actual
    nueva_tarjeta = Tarjeta(
        numero=numero,
        caducidad=caducidad,
        cvc=int(cvc),
        saldo=0,
        propietario_nombre=propietario, 
        propietario_id=usuario_actual.id 
    )
    db.session.add(nueva_tarjeta)
    db.session.commit()

    # Crear la relación en la tabla intermedia
    from models import TarjetaUsuario
    relacion = TarjetaUsuario(id_usuario=usuario_actual.id, id_tarjeta=nueva_tarjeta.id)
    db.session.add(relacion)
    db.session.commit()

    flash("Tarjeta añadida correctamente.", "success")
    return redirect(url_for("config.opciones_de_pago"))





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
    return redirect(url_for("config.opciones_de_pago"))


# ================================== COMPARTIR TARJETAS ==================================

@config_bp.route("/compartir-tarjeta", methods=["GET", "POST"])
def compartir_tarjeta():
    usuario_actual = obtener_usuario_actual()
    tarjetas = obtener_tarjetas_por_usuario(usuario_actual.id)

    if request.method == "POST":
        tarjeta_id = request.form.get("tarjeta_id")
        usuario_nombre = request.form.get("usuario_nombre")

        if not tarjeta_id or not usuario_nombre:
            flash("Debes seleccionar una tarjeta y escribir un usuario", "danger")
            return redirect(url_for("config.compartir_tarjeta"))

        # Buscar al usuario destino
        usuario_destino = Usuario.query.filter_by(nombre=usuario_nombre).first()
        if not usuario_destino:
            flash(f"El usuario '{usuario_nombre}' no existe", "danger")
            return redirect(url_for("config.compartir_tarjeta"))

        # Buscar la tarjeta
        tarjeta = Tarjeta.query.get(tarjeta_id)
        if not tarjeta:
            flash("La tarjeta seleccionada no existe", "danger")
            return redirect(url_for("config.compartir_tarjeta"))

        # ✅ Verificar que solo el propietario pueda compartir
        if tarjeta.propietario_id != usuario_actual.id:
            flash("Solo el propietario puede compartir esta tarjeta", "danger")
            return redirect(url_for("config.compartir_tarjeta"))

        # Verificar si ya está compartida
        from models import TarjetaUsuario
        existente = TarjetaUsuario.query.filter_by(
            id_usuario=usuario_destino.id, id_tarjeta=tarjeta.id
        ).first()

        if existente:
            flash("La tarjeta ya está compartida con este usuario.", "info")
        else:
            # Crear la relación sin tocar la tarjeta original
            relacion = TarjetaUsuario(id_usuario=usuario_destino.id, id_tarjeta=tarjeta.id)
            db.session.add(relacion)
            db.session.commit()
            flash(f"Tarjeta compartida correctamente con {usuario_destino.nombre}", "success")

        return redirect(url_for("config.compartir_tarjeta"))

    return render_template(
        "configuracion/compartir-tarjetas.html",
        tarjetas=tarjetas
    )
