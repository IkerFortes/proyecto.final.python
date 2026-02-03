# Sistema de Gestión de Carteras y Tarjetas

Python | Flask | SQLAlchemy ORM | 2026

Sistema modular y robusto para la gestión de usuarios, carteras digitales, tarjetas de débito y transacciones financieras.

---

## Instalación y Ejecución

1. Clonar o descargar el proyecto:
    ```bash
    git clone <repo-url>
    cd proyecto
    ```

2. Instalar dependencias:
    ```bash
    python -m pip install flask flask-sqlalchemy werkzeug
    ```

3. Ejecutar la aplicación:
    ```bash
    python main.py
    ```

> Nota: La base de datos y las carpetas necesarias se crean automáticamente al iniciar.

---

## Descripción del Proyecto

Este proyecto implementa un sistema de gestión financiera personal con las siguientes capacidades:

- Registro de usuarios con carteras asociadas automáticamente.
- Gestión de múltiples tarjetas de débito vinculadas al usuario.
- Recargas de dinero desde tarjetas a la cartera personal.
- Transferencias de dinero entre carteras de distintos usuarios.
- Compartición de tarjetas entre usuarios con control de permisos.
- Actualización de información de cuenta: correo electrónico y contraseña.
- Registro histórico de transacciones y recargas.

La arquitectura modular permite separar la **configuración**, el **modelo de datos**, la **lógica de negocio** y las **rutas/plantillas**, siguiendo buenas prácticas de desarrollo limpio y escalable.

---

## Modelo de Datos

El sistema incluye:

1. **Usuarios**: Información personal, credenciales y correo electrónico.
2. **Carteras**: Relación 1:1 con usuario, almacena el saldo actual.
3. **Tarjetas**: Relación N:M con usuario, con número, caducidad, CVC y saldo propio.
4. **Recargas**: Registro de ingresos desde tarjetas a carteras.
5. **Transacciones**: Historial de transferencias entre carteras de usuarios.
6. **TarjetaUsuario**: Tabla intermedia que gestiona la relación N:M entre usuarios y tarjetas, permitiendo compartir tarjetas.

Relaciones clave:

- Usuario ↔ Cartera: 1:1
- Usuario ↔ Tarjetas: N:M (tabla `TarjetaUsuario`)

Se asegura integridad referencial y borrado en cascada en SQLite mediante `PRAGMA foreign_keys`.

---

## Funcionalidades Implementadas

### Gestión de Cuenta
- Registro de usuario y cartera atómico.
- Actualización de correo electrónico con verificación de duplicados.
- Actualización de contraseña con validación de contraseña actual.

### Tarjetas
- Añadir, eliminar y listar múltiples tarjetas de débito.
- Compartir tarjetas con otros usuarios de forma segura.
- Las tarjetas compartidas se gestionan mediante la tabla intermedia `TarjetaUsuario`.

### Carteras
- Ingreso de dinero desde tarjetas vinculadas.
- Validación de fondos insuficientes para transferencias.
- Actualización automática de saldo tras recargas o transferencias.

### Transacciones
- Registro completo de recargas y transferencias entre usuarios.
- Posibilidad de consultar historial completo por usuario.

### Seguridad
- Contraseñas almacenadas como hashes (`generate_password_hash`).
- Bloques `try-except` en operaciones de escritura para rollback en caso de error.
- Integridad referencial reforzada en SQLite (`PRAGMA foreign_keys`).

---

## Requisitos del Sistema

- Python 3.10+
- Flask 2.x
- Flask-SQLAlchemy 3.x
- SQLAlchemy 2.0+
- Werkzeug (para hashing de contraseñas)

---

## Buenas Prácticas Implementadas

- Código limpio, modular y siguiendo PEP8.
- Uso de docstrings en todas las funciones para facilitar mantenimiento.
- Validaciones y manejo de errores consistentes en todas las operaciones.
- Arquitectura preparada para escalabilidad y nuevas funcionalidades.

---

## Futuras Mejoras

- Soporte para múltiples monedas y conversión automática.
- Integración con APIs de pagos externos (Stripe, PayPal).
- Dashboard interactivo de saldo y transacciones con gráficos.
- Autenticación avanzada con JWT o OAuth.
- Funcionalidades de notificaciones en tiempo real para movimientos de saldo.

---

## Licencia

Proyecto de fin de curso. Uso educativo y demostrativo.

