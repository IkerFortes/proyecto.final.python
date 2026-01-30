# from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database import db  # Tu conexión a DB
from models import Tarjeta  # Tu modelo de Tarjeta

# from werkzeug.security import generate_password_hash, check_password_hash
# from services.auth_service import hash_password


def obtener_tarjetas_por_usuario(id_usuario: int):
    return db.session.query(Tarjeta).filter(Tarjeta.id_usuario == id_usuario).all()


def registrada_tarjeta(tarjeta_data: Tarjeta):
    # 'tarjeta_data' es el objeto/diccionario que recibes.
    # Debes acceder a su propiedad '.numero'
    existe = (
        db.session.query(Tarjeta).filter(Tarjeta.numero == tarjeta_data.numero).first()
    )

    return existe is not None


def guardar_tarjeta_en_db(tarjeta: Tarjeta) -> str | None:
    """
    Añade una tarjeta a la base de datos.
    Devuelve None si tiene éxito, o el mensaje de error como string si falla.
    """
    try:
        db.session.add(tarjeta)
        db.session.commit()
        return None  # Éxito: no devuelve mensaje de error
    except SQLAlchemyError as e:
        db.session.rollback()
        # Devuelve el mensaje de error específico de SQLAlchemy
        return str(e)
