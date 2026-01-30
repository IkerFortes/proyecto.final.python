from datetime import datetime, timedelta

from sqlalchemy import func

from models import Cartera, Transaccion

from database import db
from .translate_utils import traducir_mes, traducir_dia_semana

import re

import calendar


def obtener_datos_grafico_saldo_evolutivo(cartera_id, rango):
    """
    Genera la serie temporal del saldo para gráficos, garantizando ejes X completos.

    Calcula la evolución del saldo partiendo del estado actual y reconstruyendo
    hacia atrás. Maneja años bisiestos (febrero) y oculta datos de periodos futuros.

    Args:
        cartera_id (int): Identificador de la cartera en la base de datos.
        rango (str): Escala del gráfico: 'semanal' (7 días), 'anual' (12 meses)
            o 'mensual' (días del mes actual).

    Returns:
        dict: Diccionario con 'labels' (etiquetas en español) y 'values'
            (saldos acumulados o None para el futuro).

    Example:
        >>> data = obtener_datos_grafico_saldo_evolutivo(1, "semanal")
        >>> print(data['values'])  # [150.5, 160.0, 140.2, None, None, None, None]
    """
    hoy = datetime.now()
    cartera = Cartera.query.get(cartera_id)
    saldo_actual = float(cartera.cantidad) if cartera else 0.0

    # 1. Configuración de periodos y etiquetas
    puntos_tiempo = []  # Lista de tuplas (clave_comparacion, etiqueta_es)

    if rango == "semanal":
        # Lunes de la semana actual a las 00:00
        inicio = (hoy - timedelta(days=hoy.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        for i in range(7):
            f = (inicio + timedelta(days=i)).date()
            puntos_tiempo.append((f, traducir_dia_semana(f.strftime("%A"))))

    elif rango == "anual":
        # Los 12 meses del año actual
        inicio = datetime(hoy.year, 1, 1)
        for m in range(1, 13):
            # Formato 'YYYY-MM' para compatibilidad con SQLite/SQLAlchemy
            clave = f"{hoy.year}-{m:02d}"
            nombre_mes = datetime(hoy.year, m, 1).strftime("%B")
            puntos_tiempo.append((clave, traducir_mes(nombre_mes)))

    else:  # mensual (por defecto)
        # Todos los días del mes actual (maneja bisiestos automáticamente)
        inicio = datetime(hoy.year, hoy.month, 1)
        _, ultimo_dia = calendar.monthrange(hoy.year, hoy.month)
        for d in range(1, ultimo_dia + 1):
            f = datetime(hoy.year, hoy.month, d).date()
            etiqueta = f"{d} {traducir_mes(f.strftime('%B'))}"
            puntos_tiempo.append((f, etiqueta))

    # 2. Consultas de transacciones desde el punto de inicio
    group_by_sql = (
        func.strftime("%Y-%m", Transaccion.fecha)
        if rango == "anual"
        else func.date(Transaccion.fecha)
    )

    q_ingresos = (
        db.session.query(group_by_sql.label("f"), func.sum(Transaccion.cantidad))
        .filter(
            Transaccion.id_cartera_recibido == cartera_id, Transaccion.fecha >= inicio
        )
        .group_by("f")
        .all()
    )

    q_gastos = (
        db.session.query(group_by_sql.label("f"), func.sum(Transaccion.cantidad))
        .filter(
            Transaccion.id_cartera_enviado == cartera_id, Transaccion.fecha >= inicio
        )
        .group_by("f")
        .all()
    )

    # 3. Mapeo de balances netos por fecha
    balances_periodo = {}
    for f, cant in q_ingresos:
        balances_periodo[f] = balances_periodo.get(f, 0.0) + float(cant)
    for f, cant in q_gastos:
        balances_periodo[f] = balances_periodo.get(f, 0.0) - float(cant)

    # 4. Cálculo del saldo inicial (Saldo hoy - Suma de movimientos en el gráfico)
    total_neto_periodo = sum(balances_periodo.values())
    saldo_acumulado = saldo_actual - total_neto_periodo

    # 5. Construcción del resultado final cruzando calendario vs datos
    labels_es = []
    values_evolucion = []

    for clave, etiqueta in puntos_tiempo:
        labels_es.append(etiqueta)

        # Verificar si el periodo es futuro
        es_futuro = False
        if rango == "anual":
            # clave es "YYYY-MM", comparamos el mes
            mes_punto = int(clave.split("-")[1])
            if mes_punto > hoy.month:
                es_futuro = True
        else:
            # clave es objeto date
            if clave > hoy.date():
                es_futuro = True

        if es_futuro:
            values_evolucion.append(None)  # Evita pintar barritas/líneas en el futuro
        else:
            # Si es string (anual), SQLite devuelve 'YYYY-MM', si es date (semanal/mensual) comparamos tal cual
            key = str(clave) if rango == "anual" else clave.isoformat()
            # Ajuste de clave para el diccionario balances_periodo
            movimiento = balances_periodo.get(key, 0.0) or balances_periodo.get(
                clave, 0.0
            )

            saldo_acumulado += movimiento
            values_evolucion.append(round(saldo_acumulado, 2))

    return {"labels": labels_es, "values": values_evolucion}


def validar_datos_tarjeta_form(propietario, numero, dia, mes, cvc):
    """
    Valida la integridad y formato de los datos de una tarjeta bancaria.

    Aplica reglas de negocio y expresiones regulares para evitar errores
    de base de datos y asegurar datos coherentes.

    Args:
        propietario (str): Nombre del titular.
        numero (str): Dígitos de la tarjeta (acepta espacios/guiones).
        dia (str/int): Día de expiración.
        mes (str/int): Mes de expiración.
        cvc (str): Código de seguridad de 3 o 4 dígitos.

    Returns:
        tuple[bool, str | None]: (True, None) si es válido;
            (False, "mensaje") si falla.

    Example:
        >>> es_valido, error = validar_datos_tarjeta_form("Paco", "1234", "31", "12", "123")
        >>> if not es_valido: print(error)
        "El número de tarjeta no es válido."
    """

    # 1. Verificar que no falte ningún dato (Evita el IntegrityError: NOT NULL)
    if not all([propietario, numero, dia, mes, cvc]):
        return False, "Todos los campos son obligatorios."

    # 2. Validar Propietario
    if len(propietario.strip()) < 3:
        return False, "El nombre del propietario es demasiado corto."

    # 3. Validar Número (Solo dígitos, entre 13 y 19)
    num_clean = re.sub(r"\D", "", numero)
    if not re.match(r"^\d{13,19}$", num_clean):
        return False, "El número de tarjeta no es válido."

    # 4. Validar Fecha (Día y Mes)
    # Nota: Si el formulario pide DD/MM, validamos rangos
    try:
        d_int = int(dia)
        m_int = int(mes)
        if not (1 <= d_int <= 31 and 1 <= m_int <= 12):
            raise ValueError
    except ValueError:
        return False, "La fecha (Día/Mes) es inválida."

    # 5. Validar CVC (3 o 4 dígitos)
    if not re.match(r"^\d{3,4}$", cvc):
        return False, "El CVC debe tener 3 o 4 dígitos."

    return True, None
