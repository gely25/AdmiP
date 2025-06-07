


import os
import uuid
import zipfile
import mimetypes
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.formatters import HtmlFormatter
from django.db.models import Q 
from .models import Category, Download


from .models import Project
from django.contrib.auth.decorators import login_required


# Configuraciones de seguridad
IGNORED_EXTENSIONS = {'.env', '.sqlite3', '.db', '.pyc', '.pyo', '.exe', '.dll', '.so'}
IGNORED_DIRS = {'__pycache__', '.git', '.idea', '.vscode', 'venv', 'node_modules', '.DS_Store'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_EXTRACTED_SIZE = 200 * 1024 * 1024  # 200MB
ALLOWED_EXTENSIONS = {
    '.py', '.js', '.html', '.css', '.json', '.xml', '.yml', '.yaml', 
    '.txt', '.md', '.rst', '.cfg', '.ini', '.conf', '.sql', '.sh',
    '.java', '.cpp', '.c', '.h', '.php', '.rb', '.go', '.rs'
}

def is_safe_path(path, base_path):
    """Verificar que la ruta no escape del directorio base"""
    abs_path = os.path.abspath(path)
    abs_base = os.path.abspath(base_path)
    return abs_path.startswith(abs_base)

def is_text_file(file_path):
    """Verificar si un archivo es de texto"""
    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type.startswith('text'):
            return True
        
        # Verificar por extensión
        _, ext = os.path.splitext(file_path)
        return ext.lower() in ALLOWED_EXTENSIONS
    except:
        return False






@login_required
def upload_project(request):
    context = {}

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        project_type = request.POST.get('type', '').strip()

        zip_file = request.FILES.get('zip_file')

        is_free = request.POST.get('is_free') == 'on'
        price_input = request.POST.get('price')

        # Validaciones
        if not title:
            context['error'] = 'El título es requerido.'
        elif not project_type:
            context['error'] = 'Debes seleccionar un tipo de proyecto.'

        elif not zip_file:
            context['error'] = 'Por favor selecciona un archivo ZIP.'
        elif not zip_file.name.endswith('.zip'):
            context['error'] = 'Solo se permiten archivos .zip'
        elif zip_file.size > MAX_FILE_SIZE:
            context['error'] = f'El archivo es demasiado grande. Máximo: {MAX_FILE_SIZE // (1024*1024)}MB'
        else:
            try:
                folder_id = str(uuid.uuid4())
                project_path = os.path.join(settings.MEDIA_ROOT, folder_id)
                os.makedirs(project_path, exist_ok=True)

                zip_path = os.path.join(project_path, zip_file.name)

                # Guardar archivo ZIP
                with open(zip_path, 'wb') as f:
                    for chunk in zip_file.chunks():
                        f.write(chunk)

                # Extraer y filtrar archivos
                total_size = 0
                extracted_files = 0

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    for member in zip_ref.namelist():
                        if '..' in member or member.startswith('/'):
                            continue
                        if any(ignored in member for ignored in IGNORED_DIRS):
                            continue
                        file_ext = os.path.splitext(member)[1].lower()
                        if file_ext in IGNORED_EXTENSIONS:
                            continue

                        member_info = zip_ref.getinfo(member)
                        total_size += member_info.file_size
                        if total_size > MAX_EXTRACTED_SIZE:
                            raise ValidationError('El proyecto es demasiado grande después de extraer.')

                        try:
                            zip_ref.extract(member, project_path)
                            extracted_files += 1
                        except Exception as e:
                            print(f"Error extrayendo {member}: {e}")
                            continue

                os.remove(zip_path)

                if extracted_files == 0:
                    context['error'] = 'No se encontraron archivos válidos en el ZIP.'
                    os.rmdir(project_path)
                else:
                    formatter = HtmlFormatter()
                    context.update({
                        'folder_id': folder_id,
                        'title': title,
                        'description': description,
                        'extracted_files': extracted_files,
                        'style_defs': formatter.get_style_defs('.highlight'),
                        'success': True
                    })

                    price = None
                    if not is_free and price_input:
                        try:
                            price = float(price_input)
                            if price <= 0:
                                raise ValueError
                        except ValueError:
                            context['error'] = 'El precio debe ser un número positivo.'
                            context['categories'] = Category.objects.all()
                            return render(request, 'projects/project_upload.html', context)

                
                    
                    
                    project = Project.objects.create(
                        title=title,
                        description=description,
                        folder_id=folder_id,
                        is_free=is_free,
                        price=price,
                        uploaded_by=request.user,
                        type=project_type 
)


                    # Guardar categorías (pueden ser existentes o nuevas)
                    category_ids = request.POST.getlist('categories[]')
                    for cat in category_ids:
                        if cat.isdigit():
                            category = Category.objects.filter(id=cat).first()
                        else:
                            category, _ = Category.objects.get_or_create(name=cat)
                        if category:
                            project.categories.add(category)
                                        

            except ValidationError as e:
                context['error'] = str(e)
            except Exception as e:
                context['error'] = f'Error procesando el archivo: {str(e)}'

    # Siempre cargar las categorías para GET y también si hubo errores en POST
    context['categories'] = Category.objects.all()
    return render(request, 'projects/project_upload.html', context)


def get_directory_tree(request):
    folder_id = request.GET.get('folder_id')
    if not folder_id:
        return JsonResponse({'error': 'folder_id requerido'}, status=400)
    
    base_path = os.path.join(settings.MEDIA_ROOT, folder_id)
    
    if not os.path.exists(base_path):
        return JsonResponse({'error': 'Proyecto no encontrado'}, status=404)

    def build_tree(path):
        tree = []
        try:
            items = sorted(os.listdir(path))
        except PermissionError:
            return tree
            
        for item in items:
            item_path = os.path.join(path, item)

            # Seguridad de ruta
            if not is_safe_path(item_path, path):
                continue

            is_file = os.path.isfile(item_path)
            is_text = is_text_file(item_path) if is_file else False

            try:
                size = os.path.getsize(item_path) if is_file else 0
            except:
                size = 0

            node = {
                'text': item,
                'icon': 'jstree-file' if is_file else 'jstree-folder',
                'children': build_tree(item_path) if not is_file else [],
                'type': 'file' if is_file else 'folder',
                'data': {
                    'path': os.path.relpath(item_path, settings.MEDIA_ROOT),
                    'size': size,
                    'is_text': is_text,
                    'binary': not is_text if is_file else False
                }
            }

            tree.append(node)
        return tree

    try:
        tree_data = build_tree(base_path)
        return JsonResponse(tree_data, safe=False)
    except Exception as e:
        print(f"Error en get_directory_tree: {e}")
        return JsonResponse({'error': f'Error construyendo árbol: {str(e)}'}, status=500)



def get_file_content(request):
    file_path = request.GET.get('path')
    if not file_path:
        return HttpResponseBadRequest('Parámetro "path" requerido.')

    try:
        # Construir ruta absoluta y verificar seguridad
        abs_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, file_path))
        media_root = os.path.abspath(settings.MEDIA_ROOT)
        
        if not abs_path.startswith(media_root):
            return HttpResponseBadRequest('Ruta no permitida.')
            
    except Exception as e:
        return HttpResponseBadRequest(f'Error procesando la ruta: {str(e)}')

    if not os.path.isfile(abs_path):
        return HttpResponseBadRequest('El archivo no existe.')

    # Verificar si es archivo de texto
    if not is_text_file(abs_path):
        return HttpResponseBadRequest('Este archivo no se puede mostrar (archivo binario).')

    try:
        # Leer archivo con manejo de errores de encoding
        encodings = ['utf-8', 'latin-1', 'cp1252']
        content = None
        
        for encoding in encodings:
            try:
                with open(abs_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
                
        if content is None:
            return HttpResponseBadRequest('No se pudo leer el archivo (problemas de codificación).')

        # Limitar tamaño del contenido mostrado
        if len(content) > 100000:  # 100KB
            content = content[:100000] + '\n\n... (archivo truncado por tamaño) ...'

        # Syntax highlighting
        try:
            lexer = get_lexer_for_filename(abs_path, stripall=True)
        except Exception:
            lexer = TextLexer()

        formatter = HtmlFormatter(
            linenos=True, 
            full=False, 
            cssclass='highlight',
            style='friendly' 
        )

        highlighted = highlight(content, lexer, formatter)
        
        # Información del archivo
        file_info = {
            'name': os.path.basename(abs_path),
            'size': os.path.getsize(abs_path),
            'lines': len(content.splitlines())
        }
        
        response_html = f"""
        <div class="file-info">
            <strong>{file_info['name']}</strong> - 
            {file_info['size']} bytes - 
            {file_info['lines']} líneas
        </div>
        <div class="file-content">
            {highlighted}
        </div>
        """
        
        return HttpResponse(response_html)
        
    except Exception as e:
        return HttpResponseBadRequest(f'Error al leer el archivo: {str(e)}')
    
    
    
    
    

@login_required
def project_list(request):
    query = request.GET.get('q', '')
    is_free = request.GET.get('free', '') == 'on'

    projects = Project.objects.all()

    if query:
        projects = projects.filter(title__icontains=query)

    if is_free:
        projects = projects.filter(is_free=True)

    return render(request, 'projects/home.html', {
        'projects': projects.order_by('-id'),
        'query': query,
        'is_free': is_free
    })




from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponseForbidden
from django.utils.encoding import smart_str
import mimetypes

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)

    # El usuario puede descargar si:
    can_download = (
        project.is_free or
        project.uploaded_by == request.user or
        Purchase.objects.filter(user=request.user, project=project).exists()
    )

    already_bought = Purchase.objects.filter(user=request.user, project=project).exists()

    # Agrega los estilos de Pygments
    formatter = HtmlFormatter()
    style_defs = formatter.get_style_defs('.highlight')

    return render(request, 'projects/project_detail.html', {
        'project': project,
        'can_download': can_download,
        'already_bought': already_bought,
        'style_defs': style_defs,  # ⬅️ lo que faltaba
    })


