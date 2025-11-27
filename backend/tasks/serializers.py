from rest_framework import serializers
from datetime import datetime

class TaskSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_null=True)
    title = serializers.CharField(max_length=200, required=True)
    due_date = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    estimated_hours = serializers.FloatField(required=False, default=0, min_value=0)
    importance = serializers.IntegerField(required=False, default=5, min_value=1, max_value=10)
    dependencies = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        default=list
    )
    
    def validate_due_date(self, value):
        if not value or value == '':
            return None
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return value
        except ValueError:
            raise serializers.ValidationError("Due date must be in YYYY-MM-DD format")
    
    def validate_importance(self, value):
        if value is None:
            return 5
        if value < 1 or value > 10:
            raise serializers.ValidationError("Importance must be between 1 and 10")
        return value
    
    def validate_estimated_hours(self, value):
        if value is None:
            return 0
        if value < 0:
            raise serializers.ValidationError("Estimated hours cannot be negative")
        return value
    
    def validate_dependencies(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("Dependencies must be a list")
        return value

