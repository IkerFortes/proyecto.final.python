from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, redirect, url_for, jsonify, request, flash
from database import db
from datetime import datetime
from sqlalchemy import func
from models import Transaccion, Usuario, Cartera
from services import esta_autenticado, obtener_usuario_actual
from utils import traducir_mes, obtener_datos_grafico_saldo_evolutivo
from services import obtener_tarjetas_por_usuario

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
    usuario_actual = obtener_usuario_actual()
    if not usuario_actual or not usuario_actual.cartera:
        return redirect(url_for("login"))

    error_transferencia = ""

    # 🔹 OBTENER TARJETAS DEL USUARIO
    tarjetas = obtener_tarjetas_por_usuario(usuario_actual.id)

    if request.method == "POST":
        cantidad = request.form.get("cantidad_transferir")
        id_tarjeta = request.form.get("tarjeta_destino")

        # Validar cantidad
        try:
            cantidad = float(cantidad)
            if cantidad <= 0:
                raise ValueError
        except (ValueError, TypeError):
            error_transferencia = "Cantidad inválida"
            return render_template(
                "cuenta/transferir.html",
                usuario=usuario_actual,
                tarjetas=tarjetas,
                error_transferencia=error_transferencia,
            )

        if not id_tarjeta:
            error_transferencia = "Debes seleccionar una tarjeta"
            return render_template(
                "cuenta/transferir.html",
                usuario=usuario_actual,
                tarjetas=tarjetas,
                error_transferencia=error_transferencia,
            )


        error_transferencia = "Transferencia realizada con éxito"

    return render_template(
        "cuenta/transferir.html",
        usuario=usuario_actual,
        tarjetas=tarjetas,
        error_transferencia=error_transferencia,
    )

# ingresar 
# =================================== INGRESAR DINERO ================================= #
@main_bp.route("/ingresar", methods=["GET", "POST"])
def ingresar():
    usuario_actual = obtener_usuario_actual()
    if not usuario_actual or not usuario_actual.cartera:
        return redirect(url_for("login"))

    error_transferencia = ""

    if request.method == "POST" and "ingresarcartera" in request.form:
        cantidad_form = request.form.get("cantidad_transferir")

        # Convertir a Decimal y validar
        try:
            cantidad = Decimal(cantidad_form)
            if cantidad <= 0:
                raise ValueError("La cantidad debe ser mayor a 0")
        except (ValueError, TypeError, InvalidOperation):
            error_transferencia = "Cantidad inválida"
            return render_template("cuenta/ingresar.html", usuario=usuario_actual, error_transferencia=error_transferencia)

        # Sumar a la cartera
        usuario_actual.cartera.cantidad += cantidad

        try:
            db.session.commit()
            error_transferencia = f"Ingreso de {cantidad:.2f} € realizado con éxito"
        except Exception as e:
            db.session.rollback()
            error_transferencia = f"Error al ingresar el dinero: {str(e)}"

    return render_template("cuenta/ingresar.html", usuario=usuario_actual, error_transferencia=error_transferencia)


# historial #
@main_bp.route("/historial")
def historial():
    """Renderiza la página del historial de transacciones del usuario."""
    if not esta_autenticado():
        return redirect(url_for("login"))

    usuario_actual = obtener_usuario_actual()
    cartera_id = usuario_actual.cartera.id  # type: ignore

    # Obtener todas las transacciones donde el usuario sea emisor o receptor
    transacciones = (
        db.session.query(Transaccion)
        .filter(
            (Transaccion.id_cartera_enviado == cartera_id) |
            (Transaccion.id_cartera_recibido == cartera_id)
        )
        .order_by(Transaccion.fecha.desc())
        .all()
    )

    # Preparar datos para la tabla
    historial = []
    for t in transacciones:
        tipo = "Enviado" if t.id_cartera_enviado == cartera_id else "Recibido"
        otra_parte_id = t.id_cartera_recibido if tipo == "Enviado" else t.id_cartera_enviado

        # Buscar el nombre del usuario receptor/emisor
        otra_cartera = db.session.query(Usuario).join(Usuario.cartera)\
            .filter(Usuario.cartera.has(id=otra_parte_id)).first()
        otra_parte_nombre = otra_cartera.nombre if otra_cartera else "Desconocido"

        historial.append({
            "fecha": t.fecha.strftime("%d/%m/%Y %H:%M"),
            "tipo": tipo,
            "usuario": otra_parte_nombre,
            "cantidad": f"{t.cantidad:.2f} €"
        })

    return render_template(
        "cuenta/historial.html",
        usuario=usuario_actual,
        historial=historial
    )
