<<<<<<< HEAD

IMPORTANTE

Para ejecutar este programa necesitas lo siguiente
    -Tener Python instalado
    -Tener flask instalado (puedes usar el comando python -m pip install flask para instalarlo)
    -Tener instalado flask-sqlalchemy (puedes usar el comando python -m pip install flask-sqlalchemy para instalarlo)
# 💳 Sistema de Gestión de Carteras y Tarjetas (SQLAlchemy 2026)

Este proyecto implementa una arquitectura modular y robusta para la gestión de usuarios, carteras digitales, tarjetas de débito y transacciones financieras, utilizando **Python** y **SQLAlchemy ORM**.

## 🏗️ Arquitectura del Proyecto

El sistema sigue una estructura profesional de capas para separar la configuración, los datos y la lógica:

*   **`database.py`**: Configura el motor de SQLAlchemy, gestiona la fábrica de sesiones y activa el soporte de claves foráneas para SQLite.
*   **`models.py`**: Define el esquema de la base de datos (tablas, columnas y relaciones) mediante clases de Python.
*   **`services.py`**: Contiene la lógica de negocio (registro de usuarios, recargas de saldo, transferencias entre carteras).
*   **`main.py`**: Punto de entrada para ejecutar la aplicación y realizar pruebas de flujo.
*   **`/data`**: Carpeta donde se aloja el archivo `base_de_datos.db` de forma persistente.

## 🗄️ Modelo de Datos

El diseño incluye integridad referencial y borrado en cascada:

1.  **Usuarios**: Almacena DNI, nombre, apellidos, credenciales y correo.
2.  **Carteras**: Relación 1:1 con Usuario. Gestiona el saldo acumulado.
3.  **Tarjetas**: Relación 1:N con Usuario. Permite vincular múltiples métodos de pago.
4.  **Recargas**: Registro de ingresos desde una tarjeta a la cartera.
5.  **Transacciones**: Registro de envíos de dinero entre carteras de diferentes usuarios.

## 🚀 Funcionalidades Implementadas

*   ✅ **Registro Atómico**: Creación de usuario y cartera en una única transacción (si uno falla, el otro no se crea).
*   ✅ **Gestión Multi-Tarjeta**: Capacidad para que un usuario registre múltiples tarjetas de débito.
*   ✅ **Lógica de Saldo**: Las recargas y transferencias actualizan automáticamente el balance real de las carteras.
*   ✅ **Validación de Fondos**: El sistema impide transferencias si el saldo de la cartera de origen es insuficiente.
*   ✅ **Seguridad SQLite**: Activación forzada de `PRAGMA foreign_keys` para garantizar la integridad de las relaciones.

## 🛠️ Requisitos e Instalación

1.  **Clonar o descargar** los archivos en una carpeta.
2.  **Instalar SQLAlchemy** (Versión 2.0+ recomendada en 2026):
    ```bash
    pip install sqlalchemy
    ```
3.  **Ejecutar**:
    ```bash
    python main.py
    ```
    *Nota: La base de datos y las carpetas necesarias se crearán automáticamente al iniciar.*

## 🔒 Consideraciones de Seguridad
*   **Contraseñas**: El sistema está diseñado para recibir hashes de contraseñas. **No** se debe almacenar texto plano en producción.
*   **Rollbacks**: Todas las operaciones de escritura están protegidas con bloques `try-except` para revertir cambios en caso de error.

---
*Proyecto desarrollado con estándares de persistencia de datos 2026.*
=======
# python.proyecto
Proyecto de fin de curso
>>>>>>> 656cb965ce586c81152e7b0f34dd8c6b4ad940fd
