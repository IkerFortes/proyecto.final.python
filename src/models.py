from database import db  # Importamos la instancia de Flask-SQLAlchemy

# Todos los modelos ahora heredan de db.Model
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


class Cartera(db.Model):
    __tablename__ = "CARTERAS"

    id = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Float(asdecimal=True), default=0.0)
    id_usuario = db.Column(db.Integer, db.ForeignKey("USUARIOS.id", ondelete="CASCADE"))

    propietario = db.relationship("Usuario", back_populates="cartera")
    recargas = db.relationship("RellenarMonedero", back_populates="cartera")

    # Transacciones como enviado y recibido
    transacciones_enviadas = db.relationship(
        "Transaccion", foreign_keys="[Transaccion.id_cartera_enviado]"
    )
    transacciones_recibidas = db.relationship(
        "Transaccion", foreign_keys="[Transaccion.id_cartera_recibido]"
    )


class Tarjeta(db.Model):
    __tablename__ = "TARJETA"

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(16), nullable=False)
    caducidad = db.Column(db.String(5), nullable=False)  # Formato MM/AA
    csv = db.Column(db.Integer, nullable=False)
    propietario_nombre = db.Column(db.String(50), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey("USUARIOS.id", ondelete="CASCADE"))

    propietario = db.relationship("Usuario", back_populates="tarjetas")


class RellenarMonedero(db.Model):
    __tablename__ = "RELLENAR_MONEDERO"

    id = db.Column(db.Integer, primary_key=True)
    id_cartera = db.Column(db.Integer, db.ForeignKey("CARTERAS.id"))

    # ¡ESTA ES LA LÍNEA CON ERROR!
    # id_tarjeta = db.Column(db.Integer, db.Integer, db.ForeignKey('TARJETA.id'))

    # CÁMBIALA POR ESTO:
    id_tarjeta = db.Column(db.Integer, db.ForeignKey("TARJETA.id"))

    cantidad = db.Column(db.Float(asdecimal=True), nullable=False)
    fecha = db.Column(db.DateTime, server_default=db.func.now())

    cartera = db.relationship("Cartera", back_populates="recargas")


class Transaccion(db.Model):
    __tablename__ = "TRANSACCION"

    id = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Float(asdecimal=True), nullable=False)
    fecha = db.Column(db.DateTime, server_default=db.func.now())

    id_cartera_enviado = db.Column(db.Integer, db.ForeignKey("CARTERAS.id"))
    id_cartera_recibido = db.Column(db.Integer, db.ForeignKey("CARTERAS.id"))
