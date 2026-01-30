from models import Usuario, Cartera, Tarjeta, Recargar, Transaccion
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

from flask import session
# from werkzeug.security import generate_password_hash, check_password_hash
from database import db

from datetime import datetime, date, timedelta

# traducir mes

def obtener_datos_grafico_ingresos(cartera_id, rango):
    hoy = datetime.now()

    query = db.session.query(
        Transaccion.fecha,
        func.sum(Transaccion.cantidad)
    ).filter(Transaccion.id_cartera_recibido == cartera_id)

    formato_fecha_sql = '%Y-%m-%d'  # Formato para agrupar en SQL (SQLite)
    formato_strftime = '%d %B'      # Formato por defecto para mostrar (inglés)

    if rango == "semanal":
        # FILTRO CORREGIDO: Inicio de la semana (Lunes, asumiendo weekday()=0 es Lunes)
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        query = query.filter(Transaccion.fecha >= inicio_semana).group_by(func.date(Transaccion.fecha))
        formato_strftime = "%A" # Nombre completo del día en inglés

    elif rango == "anual":
        # FILTRO CORREGIDO: Inicio del año (1 de Enero del año actual)
        inicio_year = datetime(hoy.year, 1, 1)
        query = query.filter(Transaccion.fecha >= inicio_year).group_by(func.strftime('%Y-%m', Transaccion.fecha))
        formato_fecha_sql = '%Y-%m'
        formato_strftime = "%B" # Nombre completo del mes en inglés

    else: # mensual (por defecto)
        # FILTRO CORREGIDO: Inicio del mes (Día 1 del mes actual)
        inicio_mes = datetime(hoy.year, hoy.month, 1)
        query = query.filter(Transaccion.fecha >= inicio_mes).group_by(func.date(Transaccion.fecha))
        formato_strftime = "%d %B" # Día y nombre completo del mes en inglés

    resultados = query.all()

    # Lista de etiquetas traducidas (Tu lógica de traducción se mantiene intacta)
    labels_es = []
    for r in resultados:
        fecha_str_en = r[0].strftime(formato_strftime)

        if rango == "anual":
            label_traducida = traducir_mes(fecha_str_en).capitalize()
        elif rango == "semanal":
            label_traducida = traducir_dia_semana(fecha_str_en).capitalize()
        elif rango == "mensual":
            try:
                partes = fecha_str_en.split(' ')
                dia = partes[0]
                mes_en = partes[1]
                mes_es = traducir_mes(mes_en).capitalize()
                label_traducida = f"{dia} {mes_es}"
            except IndexError:
                label_traducida = fecha_str_en
        else:
            label_traducida = fecha_str_en

        labels_es.append(label_traducida)

    return {
        "labels": labels_es,
        "values": [float(r[1]) for r in resultados]
    }


# ... (Imports necesarios) ...
# from datetime import datetime, date, timedelta
# from sqlalchemy import func
from models.models import Transaccion, db
# from .services import traducir_mes, traducir_dia_semana # o como las tengas importadas
def obtener_datos_grafico_movimientos(cartera_id, rango):
    hoy = datetime.now()

    # 1. Definir filtros y formatos según el rango
    if rango == "semanal":
        inicio = hoy - timedelta(days=hoy.weekday())
        group_by_sql = func.date(Transaccion.fecha)
        formato_strftime = "%A"
    elif rango == "anual":
        inicio = datetime(hoy.year, 1, 1)
        group_by_sql = func.strftime('%Y-%m', Transaccion.fecha)
        formato_strftime = "%B"
    else:  # mensual
        inicio = datetime(hoy.year, hoy.month, 1)
        group_by_sql = func.date(Transaccion.fecha)
        formato_strftime = "%d %B"

    # 2. Consulta de INGRESOS (Sumamos)
    q_ingresos = db.session.query(
        group_by_sql.label('fecha'),
        func.sum(Transaccion.cantidad)
    ).filter(
        Transaccion.id_cartera_recibido == cartera_id,
        Transaccion.fecha >= inicio
    ).group_by('fecha').all()

    # 3. Consulta de GASTOS (Restaremos)
    q_gastos = db.session.query(
        group_by_sql.label('fecha'),
        func.sum(Transaccion.cantidad)
    ).filter(
        Transaccion.id_cartera_enviado == cartera_id,
        Transaccion.fecha >= inicio
    ).group_by('fecha').all()

    # 4. Combinar en un diccionario de balances {fecha: ingresos - gastos}
    balances = {}

    for fecha, total in q_ingresos:
        balances[fecha] = float(total)

    for fecha, total in q_gastos:
        # Si la fecha ya existe (hubo ingresos), restamos el gasto.
        # Si no existe, lo inicializamos como negativo.
        balances[fecha] = balances.get(fecha, 0.0) - float(total)

    # 5. Generar listas finales ordenadas por fecha
    fechas_ordenadas = sorted(balances.keys())

    labels_es = []
    values_netos = []

    for f_clave in fechas_ordenadas:
        # --- Lógica de etiquetas (IDÉNTICA A TU FUNCIÓN DE INGRESOS) ---
        if hasattr(f_clave, 'strftime'):
            fecha_str_en = f_clave.strftime(formato_strftime)
        else:
            # Para SQLite strftime en rango anual
            if rango == "anual":
                dt_obj = datetime.strptime(f_clave, '%Y-%m')
                fecha_str_en = dt_obj.strftime(formato_strftime)
            else:
                fecha_str_en = f_clave

        if rango == "anual":
            label = traducir_mes(fecha_str_en).capitalize()
        elif rango == "semanal":
            label = traducir_dia_semana(fecha_str_en).capitalize()
        elif rango == "mensual":
            try:
                partes = fecha_str_en.split(' ')
                dia = partes[0]
                mes_es = traducir_mes(partes[1]).capitalize()
                label = f"{dia} {mes_es}"
            except: label = fecha_str_en
        else:
            label = fecha_str_en

        labels_es.append(label)
        values_netos.append(balances[f_clave])

    # El retorno es exactamente igual al que espera tu JS
    return {
        "labels": labels_es,
        "values": values_netos
    }
