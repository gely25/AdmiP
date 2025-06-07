from django.db import models
"""
    Modelo Patient: Representa los pacientes registrados en el sistema médico.
"""
class Patient(models.Model):
    first_name = models.CharField(verbose_name='Nombres', max_length=150)
    last_name = models.CharField(verbose_name='Apellidos', max_length=150)
    dni = models.CharField(verbose_name='Cédula', max_length=13, unique=True)
    birth_date = models.DateField(verbose_name='Fecha de Nacimiento')
    gender = models.CharField(
        verbose_name='Género', 
        max_length=1,
        choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')]
    )
    phone = models.CharField(verbose_name='Teléfono', max_length=15, null=True, blank=True)
    email = models.EmailField(verbose_name='Email', null=True, blank=True)
    address = models.CharField(verbose_name='Dirección', max_length=200, null=True, blank=True)
    blood_type = models.CharField(
        verbose_name='Tipo de Sangre',
        max_length=3,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-'),
        ],
        null=True, blank=True
    )
    created_at = models.DateTimeField(verbose_name='Fecha de Registro', auto_now_add=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.dni})"
    
    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['last_name', 'first_name']


"""
    Modelo Diagnosis: Representa los diagnósticos médicos realizados a los pacientes.
"""
class Diagnosis(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name='Paciente', related_name='diagnoses')
    date = models.DateTimeField(verbose_name='Fecha y Hora', auto_now_add=True)
    description = models.TextField(verbose_name='Descripción')
    icd_code = models.CharField(verbose_name='Código CIE', max_length=10, null=True, blank=True)
    notes = models.TextField(verbose_name='Notas Adicionales', null=True, blank=True)
    is_active = models.BooleanField(verbose_name='Activo', default=True)
    
    def __str__(self):
        return f"Diagnóstico de {self.patient} - {self.date.strftime('%d/%m/%Y')}"
    
    class Meta:
        verbose_name = 'Diagnóstico'
        verbose_name_plural = 'Diagnósticos'
        ordering = ['-date']
