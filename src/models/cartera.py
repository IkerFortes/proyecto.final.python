from database import db

# ---------------------------- CARTERA ------------------------------ #


class Cartera(db.Model):
    __tablename__ = "CARTERAS"

    id = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Numeric(10, 2, asdecimal=True), default=0.00)
    id_usuario = db.Column(db.Integer, db.ForeignKey("USUARIOS.id", ondelete="CASCADE"))

    propietario = db.relationship("Usuario", back_populates="cartera")
    recargas = db.relationship("Recargar", back_populates="cartera")

    transacciones_enviadas = db.relationship(
        "Transaccion", foreign_keys="Transaccion.id_cartera_enviado"
    )
    transacciones_recibidas = db.relationship(
        "Transaccion", foreign_keys="Transaccion.id_cartera_recibido"
    )
