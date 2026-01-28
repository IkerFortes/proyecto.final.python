from database import db

# ---------------------------- RECARGA ------------------------------ #


class Recargar(db.Model):
    __tablename__ = "RECARGAS"

    id = db.Column(db.Integer, primary_key=True)
    id_cartera = db.Column(db.Integer, db.ForeignKey("CARTERAS.id"))
    id_tarjeta = db.Column(db.Integer, db.ForeignKey("TARJETAS.id"))
    cantidad = db.Column(db.Numeric(10, 2, asdecimal=True), default=0.00)
    fecha = db.Column(db.DateTime, server_default=db.func.now())

    cartera = db.relationship("Cartera", back_populates="recargas")
