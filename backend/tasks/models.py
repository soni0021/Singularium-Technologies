from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class Task(models.Model):
    title = models.CharField(max_length=200)
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.FloatField(default=0)
    importance = models.IntegerField(default=5)
    dependencies = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.importance < 1 or self.importance > 10:
            raise ValidationError({'importance': 'Importance must be between 1 and 10'})
        if self.estimated_hours < 0:
            raise ValidationError({'estimated_hours': 'Estimated hours cannot be negative'})
        if not isinstance(self.dependencies, list):
            raise ValidationError({'dependencies': 'Dependencies must be a list'})
        for dep in self.dependencies:
            if not isinstance(dep, (int, str)):
                raise ValidationError({'dependencies': 'Each dependency must be an integer or string'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def is_overdue(self):
        if not self.due_date:
            return False
        return self.due_date < timezone.now().date()

    def __str__(self):
        return self.title
