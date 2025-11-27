from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from rest_framework.test import APIClient
from rest_framework import status
from .models import Task
from .scoring import (
    calculate_urgency_score,
    calculate_importance_score,
    calculate_effort_score,
    calculate_dependency_score,
    calculate_priority_score,
    detect_circular_dependencies,
    get_strategy_weights,
    get_score_explanation
)

class TaskModelTest(TestCase):
    def setUp(self):
        self.task_data = {
            'title': 'Test Task',
            'due_date': date.today() + timedelta(days=7),
            'estimated_hours': 4.0,
            'importance': 7,
            'dependencies': []
        }

    def test_create_task(self):
        task = Task.objects.create(**self.task_data)
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.importance, 7)
        self.assertEqual(task.estimated_hours, 4.0)
        self.assertIsNotNone(task.created_at)

    def test_task_validation_importance_min(self):
        task = Task(**self.task_data)
        task.importance = 0
        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_task_validation_importance_max(self):
        task = Task(**self.task_data)
        task.importance = 11
        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_task_validation_negative_hours(self):
        task = Task(**self.task_data)
        task.estimated_hours = -1
        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_task_validation_dependencies_not_list(self):
        task = Task(**self.task_data)
        task.dependencies = 'not a list'
        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_task_validation_dependencies_invalid_type(self):
        task = Task(**self.task_data)
        task.dependencies = [{'invalid': 'type'}]
        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_is_overdue(self):
        task = Task(**self.task_data)
        task.due_date = date.today() - timedelta(days=1)
        self.assertTrue(task.is_overdue())

    def test_is_not_overdue(self):
        task = Task(**self.task_data)
        task.due_date = date.today() + timedelta(days=1)
        self.assertFalse(task.is_overdue())

    def test_is_not_overdue_no_date(self):
        task = Task(**self.task_data)
        task.due_date = None
        self.assertFalse(task.is_overdue())

    def test_task_string_representation(self):
        task = Task.objects.create(**self.task_data)
        self.assertEqual(str(task), 'Test Task')

class ScoringTest(TestCase):
    def test_urgency_score_no_due_date(self):
        score = calculate_urgency_score(None)
        self.assertEqual(score, 0.5)

    def test_urgency_score_overdue(self):
        overdue_date = (date.today() - timedelta(days=5)).isoformat()
        score = calculate_urgency_score(overdue_date)
        self.assertGreater(score, 0.9)

    def test_urgency_score_today(self):
        today = date.today().isoformat()
        score = calculate_urgency_score(today)
        self.assertEqual(score, 1.0)

    def test_urgency_score_tomorrow(self):
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        score = calculate_urgency_score(tomorrow)
        self.assertEqual(score, 0.95)

    def test_urgency_score_far_future(self):
        future = (date.today() + timedelta(days=60)).isoformat()
        score = calculate_urgency_score(future)
        self.assertLess(score, 0.2)

    def test_importance_score_min(self):
        score = calculate_importance_score(1)
        self.assertEqual(score, 0.1)

    def test_importance_score_max(self):
        score = calculate_importance_score(10)
        self.assertEqual(score, 1.0)

    def test_importance_score_middle(self):
        score = calculate_importance_score(5)
        self.assertEqual(score, 0.5)

    def test_importance_score_below_min(self):
        score = calculate_importance_score(0)
        self.assertEqual(score, 0.1)

    def test_importance_score_above_max(self):
        score = calculate_importance_score(15)
        self.assertEqual(score, 1.0)

    def test_effort_score_zero_hours(self):
        score = calculate_effort_score(0)
        self.assertEqual(score, 1.0)

    def test_effort_score_one_hour(self):
        score = calculate_effort_score(1)
        self.assertEqual(score, 1.0)

    def test_effort_score_high_hours(self):
        score = calculate_effort_score(20)
        self.assertLess(score, 0.2)

    def test_dependency_score_no_blockers(self):
        task = {'id': '1', 'title': 'Task 1'}
        all_tasks = [task]
        score = calculate_dependency_score(task, all_tasks)
        self.assertEqual(score, 0.5)

    def test_dependency_score_with_blockers(self):
        task1 = {'id': '1', 'title': 'Task 1', 'dependencies': []}
        task2 = {'id': '2', 'title': 'Task 2', 'dependencies': ['1']}
        task3 = {'id': '3', 'title': 'Task 3', 'dependencies': ['1']}
        all_tasks = [task1, task2, task3]
        score = calculate_dependency_score(task1, all_tasks)
        self.assertGreater(score, 0.7)

    def test_priority_score_calculation(self):
        task = {
            'id': '1',
            'title': 'Test Task',
            'due_date': date.today().isoformat(),
            'importance': 8,
            'estimated_hours': 2,
            'dependencies': []
        }
        all_tasks = [task]
        score = calculate_priority_score(task, all_tasks)
        self.assertGreater(score, 0.5)
        self.assertLessEqual(score, 1.0)

    def test_detect_circular_dependencies_no_cycle(self):
        tasks = [
            {'id': '1', 'dependencies': []},
            {'id': '2', 'dependencies': ['1']},
            {'id': '3', 'dependencies': ['2']}
        ]
        cycles = detect_circular_dependencies(tasks)
        self.assertEqual(len(cycles), 0)

    def test_detect_circular_dependencies_with_cycle(self):
        tasks = [
            {'id': '1', 'dependencies': ['2']},
            {'id': '2', 'dependencies': ['1']}
        ]
        cycles = detect_circular_dependencies(tasks)
        self.assertGreater(len(cycles), 0)

    def test_get_strategy_weights_smart_balance(self):
        weights = get_strategy_weights('smart_balance')
        self.assertEqual(weights['urgency'], 0.35)
        self.assertEqual(weights['importance'], 0.30)
        self.assertEqual(weights['effort'], 0.20)
        self.assertEqual(weights['dependencies'], 0.15)

    def test_get_strategy_weights_fastest_wins(self):
        weights = get_strategy_weights('fastest_wins')
        self.assertEqual(weights['effort'], 0.50)

    def test_get_strategy_weights_high_impact(self):
        weights = get_strategy_weights('high_impact')
        self.assertEqual(weights['importance'], 0.60)

    def test_get_strategy_weights_deadline_driven(self):
        weights = get_strategy_weights('deadline_driven')
        self.assertEqual(weights['urgency'], 0.70)

    def test_get_strategy_weights_invalid(self):
        weights = get_strategy_weights('invalid_strategy')
        self.assertEqual(weights['urgency'], 0.35)

    def test_get_score_explanation(self):
        task = {
            'id': '1',
            'title': 'Test Task',
            'due_date': date.today().isoformat(),
            'importance': 9,
            'estimated_hours': 1,
            'dependencies': []
        }
        all_tasks = [task]
        explanation = get_score_explanation(task, all_tasks)
        self.assertIsInstance(explanation, str)
        self.assertGreater(len(explanation), 0)

class APITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.task_data = {
            'title': 'API Test Task',
            'due_date': (date.today() + timedelta(days=7)).isoformat(),
            'estimated_hours': 4.0,
            'importance': 7,
            'dependencies': []
        }

    def test_create_task_api(self):
        response = self.client.post('/api/tasks/', self.task_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'API Test Task')
        self.assertIn('id', response.data)

    def test_get_tasks_list_api(self):
        Task.objects.create(**{
            'title': 'Task 1',
            'due_date': date.today() + timedelta(days=7),
            'estimated_hours': 2.0,
            'importance': 5,
            'dependencies': []
        })
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)

    def test_get_task_detail_api(self):
        task = Task.objects.create(**{
            'title': 'Detail Task',
            'due_date': date.today() + timedelta(days=7),
            'estimated_hours': 3.0,
            'importance': 6,
            'dependencies': []
        })
        response = self.client.get(f'/api/tasks/{task.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Detail Task')

    def test_update_task_api(self):
        task = Task.objects.create(**{
            'title': 'Original Title',
            'due_date': date.today() + timedelta(days=7),
            'estimated_hours': 2.0,
            'importance': 5,
            'dependencies': []
        })
        update_data = {
            'title': 'Updated Title',
            'importance': 8
        }
        response = self.client.put(f'/api/tasks/{task.id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')
        self.assertEqual(response.data['importance'], 8)

    def test_delete_task_api(self):
        task = Task.objects.create(**{
            'title': 'To Delete',
            'due_date': date.today() + timedelta(days=7),
            'estimated_hours': 1.0,
            'importance': 3,
            'dependencies': []
        })
        response = self.client.delete(f'/api/tasks/{task.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_analyze_tasks_api(self):
        tasks_data = [
            {
                'title': 'Urgent Task',
                'due_date': date.today().isoformat(),
                'estimated_hours': 2.0,
                'importance': 9,
                'dependencies': []
            },
            {
                'title': 'Low Priority Task',
                'due_date': (date.today() + timedelta(days=30)).isoformat(),
                'estimated_hours': 8.0,
                'importance': 3,
                'dependencies': []
            }
        ]
        response = self.client.post('/api/analyze/', tasks_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tasks', response.data)
        self.assertIn('strategy', response.data)
        self.assertEqual(len(response.data['tasks']), 2)
        self.assertGreater(response.data['tasks'][0]['priority_score'], 
                          response.data['tasks'][1]['priority_score'])

    def test_analyze_tasks_with_strategy(self):
        tasks_data = [
            {
                'title': 'Quick Task',
                'estimated_hours': 1.0,
                'importance': 5,
                'dependencies': []
            }
        ]
        response = self.client.post('/api/analyze/?strategy=fastest_wins', 
                                   tasks_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['strategy'], 'fastest_wins')

    def test_analyze_tasks_circular_dependency(self):
        tasks_data = [
            {
                'id': '1',
                'title': 'Task 1',
                'dependencies': ['2']
            },
            {
                'id': '2',
                'title': 'Task 2',
                'dependencies': ['1']
            }
        ]
        response = self.client.post('/api/analyze/', tasks_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('circular', response.data['error'].lower())

    def test_analyze_tasks_empty_list(self):
        response = self.client.post('/api/analyze/', [], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_analyze_tasks_invalid_data(self):
        response = self.client.post('/api/analyze/', {'not': 'a list'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task_invalid_importance(self):
        invalid_data = self.task_data.copy()
        invalid_data['importance'] = 15
        response = self.client.post('/api/tasks/', invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_nonexistent_task(self):
        response = self.client.get('/api/tasks/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
