from app import create_app

# Creamos la instancia de la aplicación
app = create_app()

if __name__ == "__main__":
    # El servidor solo corre si este archivo se ejecuta directamente
    app.run(debug=True, port=5000)