@login_required
def download_project_zip(request, pk):
    project = get_object_or_404(Project, pk=pk)

    # Solo si es gratis o lo subió el usuario
    if project.is_free or project.uploaded_by == request.user:
        zip_name = f"{project.title.replace(' ', '_')}.zip"
        zip_path = os.path.join(settings.MEDIA_ROOT, project.folder_id, zip_name)

        # Si no existe el zip, lo reconstruimos
        if not os.path.exists(zip_path):
            import shutil
            shutil.make_archive(
                base_name=zip_path.replace('.zip', ''),
                format='zip',
                root_dir=os.path.join(settings.MEDIA_ROOT, project.folder_id)
            )

        # REGISTRO DE DESCARGA
        Download.objects.get_or_create(user=request.user, project=project)

        return FileResponse(open(zip_path, 'rb'), as_attachment=True, filename=smart_str(zip_name))

    return HttpResponseForbidden("No tienes permiso para descargar este archivo.")




@login_required
def profile_view(request):
    query = request.GET.get('q', '')
    is_free = request.GET.get('free', '') == 'on'

    # Solo los proyectos del usuario actual
    projects = Project.objects.filter(uploaded_by=request.user)

    if query:
        projects = projects.filter(title__icontains=query)

    if is_free:
        projects = projects.filter(is_free=True)

    projects = projects.order_by('-id')

    return render(request, 'users/profile.html', {
        'projects': projects,
        'query': query,
        'is_free': is_free
    })


