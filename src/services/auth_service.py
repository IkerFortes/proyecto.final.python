from werkzeug.security import generate_password_hash, check_password_hash
from flask import session

from models import Usuario

# --- FUNCIONES DE CONTROL DE ACCESO ---


def login_usuario(identificador, password):
    """
    Autentica a un usuario mediante sus credenciales y gestiona el inicio de sesión.

    Busca coincidencias en la base de datos tanto por nombre de usuario como por
    correo electrónico. Si las credenciales son válidas, inicializa la sesión.

    Args:
        identificador (str): El nombre de usuario o dirección de correo electrónico.
        password (str): La contraseña en texto plano para validar contra el hash.

    Returns:
        Usuario | None: El objeto de la clase Usuario si la autenticación es
            exitosa; None si el usuario no existe o la contraseña es incorrecta.

    Example:
        >>> user = login_usuario("paco_admin", "12345")
        >>> if user:
        ...     print(f"Bienvenido {session['nombre']}")
        "Bienvenido Paco"
    """

    # Buscamos por usuario o por gmail para dar flexibilidad al login
    usuario = Usuario.query.filter(
        (Usuario.usuario == identificador) | (Usuario.gmail == identificador)
    ).first()

    if usuario and check_password_hash(usuario.contrasena, password):
        # Guardamos datos mínimos en la sesión (cookie encriptada)
        session.clear()
        session["usuario_id"] = usuario.id
        session["nombre"] = usuario.nombre
        return usuario
    return None


def logout_usuario():
    """
    Finaliza la sesión del usuario actual eliminando todos los datos almacenados.

    Borra de forma segura todas las variables de contexto de la sesión activa,
    forzando al sistema a tratar al usuario como no autenticado.

    Args:
        Ninguno (opera directamente sobre el objeto flask.session).

    Returns:
        None: No devuelve ningún valor, simplemente limpia el estado de la sesión.

    Example:
        >>> session["usuario_id"] = 123
        >>> logout_usuario()
        >>> print(len(session))
        0
    """

    session.clear()


def esta_autenticado():
    """
    Verifica si existe una sesión activa para un usuario en el contexto actual.

    Comprueba la presencia de la clave identificadora en el objeto de sesión
    para determinar si el cliente ha pasado por el proceso de login.

    Args:
        Ninguno (accede al estado de flask.session).

    Returns:
        bool: True si el identificador de usuario existe en la sesión,
            False en caso contrario.

    Example:
        >>> if esta_autenticado():
        ...     print("Acceso concedido")
        ... else:
        ...     print("Redirigiendo al login...")
    """

    return "usuario_id" in session


# --- 2. FUNCIONES DE SEGURIDAD DE CUENTA ---


def hash_password(password_plano):
    """
    Transforma una contraseña en texto plano en un hash seguro y único.

    Utiliza el algoritmo de derivación de claves PBKDF2 con SHA256 y un
    salt aleatorio para proteger las credenciales contra ataques de fuerza bruta.

    Args:
        password_plano (str): La contraseña original proporcionada por el usuario.

    Returns:
        str: Una cadena de texto (hash) que representa la contraseña de forma irreversible.

    Example:
        >>> hash_password("mi_clave_secreta")
        'pbkdf2:sha256:600000$u8X9...hash_generado'
    """

    return generate_password_hash(password_plano, method="pbkdf2:sha256")


# --- 3. FUNCIONES DE RECUPERACIÓN Y VALIDACIÓN ---


def verificar_disponibilidad(nombre_usuario, gmail):
    """
    Comprueba si las credenciales de identidad ya están registradas en el sistema.

    Realiza una consulta en la base de datos para asegurar que no existan
    duplicados de identidad (username) o de contacto (email).

    Args:
        nombre_usuario (str): El nombre de usuario que se desea verificar.
        gmail (str): La dirección de correo electrónico a validar.

    Returns:
        tuple[bool, str]: Una tupla que contiene un booleano (True si está libre,
            False si está ocupado) y un mensaje descriptivo del estado.

    Example:
        >>> disponible, msj = verificar_disponibilidad("juanito123", "juan@mail.com")
        >>> if not disponible:
        ...     print(msj)
        "El nombre de usuario ya está en uso."
    """

    if Usuario.query.filter_by(usuario=nombre_usuario).first():
        return False, "El nombre de usuario ya está en uso."
    if Usuario.query.filter_by(gmail=gmail).first():
        return False, "El correo electrónico ya está registrado."
    return True, "Disponible"


def generar_token_recuperacion(gmail):
    """
    Genera un identificador único para el proceso de restablecimiento de contraseña.

    Verifica la existencia del usuario y crea un token seguro mediante la
    librería secrets para garantizar alta entropía.

    Args:
        gmail (str): Dirección de correo electrónico del usuario que solicita
            la recuperación.

    Returns:
        str | None: Una cadena de texto segura de tipo URL-safe si el usuario
            existe; de lo contrario, devuelve None.

    Example:
        >>> token = generar_token_recuperacion("usuario@ejemplo.com")
        >>> print(token)
        '7n8zX_J-8WqP4mY9Lz2_vQ8S7aD5fG3hJ1kL0mN9pB4'
    """

    import secrets

    usuario = Usuario.query.filter_by(gmail=gmail).first()
    if usuario:
        token = secrets.token_urlsafe(32)
        # Aquí guardarías el token en una tabla de 'Tokens' con fecha de expiración
        return token
    return None
