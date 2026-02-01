# from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database import db  # Tu conexión a DB
from models import Tarjeta, TarjetaUsuario, Usuario  # Tu modelo de Tarjeta

# from werkzeug.security import generate_password_hash, check_password_hash
# from services.auth_service import hash_password

def obtener_tarjetas_por_usuario(id_usuario):
    """
    Devuelve todas las tarjetas asociadas a un usuario a través de TarjetaUsuario.
    Convierte la caducidad a un formato legible 'MM/YYYY'.
    """
    tarjetas_query = (
        db.session.query(Tarjeta, TarjetaUsuario, Usuario)
        .join(TarjetaUsuario, Tarjeta.id == TarjetaUsuario.id_tarjeta)
        .join(Usuario, TarjetaUsuario.id_usuario == Usuario.id)
        .filter(TarjetaUsuario.id_usuario == id_usuario)
        .all()
    )

    tarjetas = []
    for tarjeta, relacion, propietario in tarjetas_query:
        # Si caducidad es string en DB, no usar strftime
        caducidad_formateada = tarjeta.caducidad if tarjeta.caducidad else ""
        tarjetas.append({
            "id": tarjeta.id,
            "numero": tarjeta.numero,
            "cvc": tarjeta.cvc,
            "caducidad": caducidad_formateada,
            "saldo": float(tarjeta.saldo),
            "propietario_id": propietario.id,
            "propietario_nombre": propietario.nombre,
            "propia": propietario.id == id_usuario
        })

    return tarjetas



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


def guardar_tarjeta_en_db(tarjeta: Tarjeta, id_usuario_propietario: int) -> str | None:
    """
    Persiste una nueva tarjeta en la base de datos y asocia al usuario propietario
    en la tabla TarjetaUsuario.
    
    Args:
        tarjeta (Tarjeta): Objeto Tarjeta a guardar.
        id_usuario_propietario (int): ID del usuario que añade la tarjeta.

    Returns:
        str | None: None si todo OK, mensaje de error si falla.
    """
    try:
        # Guardamos la tarjeta
        db.session.add(tarjeta)
        db.session.flush()  # Necesario para obtener el ID de la tarjeta antes del commit

        # Creamos la relación en TarjetaUsuario
        relacion = TarjetaUsuario(id_usuario=id_usuario_propietario, id_tarjeta=tarjeta.id)
        db.session.add(relacion)

        db.session.commit()
        return None
    except SQLAlchemyError as e:
        db.session.rollback()
        return str(e)