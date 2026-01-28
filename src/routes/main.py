from flask import Blueprint, render_template, redirect, url_for, jsonify
from database import db
from datetime import datetime
from sqlalchemy import func
from models import Transaccion
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
    if not esta_autenticado():
        return jsonify({"error": "No autorizado"}), 401

    usuario_actual = obtener_usuario_actual()

    datos = obtener_datos_grafico_saldo_evolutivo(usuario_actual.cartera.id, rango)  # type: ignore
    return jsonify(datos)


# =================================== PÁGINA PRINCIPAL ================================= #
