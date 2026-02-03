from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from sqlalchemy import func

from models import Recargar
from database import db
from models import Transaccion, Usuario, Cartera, Tarjeta, TarjetaUsuario
from services import (
    esta_autenticado,
    obtener_usuario_actual,
    obtener_tarjetas_por_usuario
)
from utils import traducir_mes, obtener_datos_grafico_saldo_evolutivo


main_bp = Blueprint("main", __name__)


@main_bp.before_request
def verificar_sesion():
    """Verifica que el usuario esté autenticado antes de cada request.

    Redirige al login si no hay sesión activa.
    
    Returns:
        Response: Redirecciona al login si no hay sesión activa, None si está autenticado.
    """
    if not esta_autenticado():
        return redirect(url_for("auth.login"))


# =================================== PÁGINA PRINCIPAL ================================= #


@main_bp.route("/")
def index():
    """Renderiza la página de inicio mostrando los gastos mensuales del usuario.

    Calcula la suma de las transacciones enviadas por el usuario
    en el mes y año actual y obtiene el nombre del mes traducido al español.

    Returns:
        Response: Renderiza la plantilla "cuenta/index.html" pasando:
            gastos_mensuales (float): Total de gastos del mes.
            mes_actual (str): Nombre del mes actual en español.
    """
    hoy = datetime.now()
    usuario_actual = obtener_usuario_actual()

    gastos_mensuales = (
        db.session.query(
            func.round(
                func.sum(Transaccion.cantidad), 2
            )  
        )
        .filter(
            Transaccion.id_cartera_enviado == usuario_actual.cartera.id,
            func.extract("month", Transaccion.fecha) == hoy.month,
            func.extract("year", Transaccion.fecha) == hoy.year,
        )
        .scalar()
        or 0.0
    )

    mes_actual = traducir_mes(hoy.strftime("%B").capitalize())

    return render_template(
        "cuenta/index.html",
        gastos_mensuales=gastos_mensuales,
        mes_actual=mes_actual,
    )


@main_bp.route("/api/grafico/<rango>")
def api_grafico(rango):
    """Endpoint API para obtener datos del gráfico de evolución de saldo.

    Requiere autenticación. Devuelve datos formateados en JSON para ser consumidos por JavaScript.

    Args:
        rango (str): Rango de tiempo para el cual obtener los datos ('semana', 'mes', 'año').

    Returns:
        jsonify: Un objeto JSON con los datos del gráfico o un mensaje de error 401 si no está autenticado.
    """
    if not esta_autenticado():
        return jsonify({"error": "No autorizado"}), 401

    usuario_actual = obtener_usuario_actual()
    datos = obtener_datos_grafico_saldo_evolutivo(usuario_actual.cartera.id, rango)
    return jsonify(datos)


# =================================== TRANSFERENCIAS ================================= #


@main_bp.route("/transferir", methods=["GET", "POST"])
def transferencias():
    """Permite al usuario transferir dinero a otro usuario.

    Valida cantidad, existencia del usuario destino y saldo suficiente antes de realizar la transacción.
    Registra la transacción en la base de datos y muestra un mensaje de éxito o error.

    Returns:
        Response: Renderiza la plantilla "cuenta/transferir.html" pasando:
            usuario (Usuario): Usuario actualmente autenticado.
            error_transferencia (str): Mensaje de error o éxito de la transferencia.
    """
    usuario_actual = obtener_usuario_actual()
    if not usuario_actual or not usuario_actual.cartera:
        return redirect(url_for("auth.login"))

    error_transferencia = ""
    hoy = datetime.now()

    gastos_mensuales = (
        db.session.query(
            func.round(
                func.sum(Transaccion.cantidad), 2
            )  
        )
        .filter(
            Transaccion.id_cartera_enviado == usuario_actual.cartera.id,
            func.extract("month", Transaccion.fecha) == hoy.month,
            func.extract("year", Transaccion.fecha) == hoy.year,
        )
        .scalar()
        or 0.0
    )

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
                error_transferencia = f"Transferencia realizada con éxito a {usuario_destino.nombre}"

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
    """
    Permite al usuario ingresar dinero a su cartera o a una de sus tarjetas.

    Muestra la interfaz con los formularios y gestiona las operaciones
    según el botón presionado.

    Args:
        Ninguno (Flask maneja request y contexto automáticamente)

    Returns:
        render_template: La plantilla 'cuenta/ingresar.html' con los datos
        del usuario, sus tarjetas y posibles mensajes de error o éxito.
    """
    usuario_actual = obtener_usuario_actual()
    if not usuario_actual:
        return redirect(url_for("auth.login"))

    tarjetas = obtener_tarjetas_por_usuario(usuario_actual.id)
    error_transferencia = ""
    error_tarjeta = ""

    if request.method == "POST":
        # ----------------- INGRESAR A LA CARTERA -----------------
        if "ingresarcartera" in request.form:
            try:
                cantidad = Decimal(request.form.get("cantidad_transferir"))
                if cantidad <= 0:
                    error_transferencia = "La cantidad debe ser mayor a 0"
                else:
                    usuario_actual.cartera.cantidad += cantidad

                    transaccion = Transaccion(
                        cantidad=float(cantidad),
                        id_cartera_enviado=-1,
                        id_cartera_recibido=usuario_actual.cartera.id
                    )

                    db.session.add(transaccion)
                    db.session.commit()
                    error_transferencia = f"Éxito: Se ingresaron {cantidad:.2f} € a tu cartera"
            except (InvalidOperation, TypeError):
                error_transferencia = "Cantidad inválida"
            except Exception as e:
                db.session.rollback()
                error_transferencia = f"Error al ingresar dinero: {str(e)}"

        # ----------------- INGRESAR A TARJETA -----------------
        elif "ingresartarjeta" in request.form:
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

                        recarga = Recargar(
                            id_cartera=usuario_actual.cartera.id,
                            id_tarjeta=tarjeta.id,
                            cantidad=cantidad
                        )

                        db.session.add(recarga)
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


