from django.contrib import admin

# Register your models here.
from django.contrib import admin
from Nomina.models import Empleado, Rol, Cargo, Departamento, TipoContrato, TipoPrestamo, Prestamo

admin.site.site_header = "App Nómina"
admin.site.site_title = "App Nómina Admin"


#Crud Préstamo (Examén Práctico)
admin.site.register(TipoPrestamo)
admin.site.register(Prestamo)
