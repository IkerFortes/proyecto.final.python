from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, redirect, url_for, jsonify, request, flash
from database import db
from datetime import datetime
from sqlalchemy import func
from models import Transaccion, Usuario, Cartera
from services import esta_autenticado, obtener_usuario_actual
from utils import traducir_mes, obtener_datos_grafico_saldo_evolutivo
from services import obtener_tarjetas_por_usuario
from models import Transaccion, Usuario, Tarjeta, TarjetaUsuario
from decimal import Decimal, InvalidOperation


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
        db.session.query(
            func.round(
                func.sum(Transaccion.cantidad), 2
            )  # Redondeo a 2 decimales en SQL
        )
        .filter(
            Transaccion.id_cartera_enviado == usuario_actual.cartera.id,
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
        return redirect(url_for("auth.login"))

    error_transferencia = ""
    hoy = datetime.now()

    # --- GASTOS MENSUALES ---
    # Suma las transacciones ENVIADAS por el usuario en el mes y año actual
    gastos_mensuales = (
        db.session.query(
            func.round(
                func.sum(Transaccion.cantidad), 2
            )  # Redondeo a 2 decimales en SQL
        )
        .filter(
            Transaccion.id_cartera_enviado == usuario_actual.cartera.id,
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

    if request.method == "POST":
        nombre_destino = request.form.get("usu_transferir")
        cantidad_raw = request.form.get("cantidad_transferir")

        try:
            cantidad = Decimal(cantidad_raw)
        except (InvalidOperation, TypeError):
            error_transferencia = "Cantidad inválida"
            return render_template(
                "cuenta/transferir.html",
                usuario=usuario_actual,
                error_transferencia=error_transferencia,
            )

        if cantidad <= 0:
            error_transferencia = "La cantidad debe ser mayor que 0"
        else:
            usuario_destino = Usuario.query.filter_by(nombre=nombre_destino).first()

            if not usuario_destino or not usuario_destino.cartera:
                error_transferencia = "El usuario destino no existe"
            elif cantidad > usuario_actual.cartera.cantidad:
                error_transferencia = "No tienes saldo suficiente"
            else:
                usuario_actual.cartera.cantidad -= cantidad
                usuario_destino.cartera.cantidad += cantidad

                transaccion = Transaccion(
                    cantidad=float(cantidad),
                    id_cartera_enviado=usuario_actual.cartera.id,
                    id_cartera_recibido=usuario_destino.cartera.id,
                )

                db.session.add(transaccion)
                db.session.commit()

                error_transferencia = (
                    f"Transferencia realizada con éxito a {usuario_destino.nombre}"
                )

    return render_template(
        "cuenta/transferir.html",
        usuario=usuario_actual,
        mes_actual=mes_actual,
        gastos_mensuales=gastos_mensuales,
        error_transferencia=error_transferencia,
    )


# ingresar
# =================================== INGRESAR DINERO ================================= #


@main_bp.route("/ingresar", methods=["GET", "POST"])
def ingresar_dinero():
    usuario_actual = obtener_usuario_actual()
    if not usuario_actual:
        return redirect(url_for("auth.login"))

    tarjetas = obtener_tarjetas_por_usuario(usuario_actual.id)

    error_transferencia = ""
    error_tarjeta = ""

    if request.method == "POST":
        if "ingresartarjeta" in request.form:
            try:
                cantidad = Decimal(request.form.get("cantidad_transferir"))
                id_tarjeta = request.form.get("tarjeta_destino")

                if not id_tarjeta:
                    error_tarjeta = "Debes seleccionar una tarjeta"
                elif cantidad <= 0:
                    error_tarjeta = "La cantidad debe ser mayor a 0"
                elif cantidad > usuario_actual.cartera.cantidad:
                    error_tarjeta = "No tienes suficiente dinero en tu cartera"
                else:
                    tarjeta = (
                        db.session.query(Tarjeta)
                        .join(TarjetaUsuario)
                        .filter(
                            Tarjeta.id == int(id_tarjeta),
                            TarjetaUsuario.id_usuario == usuario_actual.id,
                        )
                        .first()
                    )

                    if not tarjeta:
                        error_tarjeta = "Tarjeta no encontrada o no es tuya"
                    else:
                        tarjeta.saldo = Decimal(tarjeta.saldo or 0)
                        usuario_actual.cartera.cantidad -= cantidad
                        tarjeta.saldo += cantidad

                        transaccion = Transaccion(
                            cantidad=float(cantidad),
                            id_cartera_enviado=usuario_actual.cartera.id,
                            id_cartera_recibido=usuario_actual.cartera.id,
                        )

                        db.session.add(transaccion)
                        db.session.commit()

                        error_tarjeta = (
                            f"Éxito: Se transfirieron {cantidad:.2f} € "
                            f"a la tarjeta **** **** **** {tarjeta.numero[-4:]}"
                        )
            except (InvalidOperation, TypeError):
                error_tarjeta = "Cantidad inválida"
            except Exception as e:
                db.session.rollback()
                error_tarjeta = f"Error al ingresar a la tarjeta: {str(e)}"

    return render_template(
        "cuenta/ingresar.html",
        usuario=usuario_actual,
        tarjetas=tarjetas,
        error_transferencia=error_transferencia,
        error_tarjeta=error_tarjeta,
    )


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
            (Transaccion.id_cartera_enviado == cartera_id)
            | (Transaccion.id_cartera_recibido == cartera_id)
        )
        .order_by(Transaccion.fecha.desc())
        .all()
    )

    # Preparar datos para la tabla
    historial = []
    for t in transacciones:
        tipo = "Enviado" if t.id_cartera_enviado == cartera_id else "Recibido"
        otra_parte_id = (
            t.id_cartera_recibido if tipo == "Enviado" else t.id_cartera_enviado
        )

        # Buscar el nombre del usuario receptor/emisor
        otra_cartera = (
            db.session.query(Usuario)
            .join(Usuario.cartera)
            .filter(Usuario.cartera.has(id=otra_parte_id))
            .first()
        )
        otra_parte_nombre = otra_cartera.nombre if otra_cartera else "Desconocido"

        historial.append(
            {
                "fecha": t.fecha.strftime("%d/%m/%Y %H:%M"),
                "tipo": tipo,
                "usuario": otra_parte_nombre,
                "cantidad": f"{t.cantidad:.2f} €",
            }
        )

    return render_template(
        "cuenta/historial.html", usuario=usuario_actual, historial=historial
    )


# Tarjetas de el usuario


@main_bp.route("/mis-tarjetas")
def mis_tarjetas():
    usuario_actual = obtener_usuario_actual()
    if not usuario_actual:
        return redirect(url_for("auth.login"))

    # 🔹 IDs de tarjetas a las que tiene acceso este usuario
    ids_tarjetas = (
        db.session.query(TarjetaUsuario.id_tarjeta)
        .filter_by(id_usuario=usuario_actual.id)
        .distinct()
        .all()
    )
    ids_tarjetas = [id[0] for id in ids_tarjetas]  # extraer de la tupla

    if not ids_tarjetas:
        tarjetas = []
    else:
        # 🔹 Traer solo las tarjetas
        tarjetas_obj = (
            db.session.query(Tarjeta).filter(Tarjeta.id.in_(ids_tarjetas)).all()
        )

        tarjetas = []
        for tarjeta in tarjetas_obj:
            caducidad_str = (
                tarjeta.caducidad
                if isinstance(tarjeta.caducidad, str)
                else tarjeta.caducidad.strftime("%m/%Y") if tarjeta.caducidad else ""
            )

            tarjetas.append(
                {
                    "id": tarjeta.id,
                    "numero": tarjeta.numero,
                    "cvc": tarjeta.cvc,
                    "caducidad": caducidad_str,
                    "saldo": float(tarjeta.saldo),
                    "propietario_id": tarjeta.propietario_id,  # dueño original
                    "propietario_nombre": tarjeta.propietario_nombre,  # dueño original
                    "propia": tarjeta.propietario_id == usuario_actual.id,
                }
            )

    return render_template(
        "cuenta/mis-tarjetas.html", usuario=usuario_actual, tarjetas=tarjetas
    )
