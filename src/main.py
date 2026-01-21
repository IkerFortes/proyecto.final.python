import os
import services

# Asegúrate de importar 'engine' para poder cerrarlo al final
from database import DB_PATH, engine
from app import app


def run_test_suite():
    print(f"--- Iniciando Suite de Pruebas ---")

    # Declaramos las variables de usuario al principio para usarlas en finally si falla
    user_alex_id = None
    user_maria_id = None

    try:
        # --- 1. REGISTRO DE USUARIOS ---
        print("Registrando a Alex y María...")
        # AHORA CAPTURAMOS EL ID DEVUELTO
        user_alex_id = services.registrar_usuario(
            "11111111A", "Alex", "Garcia", "alex_g", "hash_alex123", "alex@mail.com"
        )
        user_maria_id = services.registrar_usuario(
            "22222222B", "Maria", "Lopez", "maria_l", "hash_maria456", "maria@mail.com"
        )

        if user_alex_id is not None and user_maria_id is not None:
            print(
                f"Usuarios Alex (ID: {user_alex_id}) y María (ID: {user_maria_id}) creados."
            )
        else:
            print("Error al crear usuarios, abortando pruebas.")
            return

        # ... (El resto del código de agregar tarjeta y enviar dinero no requiere cambios) ...
        # ...

        # --- 4. VERIFICACIÓN DE SALDOS (USANDO LA NUEVA FUNCIÓN) ---
        print("\nVerificando saldos finales:")
        saldo_alex = services.obtener_saldo_usuario(user_alex_id)
        saldo_maria = services.obtener_saldo_usuario(user_maria_id)

        print(f"Saldo Alex: {saldo_alex:.2f} EUR (Esperado: 75.00)")
        print(f"Saldo María: {saldo_maria:.2f} EUR (Esperado: 25.00)")

    except Exception as e:
        print(f"\nOcurrió un error inesperado durante las pruebas: {e}")

    finally:
        # --- LIMPIEZA FINAL ---
        print("\n--- Finalizando Pruebas y Limpiando ---")

        # CIERRA EL MOTOR ANTES DE BORRAR EL ARCHIVO
        engine.dispose()

        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print(
                f"Archivo de base de datos '{os.path.basename(DB_PATH)}' eliminado con éxito."
            )
        else:
            print("El archivo de base de datos no fue encontrado para eliminar.")


if __name__ == "__main__":
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    # Envuelve la llamada a la suite de pruebas en el contexto de la app:
    with app.app_context():  # <-- Añade esta línea
        run_test_suite()
