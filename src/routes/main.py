from flask import Blueprint, render_template, redirect, url_for, jsonify, request, flash
from database import db
from datetime import datetime
from sqlalchemy import func
from models import Transaccion, Usuario, Cartera
from services import esta_autenticado, obtener_usuario_actual
from utils import traducir_mes, obtener_datos_grafico_saldo_evolutivo

main_bp = Blueprint("main", __name__)


@main_bp.before_request
def verificar_sesion():
    if not esta_autenticado():
        return redirect(url_for("auth.login"))


# =================================== PÁGINA PRINCIPAL ================================= #


# Index #
@main_bp.route("/")
def index():
    """Renderiza la página de inicio de la cuenta, mostrando los gastos mensuales del usuario.

    Recupera el total de transacciones enviadas por el usuario en el mes y año actual.

    Args:
        None (espera parámetros de contexto estándar de Flask/Jinja si los hubiera)

    Returns:
        render_template: La plantilla HTML para la página de inicio, pasando gastos y el mes actual.
    """

    hoy = datetime.now()
    usuario_actual = obtener_usuario_actual()

    # --- GASTOS MENSUALES ---
    # Suma las transacciones ENVIADAS por el usuario en el mes y año actual
    gastos_mensuales = (
        db.session.query(func.sum(Transaccion.cantidad))
        .filter(
            Transaccion.id_cartera_enviado == usuario_actual.cartera.id,  # type: ignore
            func.extract("month", Transaccion.fecha) == hoy.month,
            func.extract("year", Transaccion.fecha) == hoy.year,
        )
        .scalar()
        or 0.0
    )

    # Obtener el nombre del mes actual en español (ej. "enero")
    # %B formatea el nombre completo del mes, y .capitalize() pone la primera en mayúscula
    mes_actual = hoy.strftime("%B").capitalize()
    mes_actual = traducir_mes(mes_actual)

    return render_template(
        "cuenta/index.html",
        gastos_mensuales=gastos_mensuales,
        mes_actual=mes_actual,
    )


# Para cargar el gráfico (la que llamará el JS)
@main_bp.route("/api/grafico/<rango>")
def api_grafico(rango):
    """Endpoint API para obtener datos del gráfico de evolución de saldo.

    Requiere autenticación. Devuelve datos formateados en JSON para ser consumidos por JavaScript.

    Args:
        rango (str): El rango de tiempo para el cual obtener los datos (ej. 'semana', 'mes', 'año').

    Returns:
        jsonify: Un objeto JSON con los datos del gráfico o un mensaje de error 401 si no está autenticado.
    """

    if not esta_autenticado():
        return jsonify({"error": "No autorizado"}), 401

    usuario_actual = obtener_usuario_actual()

    datos = obtener_datos_grafico_saldo_evolutivo(usuario_actual.cartera.id, rango)  # type: ignore
    return jsonify(datos)


# =================================== PÁGINA PRINCIPAL ================================= #


# =================================== TRANSFERENCIAS ================================= #


@main_bp.route("/transferir", methods=["GET", "POST"])
def transferencias():
    """Maneja la lógica para transferir fondos entre usuarios.

    En el método GET, renderiza el formulario de transferencia.
    En el método POST, procesa los datos del formulario, valida la cantidad y el receptor,
    verifica el saldo, realiza la transacción en la base de datos y maneja los errores.

    Args:
        None (espera datos de formulario a través de 'request.form' para POST)

    Returns:
        render_template: La plantilla HTML para la página de transferir, pasando datos de usuario y mensajes de error.
    """

    usuario_actual = obtener_usuario_actual()
    if not usuario_actual or not usuario_actual.cartera:
        return redirect(url_for("login"))

    error_transferencia = ""  # Por defecto no hay error

    if request.method == "POST":
        dni_receptor = request.form.get("usu_transferir")
        cantidad = request.form.get("cantidad_transferir")

        # Validación de cantidad
        try:
            cantidad = float(cantidad)
            if cantidad <= 0:
                error_transferencia = "La cantidad debe ser mayor a 0"
                return render_template(
                    "cuenta/transferir.html",
                    usuario=usuario_actual,
                    error_transferencia=error_transferencia,
                )
        except (ValueError, TypeError):
            error_transferencia = "Cantidad inválida"
            return render_template(
                "cuenta/transferir.html",
                usuario=usuario_actual,
                error_transferencia=error_transferencia,
            )

        # Buscar usuario receptor
        receptor = Usuario.query.filter_by(dni=dni_receptor).first()
        if not receptor or not receptor.cartera:
            error_transferencia = "El usuario receptor no existe o no tiene cartera"
            return render_template(
                "cuenta/transferir.html",
                usuario=usuario_actual,
                error_transferencia=error_transferencia,
            )

        # Comprobar saldo suficiente
        if usuario_actual.cartera.cantidad < cantidad:
            error_transferencia = "Saldo insuficiente"
            return render_template(
                "cuenta/transferir.html",
                usuario=usuario_actual,
                error_transferencia=error_transferencia,
            )

        # Realizar transferencia
        usuario_actual.cartera.cantidad -= cantidad
        receptor.cartera.cantidad += cantidad

        # Crear registro de transacción
        transaccion = Transaccion(
            cantidad=cantidad,
            id_cartera_enviado=usuario_actual.cartera.id,
            id_cartera_recibido=receptor.cartera.id,
            fecha=datetime.now(),
        )
        db.session.add(transaccion)

        try:
            db.session.commit()
            error_transferencia = (
                f"Transferencia de {cantidad} a {receptor.nombre} realizada con éxito"
            )
            # También puedes cambiar el color en el template según el mensaje de éxito
        except Exception as e:
            db.session.rollback()
            error_transferencia = f"Error al procesar la transferencia: {str(e)}"

    # Renderizar siempre el template con el error (si lo hay)
    return render_template(
        "cuenta/transferir.html",
        usuario=usuario_actual,
        error_transferencia=error_transferencia,
    )


# historial #
@main_bp.route("/historial")
def historial():
    """Renderiza la página del historial de transacciones del usuario.

    Requiere que el usuario esté autenticado. Pasa el objeto del usuario actual a la plantilla.

    Args:
        None (espera parámetros de contexto estándar de Flask/Jinja si los hubiera)

    Returns:
        redirect or render_template:
            - Redirección a la página de login si el usuario no está autenticado.
            - La plantilla HTML para la página del historial si está autenticado.
    """
    if not esta_autenticado():
        return redirect(url_for("login"))

    usuario_actual = obtener_usuario_actual()
    hoy = datetime.now()

    return render_template("cuenta/historial.html", usuario=usuario_actual)
