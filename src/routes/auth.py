from flask import Blueprint, render_template, request, redirect, url_for, flash
from services import login_usuario, logout_usuario, crear_usuario

auth_bp = Blueprint("auth", __name__)
# =================================== USUARIO ================================= #

# Log in #


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
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
    logout_usuario()
    return redirect(url_for(".login"))


# Registrarse #


@auth_bp.route("/registrarse", methods=["GET", "POST"])
def registrarse():
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
