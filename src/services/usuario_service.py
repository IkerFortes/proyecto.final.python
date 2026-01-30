from models import Usuario, Cartera

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from services.auth_service import hash_password


# --- REGISTRO DE USUARIO --- #
def crear_usuario(datos):
    """
    Orquestra el registro de un nuevo usuario junto con su cartera inicial.

    Realiza el hasheo de seguridad y crea una relación uno a uno con una
    nueva instancia de Cartera con saldo inicial cero.

    Args:
        datos (dict): Diccionario con las claves 'dni', 'nombre', 'apellidos',
            'usuario', 'contrasena' y 'gmail'.

    Returns:
        tuple[bool, str]: Un booleano indicando el éxito y un mensaje descriptivo.

    Example:
        >>> exito, msj = crear_usuario({"usuario": "paco", "contrasena": "123", ...})
        >>> if exito:
        ...     print("Usuario creado")
    """

    try:
        # 1. Hashear la contraseña
        password_hashed = generate_password_hash(
            datos["contrasena"], method="pbkdf2:sha256"
        )

        # 2. Crear instancia de Usuario
        nuevo_usuario = Usuario(
            dni=datos["dni"],  # type: ignore
            nombre=datos["nombre"],  # type: ignore
            apellidos=datos["apellidos"],  # type: ignore
            usuario=datos["usuario"],  # type: ignore
            contrasena=password_hashed,  # type: ignore
            gmail=datos["gmail"],  # type: ignore
        )

        # 3. Crear Cartera asociada (saldo 0 por defecto)
        nueva_cartera = Cartera(cantidad=0.0, propietario=nuevo_usuario)  # type: ignore

        db.session.add(nuevo_usuario)
        db.session.add(nueva_cartera)

        # 4. Guardar en base de datos
        db.session.commit()
        return True, "Registro completado con éxito."

    except Exception as e:
        db.session.rollback()  # Si algo falla, deshace los cambios
        return False, f"Error al registrar: {str(e)}"


def actualizar_contrasena(usuario_id, password_antiguo, nuevo_password):
    """
    Modifica la credencial de acceso tras validar la identidad del usuario.

    Args:
        usuario_id (int): ID único del usuario a modificar.
        password_antiguo (str): Contraseña actual para verificar propiedad.
        nuevo_password (str): Nueva contraseña en texto plano.

    Returns:
        bool: True si la validación y el cambio fueron exitosos, False en caso contrario.

    Example:
        >>> if actualizar_contrasena(1, "vieja123", "nueva456"):
        ...     print("Contraseña actualizada")
    """

    usuario = Usuario.query.get(usuario_id)
    if usuario and check_password_hash(usuario.contrasena, password_antiguo):
        usuario.contrasena = hash_password(nuevo_password)
        db.session.commit()
        return True
    return False


# --- OBTENER PERFIL --- #
def obtener_perfil_completo(usuario_id):
    """
    Recupera la entidad Usuario incluyendo sus relaciones cargadas.

    Args:
        usuario_id (int): Identificador del usuario a consultar.

    Returns:
        Usuario | None: Objeto Usuario con acceso a .cartera y .tarjetas,
            o None si no existe.

    Example:
        >>> user = obtener_perfil_completo(1)
        >>> print(user.cartera.cantidad)
    """

    return Usuario.query.get(usuario_id)


def obtener_usuario_actual():
    """
    Obtiene el objeto Usuario del usuario que tiene la sesión iniciada.

    Returns:
        Usuario | None: La instancia del usuario logueado extraída de la BD
            según el ID de la sesión de Flask.

    Example:
        >>> actual = obtener_usuario_actual()
        >>> if actual:
        ...     print(f"Hola de nuevo, {actual.nombre}")
    """

    usuario_id = session.get("usuario_id")
    if usuario_id:
        return Usuario.query.get(usuario_id)
    return None
