from database import db

# ---------------------------- TARJETAUSUARIO ------------------------------ #


class TarjetaUsuario(db.Model):
    __tablename__ = "TARJETAS_USUARIO"

    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey("USUARIOS.id", ondelete="CASCADE"), nullable=False)
    id_tarjeta = db.Column(db.Integer, db.ForeignKey("TARJETAS.id", ondelete="CASCADE"), nullable=False)

    usuario = db.relationship("Usuario", backref=db.backref("tarjetas_asociadas", cascade="all, delete-orphan"))
    tarjeta = db.relationship("Tarjeta", backref=db.backref("usuarios_asociados", cascade="all, delete-orphan"))