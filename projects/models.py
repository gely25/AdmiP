

from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Project(models.Model):
    TYPE_CHOICES = [
        ('mobile', 'Aplicación Móvil'),
        ('web', 'Aplicación Web'),
        ('game', 'Juego'),
        ('dashboard', 'Dashboard'),
        ('ai', 'IA / Machine Learning'),
        ('script', 'Script / Automatización'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    folder_id = models.CharField(max_length=100, unique=True)  # ID generado al subir
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    upload_date = models.DateTimeField(auto_now_add=True)
    categories = models.ManyToManyField(Category, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, blank=True)

    def __str__(self):
        return self.title


class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project')

    def __str__(self):
        return f"{self.user.username} compró {self.project.title}"


# models.py
from django.db import models
from django.contrib.auth.models import User

class Download(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} descargó {self.project.title}"
