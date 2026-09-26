-- ---------------------------------------------------------------------------
-- Creación de la base de datos del Sistema de Información - Colegio Marycarmen.
-- Ejecutar UNA sola vez en MySQL Workbench (o en la consola de MySQL) como root.
--
-- Importante: cambie la clave 'CambiaEstaClave2026' y use la misma en la
-- variable de entorno DB_PASSWORD (ver README.md).
-- ---------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS colegio_marycarmen
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'marycarmen_app'@'localhost' IDENTIFIED BY 'CambiaEstaClave2026';

GRANT ALL PRIVILEGES ON colegio_marycarmen.* TO 'marycarmen_app'@'localhost';

-- Necesario para ejecutar las pruebas unitarias de Django
-- (Django crea y luego elimina una base de datos temporal llamada test_colegio_marycarmen).
GRANT ALL PRIVILEGES ON test_colegio_marycarmen.* TO 'marycarmen_app'@'localhost';

FLUSH PRIVILEGES;
