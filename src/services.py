# Ya no importamos SessionLocal ni engine
from database import db

from models import Usuario, Cartera, Tarjeta, RellenarMonedero, Transaccion
from sqlalchemy.exc import SQLAlchemyError


def registrar_usuario(dni, nombre, apellidos, username, password, email):
    # Ya no necesitamos session = SessionLocal() ni session.close()
    try:
        nuevo_usuario = Usuario(
            dni=dni,
            nombre=nombre,
            apellidos=apellidos,
            usuario=username,
            contrasena=password,
            gmail=email,
        )
        # Usamos db.session
        db.session.add(nuevo_usuario)
        db.session.flush()

        nueva_cartera = Cartera(id_usuario=nuevo_usuario.id, cantidad=0.0)
        db.session.add(nueva_cartera)

        db.session.commit()
        return nuevo_usuario.id
    except SQLAlchemyError as e:
        db.session.rollback()  # Seguimos necesitando el rollback
        print(f"Error al registrar: {e}")
        return None


# Refactoriza el resto de las funciones de services.py para usar db.session.add,
# db.session.commit, db.session.rollback y db.session.query()
