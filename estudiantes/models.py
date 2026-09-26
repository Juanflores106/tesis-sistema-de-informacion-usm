"""
Modelos del módulo de Estudiantes y Representantes.
Sistema de Información para la Gestión Académica y Financiera - Colegio Marycarmen.

Cada clase de este archivo se convierte en una tabla de la base de datos MySQL
al ejecutar:  python manage.py makemigrations  y  python manage.py migrate
"""
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

# ---------------------------------------------------------------------------
# Validadores reutilizables
# ---------------------------------------------------------------------------
validar_cedula = RegexValidator(
    regex=r'^\d{6,9}$',
    message='La cédula debe contener entre 6 y 9 dígitos, sin puntos ni letras.',
)
validar_telefono = RegexValidator(
    regex=r'^0\d{3}-?\d{7}$',
    message='Formato de teléfono válido: 0414-1234567',
)


# ---------------------------------------------------------------------------
# Opciones (listas desplegables)
# ---------------------------------------------------------------------------
class Nacionalidad(models.TextChoices):
    VENEZOLANO = 'V', 'Venezolano(a)'
    EXTRANJERO = 'E', 'Extranjero(a)'


class Sexo(models.TextChoices):
    MASCULINO = 'M', 'Masculino'
    FEMENINO = 'F', 'Femenino'


# ---------------------------------------------------------------------------
# Clase abstracta: agrupa los datos comunes de cualquier persona.
# No genera tabla propia; sus campos se copian en Estudiante y Representante.
# (En el diagrama de clases se representa como una generalización / herencia.)
# ---------------------------------------------------------------------------
class Persona(models.Model):
    nacionalidad = models.CharField(
        max_length=1, choices=Nacionalidad.choices, default=Nacionalidad.VENEZOLANO
    )
    nombres = models.CharField(max_length=80)
    apellidos = models.CharField(max_length=80)
    sexo = models.CharField(max_length=1, choices=Sexo.choices)
    direccion = models.TextField('dirección de habitación')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    @property
    def nombre_completo(self):
        return f'{self.nombres} {self.apellidos}'


# ---------------------------------------------------------------------------
# Representante
# ---------------------------------------------------------------------------
class Representante(Persona):
    cedula = models.CharField(
        'cédula de identidad', max_length=9, unique=True, validators=[validar_cedula]
    )
    fecha_nacimiento = models.DateField(null=True, blank=True)
    telefono_principal = models.CharField(max_length=12, validators=[validar_telefono])
    telefono_secundario = models.CharField(
        max_length=12, blank=True, validators=[validar_telefono]
    )
    correo = models.EmailField('correo electrónico', blank=True)
    ocupacion = models.CharField('ocupación', max_length=80, blank=True)
    lugar_trabajo = models.CharField('lugar de trabajo', max_length=120, blank=True)

    class Meta:
        verbose_name = 'representante'
        verbose_name_plural = 'representantes'
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f'{self.nacionalidad}-{self.cedula} | {self.nombre_completo}'


# ---------------------------------------------------------------------------
# Estudiante
# ---------------------------------------------------------------------------
class Estudiante(Persona):
    class Estatus(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        RETIRADO = 'RETIRADO', 'Retirado'
        EGRESADO = 'EGRESADO', 'Egresado'

    cedula_escolar = models.CharField(
        'cédula escolar',
        max_length=15,
        unique=True,
        help_text='Cédula escolar asignada al estudiante (verificar formato con la secretaría).',
    )
    cedula = models.CharField(
        'cédula de identidad',
        max_length=9,
        unique=True,
        null=True,
        blank=True,
        validators=[validar_cedula],
        help_text='Opcional: solo si el estudiante ya posee cédula de identidad.',
    )
    fecha_nacimiento = models.DateField()
    lugar_nacimiento = models.CharField(max_length=120)
    condiciones_medicas = models.TextField(
        'condiciones médicas',
        blank=True,
        help_text='Alergias, enfermedades u otras condiciones de salud relevantes.',
    )
    estatus = models.CharField(
        max_length=10, choices=Estatus.choices, default=Estatus.ACTIVO
    )
    representantes = models.ManyToManyField(
        Representante,
        through='EstudianteRepresentante',
        related_name='estudiantes',
    )

    class Meta:
        verbose_name = 'estudiante'
        verbose_name_plural = 'estudiantes'
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f'{self.cedula_escolar} | {self.nombre_completo}'

    def save(self, *args, **kwargs):
        # Un campo vacío se guarda como NULL para no violar la restricción "unique"
        # cuando varios estudiantes aún no tienen cédula de identidad.
        if not self.cedula:
            self.cedula = None
        super().save(*args, **kwargs)

    @property
    def representante_legal(self):
        relacion = self.relaciones_representante.filter(
            es_representante_legal=True
        ).select_related('representante').first()
        return relacion.representante if relacion else None


# ---------------------------------------------------------------------------
# Tabla intermedia: relación muchos a muchos entre Estudiante y Representante
# ---------------------------------------------------------------------------
class EstudianteRepresentante(models.Model):
    class Parentesco(models.TextChoices):
        MADRE = 'MADRE', 'Madre'
        PADRE = 'PADRE', 'Padre'
        ABUELO = 'ABUELO', 'Abuelo(a)'
        TIO = 'TIO', 'Tío(a)'
        HERMANO = 'HERMANO', 'Hermano(a)'
        OTRO = 'OTRO', 'Otro'

    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name='relaciones_representante'
    )
    representante = models.ForeignKey(
        Representante, on_delete=models.PROTECT, related_name='relaciones_estudiante'
    )
    parentesco = models.CharField(max_length=10, choices=Parentesco.choices)
    es_representante_legal = models.BooleanField(default=False)
    autorizado_retirar = models.BooleanField(
        'autorizado para retirar al estudiante', default=True
    )

    class Meta:
        verbose_name = 'relación estudiante-representante'
        verbose_name_plural = 'relaciones estudiante-representante'
        constraints = [
            models.UniqueConstraint(
                fields=['estudiante', 'representante'],
                name='representante_unico_por_estudiante',
            ),
        ]

    def __str__(self):
        return f'{self.representante.nombre_completo} ({self.get_parentesco_display()}) → {self.estudiante.nombre_completo}'

    def clean(self):
        # Regla de negocio: cada estudiante solo puede tener UN representante legal.
        # Se valida aquí porque MySQL no admite restricciones únicas condicionales.
        if self.es_representante_legal and self.estudiante_id:
            ya_existe = EstudianteRepresentante.objects.filter(
                estudiante_id=self.estudiante_id,
                es_representante_legal=True,
            ).exclude(pk=self.pk).exists()
            if ya_existe:
                raise ValidationError(
                    'Este estudiante ya tiene un representante legal asignado.'
                )
