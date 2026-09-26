# tesis de grado realizada por mi persona en la cual se busca gestionar y automatizar la parte financiera y academica de un colegio

**Sistema de información para la gestión académica y financiera en un colegio.**
Caso de estudio: Colegio Marycarmen, Puerto La Cruz, estado Anzoátegui.
Universidad Santa María, Núcleo de Oriente. Ingeniería de Sistemas.

Aplicación web cliente-servidor de tres capas con el patrón MVT de Django.

| Capa | Tecnología |
|------|------------|
| Presentación | HTML5, CSS3, JavaScript y Bootstrap 5.3 (incluido en `static/vendor`, funciona sin Internet) |
| Lógica de negocio | Python 3.12+ y Django 5.2 LTS |
| Datos | MySQL Community Server 8.4 LTS (administrado con MySQL Workbench) |

## Estado del desarrollo

| Módulo (app) | Estado |
|--------------|--------|
| `usuarios`: inicio de sesión, roles y administración de usuarios | Listo |
| `estudiantes`: estudiantes, representantes y su relación | Listo |
| `academico`: año escolar, grados, secciones, materias, lapsos y notas | Pendiente (esperando confirmar el diseño) |
| `inscripciones`: inscripción por año escolar y sección | Pendiente |
| `finanzas`: conceptos de pago, mensualidades, pagos, tasa BCV y morosidad | Pendiente |
| `reportes`: constancias, boletas y estados de cuenta en PDF y Excel | Pendiente |

## Estructura del proyecto

```
├── manage.py
├── requirements.txt
├── config/            configuración (settings.py, urls.py)
├── usuarios/          inicio de sesión, roles (roles.py) y usuarios
├── estudiantes/       estudiantes y representantes
├── academico/         (pendiente)
├── inscripciones/     (pendiente)
├── finanzas/          (pendiente)
├── reportes/          (pendiente)
├── templates/         plantillas HTML (base.html con el menú por rol)
├── static/            CSS propio y Bootstrap
└── docs/              script SQL para crear la base de datos
```

## Instalación en Windows

1. **Requisitos:** Python 3.12 o superior, MySQL Community Server 8.4 LTS con MySQL Workbench, y Git.
   No use XAMPP: su MariaDB 10.4 no es compatible con Django 5.1 o superior.

2. **Descargar el proyecto y crear el entorno virtual** (en la terminal de VS Code):

   ```bat
   git clone https://github.com/juanflores106/tesis-sistema-de-informacion-usm.git
   cd tesis-sistema-de-informacion-usm
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

   Si `mysqlclient` da error al instalarse, ejecute `pip install PyMySQL` y agregue al
   archivo `config/__init__.py`:

   ```python
   import pymysql
   pymysql.install_as_MySQLdb()
   ```

3. **Crear la base de datos:** abra `docs/crear_base_datos.sql` en MySQL Workbench
   (conectado como root) y ejecútelo. Crea la base `colegio_marycarmen` y el usuario
   `marycarmen_app`.

4. **Clave de la base de datos:** si cambió la clave en el script, indíquela antes de
   ejecutar el sistema (en PowerShell):

   ```powershell
   $env:DB_PASSWORD = "SuNuevaClave"
   ```

5. **Crear las tablas y los roles:**

   ```bat
   python manage.py migrate
   ```

   Además de las tablas, este comando crea los tres roles (Director, Control de
   Estudios y Administración) con sus permisos.

6. **Crear la cuenta de soporte técnico** (superusuario) y levantar el servidor:

   ```bat
   python manage.py createsuperuser
   python manage.py runserver
   ```

   Abra http://127.0.0.1:8000, inicie sesión con el superusuario y registre los usuarios
   del colegio en el menú **Usuarios**, asignándoles su rol.

> Si ya había ejecutado `makemigrations` y `migrate` con otra versión de los modelos,
> borre la base de datos (`DROP DATABASE colegio_marycarmen;`), vuelva a ejecutar el
> script del paso 3 y luego `migrate`. Las migraciones oficiales son las de este repositorio.

## Roles y permisos

Cada rol es un Grupo de Django. Sus permisos se definen en una sola tabla
(`MATRIZ_PERMISOS` en `usuarios/roles.py`) y se aplican cada vez que se ejecuta `migrate`.

| Rol | Estudiantes y representantes | Usuarios | Finanzas (pendiente) |
|-----|------------------------------|----------|----------------------|
| Director | Consultar, registrar y modificar | Consultar, registrar, modificar, activar y desactivar | Consultar, registrar y modificar |
| Control de Estudios | Consultar, registrar y modificar | — | — |
| Administración | Solo consultar | — | Consultar, registrar y modificar |

- Ningún rol puede eliminar estudiantes, representantes ni usuarios: se cambia el
  estatus (Activo, Retirado, Egresado) o se desactiva la cuenta.
- Sí se puede quitar el vínculo entre un estudiante y un representante asignado por
  error. Esto no borra los datos del representante.
- Si un usuario intenta abrir una opción que no le corresponde, el sistema muestra
  "Acceso denegado" (error 403).

## Pruebas

```bat
python manage.py test
```

Ejecuta 53 pruebas unitarias e integrales (validaciones, reglas de negocio, permisos
por rol y pantallas). Django crea una base de datos temporal (`test_colegio_marycarmen`)
y la elimina al terminar; los datos reales no se tocan. Con `python manage.py test -v 2`
se ve el nombre de cada prueba, útil para los cuadros de pruebas del Capítulo IV.

## Variables de entorno

Todas son opcionales en desarrollo. En el servidor del colegio se deben definir al
menos `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` y `DB_PASSWORD`.

| Variable | Valor por defecto |
|----------|-------------------|
| `DJANGO_SECRET_KEY` | clave de desarrollo (cambiar en producción) |
| `DJANGO_DEBUG` | `1` (activado) |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | `colegio_marycarmen` / `marycarmen_app` / `CambiaEstaClave2026` |
| `DB_HOST` / `DB_PORT` | `localhost` / `3306` |
| `DB_ENGINE` | vacío (MySQL). Con `sqlite` usa un archivo local para pruebas rápidas sin MySQL |
