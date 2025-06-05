# import os
# import uuid
# import zipfile
# from django.shortcuts import render
# from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
# from django.conf import settings
# from pygments import highlight
# from pygments.lexers import get_lexer_for_filename, TextLexer
# from pygments.formatters import HtmlFormatter

# IGNORED_EXTENSIONS = {'.env', '.sqlite3', '.db'}
# IGNORED_DIRS = {'__pycache__', '.git', '.idea', '.vscode', 'venv'}

# def upload_project(request):
#     context = {}

#     if request.method == 'POST':
#         title = request.POST.get('title')
#         description = request.POST.get('description')
#         zip_file = request.FILES.get('zip_file')

#         if not zip_file or not zip_file.name.endswith('.zip'):
#             context['error'] = 'Por favor sube un archivo .zip válido.'
#         else:
#             folder_id = str(uuid.uuid4())
#             project_path = os.path.join(settings.MEDIA_ROOT, folder_id)
#             os.makedirs(project_path, exist_ok=True)

#             zip_path = os.path.join(project_path, zip_file.name)
#             with open(zip_path, 'wb') as f:
#                 for chunk in zip_file.chunks():
#                     f.write(chunk)

#             # Filtro de archivos al extraer
#             with zipfile.ZipFile(zip_path, 'r') as zip_ref:
#                 for member in zip_ref.namelist():
#                     # Ignorar carpetas/archivos ocultos y no deseados
#                     if any(ignored in member for ignored in IGNORED_DIRS):
#                         continue
#                     if os.path.splitext(member)[1] in IGNORED_EXTENSIONS:
#                         continue
#                     # Extraer solamente los archivos permitidos
#                     zip_ref.extract(member, project_path)

#             os.remove(zip_path)

#             formatter = HtmlFormatter()
#             context.update({
#                 'folder_id': folder_id,
#                 'title': title,
#                 'description': description,
#                 'style_defs': formatter.get_style_defs('.highlight')
#             })

#     return render(request, 'projects/project_upload.html', context)

# def get_directory_tree(request):
#     import json
#     folder_id = request.GET.get('folder_id')
#     base_path = os.path.join(settings.MEDIA_ROOT, folder_id)

#     def build_tree(path):
#         tree = []
#         for item in sorted(os.listdir(path)):
#             item_path = os.path.join(path, item)
#             node = {
#                 'text': item,
#                 'icon': 'jstree-file' if os.path.isfile(item_path) else 'jstree-folder',
#                 'type': 'file' if os.path.isfile(item_path) else 'folder',
#                 'data': {'path': os.path.relpath(item_path, settings.MEDIA_ROOT)}
#             }
#             if os.path.isdir(item_path):
#                 node['children'] = build_tree(item_path)
#             tree.append(node)
#         return tree

#     return JsonResponse(build_tree(base_path), safe=False)


# def get_file_content(request):
#     file_path = request.GET.get('path')
#     if not file_path:
#         return HttpResponseBadRequest('Parámetro "path" faltante.')

#     try:
#         abs_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, file_path))
#         if not abs_path.startswith(os.path.abspath(settings.MEDIA_ROOT)):
#             return HttpResponseBadRequest('Ruta no permitida.')
#     except Exception as e:
#         return HttpResponseBadRequest(f'Error procesando la ruta: {str(e)}')

#     if not os.path.isfile(abs_path):
#         return HttpResponseBadRequest(f'El archivo no existe en: {abs_path}')

#     try:
#         with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
#             content = f.read()

#         try:
#             lexer = get_lexer_for_filename(abs_path, stripall=True)
#         except Exception:
#             lexer = TextLexer()

#         formatter = HtmlFormatter(linenos=True, full=False, cssclass='highlight')
#         highlighted = highlight(content, lexer, formatter)
#         return HttpResponse(highlighted)
#     except Exception as e:
#         return HttpResponseBadRequest(f'Error al leer el archivo: {str(e)}')



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

def upload_project(request):
    context = {}

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        zip_file = request.FILES.get('zip_file')

        # Validaciones
        if not title:
            context['error'] = 'El título es requerido.'
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
                        # Verificar seguridad de la ruta
                        if '..' in member or member.startswith('/'):
                            continue
                            
                        # Ignorar directorios y archivos no deseados
                        if any(ignored in member for ignored in IGNORED_DIRS):
                            continue
                            
                        file_ext = os.path.splitext(member)[1].lower()
                        if file_ext in IGNORED_EXTENSIONS:
                            continue
                            
                        # Verificar tamaño total
                        member_info = zip_ref.getinfo(member)
                        total_size += member_info.file_size
                        if total_size > MAX_EXTRACTED_SIZE:
                            raise ValidationError('El proyecto es demasiado grande después de extraer.')
                        
                        # Extraer archivo
                        try:
                            zip_ref.extract(member, project_path)
                            extracted_files += 1
                        except Exception as e:
                            print(f"Error extrayendo {member}: {e}")
                            continue

                # Limpiar archivo ZIP
                os.remove(zip_path)
                
                if extracted_files == 0:
                    context['error'] = 'No se encontraron archivos válidos en el ZIP.'
                    # Limpiar directorio vacío
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
                    
            except ValidationError as e:
                context['error'] = str(e)
            except Exception as e:
                context['error'] = f'Error procesando el archivo: {str(e)}'

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
            style='friendly'  # ✅ estilo seguro incluido en Pygments
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
    
    
    
    
    