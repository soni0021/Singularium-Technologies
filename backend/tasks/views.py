from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from .models import Task
from .serializers import TaskSerializer
from .scoring import (
    calculate_priority_score,
    get_score_explanation,
    detect_circular_dependencies,
    get_strategy_weights
)

@api_view(['GET', 'POST'])
def task_list_create(request):
    if request.method == 'GET':
        tasks = Task.objects.all().order_by('-created_at')
        tasks_data = []
        for task in tasks:
            task_dict = {
                'id': str(task.id),
                'title': task.title,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'estimated_hours': task.estimated_hours,
                'importance': task.importance,
                'dependencies': task.dependencies,
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat()
            }
            tasks_data.append(task_dict)
        return Response(tasks_data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            task = Task(
                title=validated_data['title'],
                due_date=validated_data.get('due_date') if validated_data.get('due_date') else None,
                estimated_hours=validated_data.get('estimated_hours', 0),
                importance=validated_data.get('importance', 5),
                dependencies=validated_data.get('dependencies', [])
            )
            if task.due_date and isinstance(task.due_date, str):
                task.due_date = datetime.strptime(task.due_date, '%Y-%m-%d').date()
            try:
                task.save()
                response_data = {
                    'id': str(task.id),
                    'title': task.title,
                    'due_date': task.due_date.isoformat() if task.due_date else None,
                    'estimated_hours': task.estimated_hours,
                    'importance': task.importance,
                    'dependencies': task.dependencies,
                    'created_at': task.created_at.isoformat(),
                    'updated_at': task.updated_at.isoformat()
                }
                return Response(response_data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def task_detail(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        task_dict = {
            'id': str(task.id),
            'title': task.title,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'estimated_hours': task.estimated_hours,
            'importance': task.importance,
            'dependencies': task.dependencies,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat()
        }
        return Response(task_dict, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            task.title = validated_data['title']
            if validated_data.get('due_date'):
                task.due_date = datetime.strptime(validated_data['due_date'], '%Y-%m-%d').date()
            else:
                task.due_date = None
            task.estimated_hours = validated_data.get('estimated_hours', task.estimated_hours)
            task.importance = validated_data.get('importance', task.importance)
            task.dependencies = validated_data.get('dependencies', task.dependencies)
            try:
                task.save()
                response_data = {
                    'id': str(task.id),
                    'title': task.title,
                    'due_date': task.due_date.isoformat() if task.due_date else None,
                    'estimated_hours': task.estimated_hours,
                    'importance': task.importance,
                    'dependencies': task.dependencies,
                    'created_at': task.created_at.isoformat(),
                    'updated_at': task.updated_at.isoformat()
                }
                return Response(response_data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
def analyze_tasks(request):
    if not isinstance(request.data, list):
        return Response({'error': 'Expected a list of tasks'}, status=status.HTTP_400_BAD_REQUEST)
    
    tasks_data = request.data
    if not tasks_data:
        return Response({'error': 'Task list cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = TaskSerializer(data=tasks_data, many=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_tasks = serializer.validated_data
    
    for idx, task in enumerate(validated_tasks):
        if not task.get('id'):
            task['id'] = str(idx + 1)
    
    circular_deps = detect_circular_dependencies(validated_tasks)
    if circular_deps:
        return Response({
            'error': 'Circular dependencies detected',
            'cycles': circular_deps
        }, status=status.HTTP_400_BAD_REQUEST)
    
    strategy = request.query_params.get('strategy', 'smart_balance')
    weights = get_strategy_weights(strategy)
    
    analyzed_tasks = []
    for task in validated_tasks:
        priority_score = calculate_priority_score(task, validated_tasks, weights)
        explanation = get_score_explanation(task, validated_tasks, weights)
        
        task_result = {
            'id': task.get('id'),
            'title': task.get('title'),
            'due_date': task.get('due_date'),
            'estimated_hours': task.get('estimated_hours', 0),
            'importance': task.get('importance', 5),
            'dependencies': task.get('dependencies', []),
            'priority_score': priority_score,
            'explanation': explanation
        }
        analyzed_tasks.append(task_result)
    
    analyzed_tasks.sort(key=lambda x: x['priority_score'], reverse=True)
    
    return Response({
        'tasks': analyzed_tasks,
        'strategy': strategy,
        'total_tasks': len(analyzed_tasks)
    }, status=status.HTTP_200_OK)
