# routes/config.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import Usuario, Tarjeta, TarjetaUsuario
from services import (
    esta_autenticado,
    obtener_usuario_actual,
    obtener_tarjetas_por_usuario
)
from utils import validar_datos_tarjeta_form

# ================================== Blueprint ==================================
config_bp = Blueprint("config", __name__, url_prefix="/configuracion")


# =============================== Middleware =====================================
@config_bp.before_request
def verificar_sesion():
    """
    Verifica si el usuario está autenticado antes de cada solicitud.

    Redirige a la página de login si no hay sesión activa.

    Returns:
        redirect or None: Redirección a login o None para continuar la solicitud.
    """
    if not esta_autenticado():
        return redirect(url_for("auth.login"))


# =============================== CUENTA ========================================
@config_bp.route("cuenta")
def cuenta():
    """
    Renderiza la página principal de la cuenta del usuario.

    Returns:
        render_template: Plantilla de la cuenta del usuario.
    """
    return render_template("configuracion/cuenta.html")


@config_bp.route("cuenta/actualizar_email", methods=["POST"])
def actualizar_email():
    """
    Actualiza el correo electrónico del usuario actual.

    Verifica que el email no esté registrado por otro usuario y tenga formato válido.

    Returns:
        redirect: Redirección a la página de la cuenta.
    """
    nuevo_email = request.form.get("nuevo_email")
    usuario_actual = obtener_usuario_actual()

    if nuevo_email and "@" in nuevo_email:
        existe = Usuario.query.filter_by(gmail=nuevo_email).first()
        if existe:
            if nuevo_email == usuario_actual.gmail:  # type: ignore
                flash("Ese correo ya lo estás usando.", "danger")
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
    """
    Actualiza la contraseña del usuario actual tras verificar la anterior.

    Verifica que la contraseña actual coincida y que la nueva sea confirmada correctamente.

    Returns:
        redirect: Redirección a la página de la cuenta.
    """
    pass_actual = request.form.get("pass_actual")
    pass_nuevo = request.form.get("pass_nuevo")
    pass_confirmar = request.form.get("pass_confirmar")
    usuario_actual = obtener_usuario_actual()

    if pass_nuevo == pass_confirmar:
        if check_password_hash(usuario_actual.contrasena, pass_actual):  # type: ignore
            usuario_actual.contrasena = generate_password_hash(pass_nuevo)  # type: ignore
            db.session.commit()
            flash("Contraseña actualizada correctamente.", "success")
        else:
            flash("La contraseña actual es incorrecta.", "danger")
    else:
        flash("La contraseña no coincide.", "danger")

    return redirect(url_for(".cuenta"))


# ============================= NOTIFICACIONES ===================================
@config_bp.route("notificaciones")
def notificaciones():
    """
    Renderiza la página de notificaciones del usuario.

    Returns:
        render_template: Plantilla de notificaciones.
    """
    return render_template("configuracion/notificaciones.html")


# ============================ OPCIONES DE PAGO ==================================
@config_bp.route("/opciones-de-pago")
def opciones_de_pago():
    """
    Muestra todas las tarjetas asociadas al usuario actual.

    Returns:
        render_template: Plantilla con las tarjetas del usuario.
    """
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
    """
    Añade una nueva tarjeta al usuario actual.

    Valida que todos los campos estén completos, que la tarjeta no exista,
    y crea la relación con el usuario en la tabla intermedia.

    Returns:
        redirect: Redirección a la página de opciones de pago.
    """
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
    tarjeta_existente = Tarjeta.query.filter_by(numero=numero).first()
    if tarjeta_existente:
        flash("Esta tarjeta ya está registrada.", "danger")
        return redirect(url_for("config.opciones_de_pago"))

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

    relacion = TarjetaUsuario(id_usuario=usuario_actual.id, id_tarjeta=nueva_tarjeta.id)
    db.session.add(relacion)
    db.session.commit()

    flash("Tarjeta añadida correctamente.", "success")
    return redirect(url_for("config.opciones_de_pago"))


@config_bp.route("/eliminar-tarjeta", methods=["POST"])
def eliminar_tarjeta():
    """
    Elimina una tarjeta seleccionada por el usuario.

    Returns:
        redirect: Redirección a la página de opciones de pago.
    """
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


# ============================ COMPARTIR TARJETAS ================================
@config_bp.route("/compartir-tarjeta", methods=["GET", "POST"])
def compartir_tarjeta():
    """
    Permite al propietario compartir una tarjeta con otro usuario.

    Valida que solo el propietario pueda compartir y que la relación no exista previamente.

    Returns:
        render_template or redirect: Página de compartir tarjetas o redirección tras acción.
    """
    usuario_actual = obtener_usuario_actual()
    tarjetas = obtener_tarjetas_por_usuario(usuario_actual.id)

    if request.method == "POST":
        tarjeta_id = request.form.get("tarjeta_id")
        usuario_nombre = request.form.get("usuario_nombre")

        if not tarjeta_id or not usuario_nombre:
            flash("Debes seleccionar una tarjeta y escribir un usuario", "danger")
            return redirect(url_for("config.compartir_tarjeta"))

        usuario_destino = Usuario.query.filter_by(nombre=usuario_nombre).first()
        if not usuario_destino:
            flash(f"El usuario '{usuario_nombre}' no existe", "danger")
            return redirect(url_for("config.compartir_tarjeta"))

        tarjeta = Tarjeta.query.get(tarjeta_id)
        if not tarjeta:
            flash("La tarjeta seleccionada no existe", "danger")
            return redirect(url_for("config.compartir_tarjeta"))

        if tarjeta.propietario_id != usuario_actual.id:
            flash("Solo el propietario puede compartir esta tarjeta", "danger")
            return redirect(url_for("config.compartir_tarjeta"))

        existente = TarjetaUsuario.query.filter_by(
            id_usuario=usuario_destino.id, id_tarjeta=tarjeta.id
        ).first()

        if existente:
            flash("La tarjeta ya está compartida con este usuario.", "info")
        else:
            relacion = TarjetaUsuario(id_usuario=usuario_destino.id, id_tarjeta=tarjeta.id)
            db.session.add(relacion)
            db.session.commit()
            flash(f"Tarjeta compartida correctamente con {usuario_destino.nombre}", "success")

        return redirect(url_for("config.compartir_tarjeta"))

    return render_template(
        "configuracion/compartir-tarjetas.html",
        tarjetas=tarjetas
    )
