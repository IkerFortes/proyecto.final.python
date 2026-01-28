from database import db

# ---------------------------- TRANSACCION ------------------------------ #


class Transaccion(db.Model):
    __tablename__ = "TRANSACCIONES"

    id = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Float(asdecimal=True), nullable=False)
    fecha = db.Column(db.DateTime, server_default=db.func.now())

    id_cartera_enviado = db.Column(db.Integer, db.ForeignKey("CARTERAS.id"))
    id_cartera_recibido = db.Column(db.Integer, db.ForeignKey("CARTERAS.id"))
