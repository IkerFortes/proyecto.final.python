def traducir_mes(mes_ingles):
    """
    Traduce el nombre de un mes de inglés a castellano.
    Ejemplo: 'January' -> 'Enero'
    """
    MESES_MAP = {
        "January": "Enero",
        "February": "Febrero",
        "March": "Marzo",
        "April": "Abril",
        "May": "Mayo",
        "June": "Junio",
        "July": "Julio",
        "August": "Agosto",
        "September": "Septiembre",
        "October": "Octubre",
        "November": "Noviembre",
        "December": "Diciembre",
    }

    # Verificar si la entrada es válida antes de intentar .title() y .get()
    if not isinstance(mes_ingles, str):
        return ""  # Devolvemos una cadena vacía si no es un string válido

    # Usamos .get() con una cadena vacía como valor por defecto si no se encuentra
    traduccion = MESES_MAP.get(mes_ingles.title(), "")

    # Ahora sí podemos aplicar .capitalize() de forma segura
    return traduccion.capitalize()


def traducir_dia_semana(dia_ingles):
    """
    Traduce el nombre completo de un día de la semana de inglés a castellano.
    Ejemplo: 'Monday' -> 'Lunes'
    """
    DIAS_MAP = {
        "Monday": "Lunes",
        "Tuesday": "Martes",
        "Wednesday": "Miércoles",
        "Thursday": "Jueves",
        "Friday": "Viernes",
        "Saturday": "Sábado",
        "Sunday": "Domingo",
    }

    # Verificar si la entrada es válida antes de intentar usarla
    if not isinstance(dia_ingles, str):
        return ""  # Devolvemos una cadena vacía si no es un string

    # Usamos .get() con una cadena vacía como valor por defecto si no se encuentra
    # También aplicamos .title() a la entrada para manejar mayúsculas/minúsculas
    traduccion = DIAS_MAP.get(dia_ingles.title(), "")

    # Ahora sí podemos aplicar .capitalize() de forma segura
    return traduccion.capitalize()
