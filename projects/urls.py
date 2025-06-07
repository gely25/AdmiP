from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView
from users.views import signup_view  
from .views import profile_view



urlpatterns = [
    path('', views.home, name='home'),
    path('uploading', views.upload_project, name='upload_project'),
    path('get_directory_tree/', views.get_directory_tree, name='get_directory_tree'),
    path('get_file_content/', views.get_file_content, name='get_file_content'),
    path('proyectos/', views.project_list, name='project_list'),
    path('proyectos/<int:pk>/', views.project_detail, name='project_detail'),
    path('proyectos/<int:pk>/descargar/', views.download_project_zip, name='download_project_zip'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),  
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('signup/', signup_view, name='signup'),
    path('perfil/', profile_view, name='profile'),
    path('proyectos/<int:pk>/comprar/', views.purchase_project, name='purchase_project'),
    path('projects/<int:pk>/edit/', views.edit_project, name='edit_project'),
    path('projects/<int:pk>/delete/', views.delete_project, name='delete_project'),
    path('historial-descargas/', views.download_history, name='download_history'),
    path('download/<int:pk>/', views.download_project_zip, name='download_project'),


    

]

