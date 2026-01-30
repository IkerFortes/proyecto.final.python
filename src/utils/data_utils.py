from datetime import datetime, timedelta

from sqlalchemy import func

from models import Cartera, Transaccion

from database import db
from .translate_utils import traducir_mes, traducir_dia_semana

import re


def obtener_datos_grafico_saldo_evolutivo(cartera_id, rango):
    hoy = datetime.now()

    # 1. Obtener el saldo actual real de la cartera
    cartera = Cartera.query.get(cartera_id)
    saldo_actual = float(cartera.cantidad) if cartera else 0.0

    # 2. Configuración de filtros y formatos según el rango
    if rango == "semanal":
        inicio = hoy - timedelta(days=hoy.weekday())
        group_by_sql = func.date(Transaccion.fecha)
        formato_strftime = "%A"
    elif rango == "anual":
        inicio = datetime(hoy.year, 1, 1)
        group_by_sql = func.strftime("%Y-%m", Transaccion.fecha)
        formato_strftime = "%B"
    else:  # mensual (por defecto)
        inicio = datetime(hoy.year, hoy.month, 1)
        group_by_sql = func.date(Transaccion.fecha)
        formato_strftime = "%d %B"

    # 3. Consultas de movimientos en el periodo
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

    # 4. Calcular balances por fecha y el total neto del periodo
    balances_periodo = {}
    total_neto_periodo = 0.0

    for f, cant in q_ingresos:
        val = float(cant)
        balances_periodo[f] = balances_periodo.get(f, 0.0) + val
        total_neto_periodo += val

    for f, cant in q_gastos:
        val = float(cant)
        balances_periodo[f] = balances_periodo.get(f, 0.0) - val
        total_neto_periodo -= val

    # 5. Calcular el saldo inicial (Saldo antes de los movimientos del gráfico)
    # Saldo Inicial = Saldo Hoy - Suma de lo que entró/salió en este periodo
    saldo_acumulado = saldo_actual - total_neto_periodo

    # 6. Generar listas finales ordenadas cronológicamente
    fechas_ordenadas = sorted(balances_periodo.keys())

    labels_es = []
    values_evolucion = []

    for f_clave in fechas_ordenadas:
        # El saldo del día es el acumulado anterior + el neto de este día
        saldo_acumulado += balances_periodo[f_clave]
        values_evolucion.append(round(saldo_acumulado, 2))

        # --- Lógica de etiquetas y traducción ---
        if hasattr(f_clave, "strftime"):  # Si es objeto date/datetime
            fecha_str_en = f_clave.strftime(formato_strftime)
        else:
            # Si es string (caso anual de SQLite 'YYYY-MM')
            if rango == "anual":
                dt_obj = datetime.strptime(f_clave, "%Y-%m")
                fecha_str_en = dt_obj.strftime(formato_strftime)
            else:
                fecha_str_en = f_clave

        # Traducción de etiquetas
        if rango == "anual":
            label = traducir_mes(fecha_str_en)
        elif rango == "semanal":
            label = traducir_dia_semana(fecha_str_en)
        elif rango == "mensual":
            try:
                partes = fecha_str_en.split(" ")
                dia = partes[0]
                mes_es = traducir_mes(partes[1])
                label = f"{dia} {mes_es}"
            except:
                label = fecha_str_en
        else:
            label = fecha_str_en

        labels_es.append(label)

    return {"labels": labels_es, "values": values_evolucion}


def validar_datos_tarjeta_form(propietario, numero, dia, mes, cvc):
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
