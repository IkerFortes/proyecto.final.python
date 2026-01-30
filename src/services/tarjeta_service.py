# from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import db  # Tu conexión a DB
from models import Tarjeta  # Tu modelo de Tarjeta

# from werkzeug.security import generate_password_hash, check_password_hash
# from services.auth_service import hash_password


def obtener_tarjetas_por_usuario(id_usuario: int):
    tarjetas = db.session.query(Tarjeta).filter(Tarjeta.id_usuario == id_usuario).all()

    if not tarjetas:
        return None

    return tarjetas


def registrada_tarjeta(tarjeta_data, id_usuario):
    # 'tarjeta_data' es el objeto/diccionario que recibes.
    # Debes acceder a su propiedad '.numero'
    existe = (
        db.session.query(Tarjeta)
        .filter(Tarjeta.numero == tarjeta_data.numero, Tarjeta.id_usuario == id_usuario)
        .first()
    )  # .first() es más eficiente que .all() para verificar existencia

    return existe is not None


# def aniadir_tarjeta(tarjeta):