# =================================== HISTORIAL ================================= #

@main_bp.route("/historial")
def historial():
    """Renderiza la página del historial de transacciones del usuario.

    Recupera todas las transacciones donde el usuario es emisor o receptor,
    mostrando tipo de transacción, usuario contrario, fecha y cantidad.

    Returns:
        Response: Renderiza la plantilla "cuenta/historial.html" pasando:
            usuario (Usuario): Usuario actualmente autenticado.
            historial (list): Lista de transacciones con información para mostrar en tabla.
    """
    if not esta_autenticado():
        return redirect(url_for("auth.login"))

    usuario_actual = obtener_usuario_actual()
    cartera_id = usuario_actual.cartera.id

    transacciones = (
        db.session.query(Transaccion)
        .filter(
            (Transaccion.id_cartera_enviado == cartera_id)
            | (Transaccion.id_cartera_recibido == cartera_id)
        )
        .order_by(Transaccion.fecha.desc())
        .all()
    )

    historial_data = []
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

        historial_data.append({
            "fecha": t.fecha.strftime("%d/%m/%Y %H:%M"),
            "tipo": tipo,
            "usuario": otra_parte_nombre,
            "cantidad": f"{t.cantidad:.2f} €"
        })

    return render_template(
        "cuenta/historial.html",
        usuario=usuario_actual,
        historial=historial_data
    )


# Tarjetas de el usuario
# =================================== MIS TARJETAS ================================= #

@main_bp.route("/mis-tarjetas")
def mis_tarjetas():
    """Muestra todas las tarjetas asociadas al usuario actual.

    Recupera las tarjetas a las que el usuario tiene acceso, incluyendo tarjetas propias y compartidas,
    y devuelve información de cada tarjeta para renderizar en la vista.

    Returns:
        Response: Renderiza la plantilla "cuenta/mis-tarjetas.html" pasando:
            usuario (Usuario): Usuario actualmente autenticado.
            tarjetas (list): Lista de diccionarios con información de cada tarjeta.
    """
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

    ids_tarjetas = [id[0] for id in ids_tarjetas]

    tarjetas = []
    if ids_tarjetas:
        tarjetas_obj = db.session.query(Tarjeta).filter(Tarjeta.id.in_(ids_tarjetas)).all()

        for tarjeta in tarjetas_obj:
            caducidad_str = (
                tarjeta.caducidad if isinstance(tarjeta.caducidad, str)
                else tarjeta.caducidad.strftime("%m/%Y") if tarjeta.caducidad else ""
            )

            tarjetas.append({
                "id": tarjeta.id,
                "numero": tarjeta.numero,
                "cvc": tarjeta.cvc,
                "caducidad": caducidad_str,
                "saldo": float(tarjeta.saldo),
                "propietario_id": tarjeta.propietario_id,
                "propietario_nombre": tarjeta.propietario_nombre,
                "propia": tarjeta.propietario_id == usuario_actual.id
            })

    return render_template(
        "cuenta/mis-tarjetas.html", usuario=usuario_actual, tarjetas=tarjetas
    )
