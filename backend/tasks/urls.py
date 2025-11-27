from django.urls import path
from . import views

urlpatterns = [
    path('tasks/', views.task_list_create, name='task-list-create'),
    path('tasks/<int:task_id>/', views.task_detail, name='task-detail'),
    path('analyze/', views.analyze_tasks, name='analyze-tasks'),
]

