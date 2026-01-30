from flask import Blueprint, render_template, request, redirect, url_for, flash
from services import login_usuario, logout_usuario, crear_usuario

auth_bp = Blueprint("auth", __name__)
# =================================== USUARIO ================================= #

# Log in #


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Maneja el proceso de inicio de sesión de usuarios.

    En el método GET, renderiza el formulario de login.
    En el método POST, procesa las credenciales, valida al usuario usando `login_usuario()`,
    crea la sesión y redirige al índice principal, o muestra un mensaje de error.

    Args:
        None (espera datos de formulario a través de 'request.form' para POST)

    Returns:
        redirect or render_template:
            - Redirección a `main.index` si el login es exitoso.
            - Renderiza la plantilla `usuario/login.html` con mensajes flash si falla la validación
              o si el método es GET.
    """

    if request.method == "POST":
        # Datos del formulario HTML que pasaste antes
        user_input = request.form.get("nombre_usuario")
        pass_input = request.form.get("contraseña")

        usuario = login_usuario(user_input, pass_input)

        if usuario:
            flash(f"Bienvenido de nuevo, {usuario.nombre}", "success")
            return redirect(url_for("main.index"))

        flash("Credenciales inválidas. Inténtalo de nuevo.", "danger")

    return render_template("usuario/login.html")


# Log out #


@auth_bp.route("/logout")
def logout():
    """Cierra la sesión del usuario actual.

    Llama a la función auxiliar `logout_usuario()` para manejar la lógica de la sesión
    y redirige al usuario a la página de login.

    Args:
        None (Esta función no recibe argumentos explícitos)

    Returns:
        redirect: Una redirección a la ruta '.login'.
    """

    logout_usuario()
    return redirect(url_for(".login"))


# Registrarse #


@auth_bp.route("/registrarse", methods=["GET", "POST"])
def registrarse():
    """
    Gestiona el flujo de registro de nuevos usuarios.

    Procesa la entrada del formulario, valida la coincidencia de contraseñas
    y delega la creación del usuario a la capa de servicios.

    Args:
        Ninguno (obtiene datos directamente de flask.request.form).

    Returns:
        str: El HTML renderizado de la página de registro (GET) o una
             redirección (redirect) a la página de login o registro (POST).

    Example:
        Si el usuario accede vía navegador:
        >>> registrarse()
        # Retorna el render_template("usuario/registrarse.html")

        Si el usuario envía el formulario con datos válidos:
        >>> registrarse()
        # Retorna redirect(url_for(".login"))
    """

    if request.method == "POST":
        # Verificar si las contraseñas coinciden antes de ir al servicio
        pass1 = request.form.get("contrasena")
        pass2 = request.form.get("contrarep")

        if pass1 != pass2:
            flash("Las contraseñas no coinciden", "danger")
            return redirect(url_for(".registrarse"))

        # Mapeo de datos para el servicio crear_usuario
        datos = {
            "dni": request.form.get("dni"),
            "nombre": request.form.get("nombre"),
            "apellidos": request.form.get("apellidos"),
            "usuario": request.form.get("usuario"),
            "contrasena": pass1,
            "gmail": request.form.get("gmail"),
        }

        exito, mensaje = crear_usuario(datos)

        if exito:
            flash("¡Cuenta creada! Ahora puedes iniciar sesión.", "success")
            return redirect(url_for(".login"))
        else:
            flash(mensaje, "danger")

    return render_template("usuario/registrarse.html")


# =================================== USUARIO ================================= #
