from django.shortcuts import get_object_or_404, render, redirect
from .models import Empleado, Rol, Departamento, Cargo, TipoContrato, Prestamo, TipoPrestamo
from .forms import EmpleadoForm, RolForm, CargoForm, DepartamentoForm, TipoContratoForm, PrestamoForm
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse
from django.http.request import HttpRequest



#Crud adicional examen práctico
@login_required
def listar_prestamos(request):
    query = request.GET.get('q', '')  # nombre del empleado
    tipo = request.GET.get('tipo', '')
    fecha = request.GET.get('fecha', '')

    prestamos = Prestamo.objects.select_related('empleado', 'tipo_prestamo').all()

    if query:
        prestamos = prestamos.filter(empleado__nombre__icontains=query)

    if tipo:
        prestamos = prestamos.filter(tipo_prestamo__descripcion__icontains=tipo)

    if fecha:
        try:
            fecha_dt = datetime.strptime(fecha, '%Y-%m-%d').date()
            prestamos = prestamos.filter(fecha_prestamo=fecha_dt)
        except ValueError:
            print("⚠️ Fecha inválida: no se aplicó filtro por fecha")

    paginator = Paginator(prestamos, 5)
    page = request.GET.get('page', 1)

    try:
        prestamos_paginados = paginator.page(page)
    except PageNotAnInteger:
        prestamos_paginados = paginator.page(1)
    except:
        prestamos_paginados = paginator.page(paginator.num_pages)

    contexto = {
        'prestamos': prestamos_paginados,
        'title': 'Listado de Préstamos',
        'q': query,
        'tipo': tipo,
        'fecha': fecha,
    }

    return render(request, 'prestamo/list.html', contexto)

@login_required
def crear_prestamo(request):
    contexto = {'title': 'Crear Préstamo'}
    if request.method == 'GET':
        form = PrestamoForm()
        contexto['form'] = form
        return render(request, 'prestamo/create.html', contexto)
    else:
        form = PrestamoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('Nomina:listar_prestamos')
        else:
            contexto['form'] = form
            return render(request, 'prestamo/create.html', contexto)

@login_required
def actualizar_prestamo(request, id):
    prestamo = get_object_or_404(Prestamo, pk=id)
    contexto = {'title': 'Actualizar Préstamo'}
    if request.method == 'GET':
        form = PrestamoForm(instance=prestamo)
        contexto['form'] = form
        return render(request, 'prestamo/create.html', contexto)
    else:
        form = PrestamoForm(request.POST, instance=prestamo)
        if form.is_valid():
            form.save()
            return redirect('Nomina:listar_prestamos')
        else:
            contexto['form'] = form
            return render(request, 'prestamo/create.html', contexto)

@login_required
def eliminar_prestamo(request, id):
    prestamo = get_object_or_404(Prestamo, pk=id)
    if request.method == 'POST':
        prestamo.delete()
        return redirect('Nomina:listar_prestamos')
    return render(request, 'prestamo/delete.html', {'prestamo': prestamo, 'title': 'Eliminar Préstamo'})
