from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'due_date', 'estimated_hours', 'importance', 'created_at']
    list_filter = ['importance', 'due_date', 'created_at']
    search_fields = ['title']
    ordering = ['-created_at']
