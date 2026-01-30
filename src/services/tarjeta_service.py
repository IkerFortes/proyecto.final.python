# from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database import db  # Tu conexión a DB
from models import Tarjeta  # Tu modelo de Tarjeta

# from werkzeug.security import generate_password_hash, check_password_hash
# from services.auth_service import hash_password


def obtener_tarjetas_por_usuario(id_usuario: int):
    """
    Recupera el listado completo de tarjetas vinculadas a un usuario específico.

    Args:
        id_usuario (int): El identificador único del usuario en la base de datos.

    Returns:
        list[Tarjeta]: Una lista de objetos Tarjeta asociados al ID proporcionado.
            Devuelve una lista vacía si no existen registros.

    Example:
        >>> tarjetas = obtener_tarjetas_por_usuario(5)
        >>> print(len(tarjetas))
        2
    """

    return db.session.query(Tarjeta).filter(Tarjeta.id_usuario == id_usuario).all()


def registrada_tarjeta(tarjeta_data: Tarjeta):
    """
    Verifica si un número de tarjeta ya existe en el sistema para evitar duplicados.

    Args:
        tarjeta_data (Tarjeta): Instancia del modelo Tarjeta que contiene los
            datos a validar (específicamente el atributo número).

    Returns:
        bool: True si el número de tarjeta ya está registrado, False en caso contrario.

    Example:
        >>> nueva_t = Tarjeta(numero="1234567890123456")
        >>> if registrada_tarjeta(nueva_t):
        ...     print("Error: Tarjeta duplicada")
    """

    existe = (
        db.session.query(Tarjeta).filter(Tarjeta.numero == tarjeta_data.numero).first()
    )

    return existe is not None


def guardar_tarjeta_en_db(tarjeta: Tarjeta) -> str | None:
    """
    Persiste una nueva tarjeta en la base de datos de forma segura.

    Gestiona la transacción atómica, realizando un commit si los datos son
    válidos o un rollback en caso de error de integridad o conexión.

    Args:
        tarjeta (Tarjeta): El objeto instancia de Tarjeta que se desea guardar.

    Returns:
        str | None: None si la operación es exitosa. En caso de fallo, devuelve
            una cadena de texto con la descripción del error.

    Example:
        >>> error = guardar_tarjeta_en_db(mi_tarjeta)
        >>> if error:
        ...     print(f"No se pudo guardar: {error}")
    """

    try:
        db.session.add(tarjeta)
        db.session.commit()
        return None  # Éxito: no devuelve mensaje de error
    except SQLAlchemyError as e:
        db.session.rollback()
        # Devuelve el mensaje de error específico de SQLAlchemy
        return str(e)