from .models import Project, Purchase
from django.contrib import messages
from django.shortcuts import redirect

@login_required
def purchase_project(request, pk):
    project = get_object_or_404(Project, pk=pk)

    # Validaciones
    if project.is_free:
        messages.info(request, "Este proyecto es gratuito, no necesitas comprarlo.")
        return redirect('project_detail', pk=pk)
    
    if project.uploaded_by == request.user:
        messages.info(request, "Este es tu propio proyecto.")
        return redirect('project_detail', pk=pk)

    already_bought = Purchase.objects.filter(user=request.user, project=project).exists()
    if already_bought:
        messages.info(request, "Ya has comprado este proyecto.")
        return redirect('project_detail', pk=pk)

    # Simular compra
    Purchase.objects.create(user=request.user, project=project)
    messages.success(request, f"Has comprado correctamente: {project.title}")
    return redirect('project_detail', pk=pk)



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk, uploaded_by=request.user)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        project_type = request.POST.get('type', 'Otro')

        is_free = request.POST.get('is_free') == 'on'
        price_input = request.POST.get('price')

        if not title:
            return render(request, 'projects/project_edit.html', {
                'project': project,
                'categories': Category.objects.all(),
                'selected_categories': list(project.categories.values_list('id', flat=True)),
                'error': 'El título es requerido.'
            })

        price = None
        if not is_free and price_input:
            try:
                price = float(price_input)
                if price <= 0:
                    raise ValueError
            except ValueError:
                return render(request, 'projects/project_edit.html', {
                    'project': project,
                    'categories': Category.objects.all(),
                    'selected_categories': list(project.categories.values_list('id', flat=True)),
                    'error': 'El precio debe ser un número positivo.'
                })

        project.title = title
        project.description = description
        project.is_free = is_free
        project.price = price
        project.type = project_type
        project.save()

        # Actualizar categorías
        category_ids = request.POST.getlist('categories[]')
        categories = []
        for cat in category_ids:
            if cat.isdigit():
                category = Category.objects.filter(id=cat).first()
            else:
                category, _ = Category.objects.get_or_create(name=cat)
            if category:
                categories.append(category)

        project.categories.set(categories)

        return redirect('profile')

    return render(request, 'projects/project_edit.html', {
        'project': project,
        'categories': Category.objects.all(),
        'selected_categories': list(project.categories.values_list('id', flat=True))
    })



@login_required
def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk, uploaded_by=request.user)

    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Proyecto eliminado correctamente.')
        return redirect('profile')

    return render(request, 'projects/project_confirm_delete.html', {'project': project})



@login_required
def home(request):
    query = request.GET.get('q', '')
    selected_type = request.GET.get('type', '')
    is_free = request.GET.get('free') == 'on'
    is_paid = request.GET.get('paid') == 'on'
    selected_categories = request.GET.getlist('categories')

    projects = Project.objects.exclude(uploaded_by=request.user)

    if query:
        projects = projects.filter(title__icontains=query)

    if selected_type:
        projects = projects.filter(type=selected_type)

    if is_free:
        projects = projects.filter(is_free=True)
    elif is_paid:
        projects = projects.filter(is_free=False)

    if selected_categories:
        projects = projects.filter(categories__id__in=selected_categories).distinct()

    types = dict(Project.TYPE_CHOICES)
    categories = Category.objects.all()

    return render(request, 'home.html', {
        'projects': projects.order_by('-id'),
        'query': query,
        'selected_type': selected_type,
        'is_free': is_free,
        'is_paid': is_paid,
        'selected_categories': list(map(int, selected_categories)),
        'types': types,
        'categories': categories,
    })



@login_required
def download_history(request):
    downloads = Download.objects.filter(user=request.user).select_related('project').order_by('-timestamp')
    return render(request, 'projects/download_history.html', {'downloads': downloads})
