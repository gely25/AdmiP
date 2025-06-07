# Crud Adicional (Examén Práctico)
class TipoPrestamo(models.Model):
    descripcion = models.CharField(max_length=100)
    tasa = models.IntegerField(default=0)

    def __str__(self):
        return self.descripcion
    
    
class Prestamo(models.Model):

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)

    tipo_prestamo = models.ForeignKey(TipoPrestamo, on_delete=models.CASCADE)

    fecha_prestamo = models.DateField()

    monto = models.DecimalField(max_digits=10, decimal_places=2)

    interes = models.DecimalField(max_digits=10, decimal_places=2)

    monto_pagar = models.DecimalField(max_digits=10, decimal_places=2)

    numero_cuotas = models.PositiveIntegerField(default=1)

    cuota_mensual = models.DecimalField(max_digits=10, decimal_places=2)

    saldo = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):

        return f"Préstamo de {self.empleado.nombre} - {self.tipo_prestamo.descripcion}"
    
    
    def save(self, *args, **kwargs):
        tasa = self.tipo_prestamo.tasa
        self.interes = self.monto * (tasa / Decimal('100'))
        self.monto_pagar = self.monto + self.interes
        self.cuota_mensual = self.monto_pagar / self.numero_cuotas
        self.saldo = self.monto_pagar
        super().save(*args, **kwargs)

    
