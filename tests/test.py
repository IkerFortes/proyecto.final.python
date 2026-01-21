import sys
import os

# Añade la ruta base del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src import services

# En tests/test.py
from src.database import db, DB_PATH  # Asegúrate de importar lo que realmente necesitas


def run_test_suite():
    print(f"--- Iniciando Suite de Pruebas ---")
    print(f"La base de datos se encuentra en: {os.path.abspath(DB_PATH)}\n")

    try:
        # --- 1. REGISTRO DE USUARIOS ---
        print("Registrando a Alex y María...")
        # Nota: En un entorno real, la contraseña debe ser un hash seguro.
        user_alex = services.registrar_usuario(
            "11111111A", "Alex", "Garcia", "alex_g", "hash_alex123", "alex@mail.com"
        )
        user_maria = services.registrar_usuario(
            "22222222B", "Maria", "Lopez", "maria_l", "hash_maria456", "maria@mail.com"
        )

        if user_alex and user_maria:
            print(
                f"Usuarios Alex (ID: {user_alex.id}) y María (ID: {user_maria.id}) creados."
            )
        else:
            print("Error al crear usuarios, abortando pruebas.")
            return

        # --- 2. AGREGAR TARJETAS Y RECARGAR ---
        print("\nAñadiendo tarjeta a Alex y recargando su cartera...")
        services.agregar_tarjeta(
            user_alex.id, "4000123456789010", "12/28", 123, "Alex Garcia"
        )

        # Asumimos que el ID de tarjeta que acabamos de crear es 1 para el ejemplo simple
        services.recargar_cartera(user_alex.id, id_tarjeta=1, cantidad=100.00)
        print("Cartera de Alex recargada con 100 EUR.")

        # --- 3. TRANSFERENCIA ENTRE USUARIOS ---
        print(f"\nAlex envía 25 EUR a María...")
        transferencia_exitosa = services.enviar_dinero(
            id_usuario_origen=user_alex.id, username_destino="maria_l", cantidad=25.00
        )

        if transferencia_exitosa:
            print("Transferencia completada con éxito.")
        else:
            print("Error en la transferencia (saldo insuficiente o usuario no existe).")

        # --- 4. VERIFICACIÓN DE SALDOS ---
        print("\nVerificando saldos finales:")
        alex_data = services.obtener_datos_usuario(user_alex.id)
        maria_data = services.obtener_datos_usuario(user_maria.id)

        print(f"Saldo Alex: {alex_data.cartera.cantidad:.2f} EUR (Esperado: 75.00)")
        print(f"Saldo María: {maria_data.cartera.cantidad:.2f} EUR (Esperado: 25.00)")

    except Exception as e:
        print(f"\nOcurrió un error inesperado durante las pruebas: {e}")

    finally:
        # --- LIMPIEZA FINAL ---
        print("\n--- Finalizando Pruebas y Limpiando ---")
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print(
                f"Archivo de base de datos '{os.path.basename(DB_PATH)}' eliminado con éxito."
            )
        else:
            print("El archivo de base de datos no fue encontrado para eliminar.")


if __name__ == "__main__":
    # Asegurarse de que la carpeta 'data' exista antes de ejecutar
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    run_test_suite()
