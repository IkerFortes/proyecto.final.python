from database import db

# ---------------------------- USUARIO ------------------------------ #


class Usuario(db.Model):
    __tablename__ = "USUARIOS"

    id = db.Column(db.Integer, primary_key=True)
    dni = db.Column(db.String(9), unique=True, nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    apellidos = db.Column(db.String(75), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    contrasena = db.Column(db.String, nullable=False)
    gmail = db.Column(db.String(50), unique=True, nullable=False)

    # Las relaciones (back_populates) permiten la navegación bidireccional
    cartera = db.relationship(
        "Cartera",
        back_populates="propietario",
        uselist=False,
        cascade="all, delete-orphan",
    )
    tarjetas = db.relationship(
        "Tarjeta", back_populates="propietario", cascade="all, delete-orphan"
    )
