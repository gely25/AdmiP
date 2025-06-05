from django.urls import path
from . import views



urlpatterns = [
    path('', views.upload_project, name='upload_project'),
    path('get_directory_tree/', views.get_directory_tree, name='get_directory_tree'),
    path('get_file_content/', views.get_file_content, name='get_file_content'),
]
