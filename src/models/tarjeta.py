from database import db

# ---------------------------- TARJETA ------------------------------ #


class Tarjeta(db.Model):
    __tablename__ = "TARJETAS"

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(16), nullable=False)
    caducidad = db.Column(db.String(5), nullable=False)  # Formato MM/AA
    cvc = db.Column(db.Integer, nullable=False)
    propietario_nombre = db.Column(db.String(50), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey("USUARIOS.id", ondelete="CASCADE"))

    propietario = db.relationship("Usuario", back_populates="tarjetas")
