# Task Analyzer

A Django REST API application for task management and intelligent priority scoring. The system helps users prioritize tasks based on urgency, importance, effort, and dependencies.

## Features

- **Task Management**: Full CRUD operations for tasks
- **Priority Scoring**: Intelligent algorithm that calculates task priority based on multiple factors
- **Multiple Strategies**: Choose from different prioritization strategies
- **Dependency Management**: Track task dependencies with circular dependency detection
- **RESTful API**: Clean, well-documented API endpoints
- **Admin Interface**: Django admin for task management

## Technology Stack

- **Backend**: Django 4.2.7
- **API**: Django REST Framework 3.14.0
- **CORS**: django-cors-headers 4.3.1
- **Database**: SQLite

## Installation

### Prerequisites

- Python 3.9 or higher
- pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd task-analyzer/backend
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create superuser (optional):
```bash
python manage.py createsuperuser
```

6. Run development server:
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Task Management

#### List All Tasks
```
GET /api/tasks/
```

#### Create Task
```
POST /api/tasks/
Content-Type: application/json

{
  "title": "Task title",
  "due_date": "2024-12-31",
  "estimated_hours": 4.0,
  "importance": 7,
  "dependencies": []
}
```

#### Get Task Details
```
GET /api/tasks/<id>/
```

#### Update Task
```
PUT /api/tasks/<id>/
Content-Type: application/json

{
  "title": "Updated title",
  "importance": 8
}
```

#### Delete Task
```
DELETE /api/tasks/<id>/
```

### Task Analysis

#### Analyze and Prioritize Tasks
```
POST /api/analyze/?strategy=smart_balance
Content-Type: application/json

[
  {
    "id": "1",
    "title": "Task 1",
    "due_date": "2024-12-15",
    "estimated_hours": 2.0,
    "importance": 8,
    "dependencies": []
  },
  {
    "id": "2",
    "title": "Task 2",
    "due_date": "2024-12-20",
    "estimated_hours": 6.0,
    "importance": 5,
    "dependencies": ["1"]
  }
]
```

**Query Parameters:**
- `strategy`: Prioritization strategy (optional, default: `smart_balance`)
  - `smart_balance`: Balanced approach (default)
  - `fastest_wins`: Prioritize quick tasks
  - `high_impact`: Focus on important tasks
  - `deadline_driven`: Emphasize urgent tasks

**Response:**
```json
{
  "tasks": [
    {
      "id": "1",
      "title": "Task 1",
      "due_date": "2024-12-15",
      "estimated_hours": 2.0,
      "importance": 8,
      "dependencies": [],
      "priority_score": 0.8234,
      "explanation": "high urgency, high importance, quick win"
    }
  ],
  "strategy": "smart_balance",
  "total_tasks": 2
}
```

## Priority Scoring Algorithm

The system calculates priority scores using a weighted formula:

- **Urgency (35%)**: Based on due date proximity
  - Overdue tasks get highest scores
  - Tasks due today get score 1.0
  - Future tasks get decreasing scores based on days until due
  
- **Importance (30%)**: User-defined importance (1-10 scale)
  - Normalized to 0.1 - 1.0 range
  
- **Effort (20%)**: Estimated hours (inverse relationship)
  - Lower effort = higher score
  - Quick wins (≤1 hour) get score 1.0
  
- **Dependencies (15%)**: Number of tasks blocked by this task
  - More blocked tasks = higher priority

### Scoring Strategies

1. **smart_balance** (default)
   - Urgency: 35%, Importance: 30%, Effort: 20%, Dependencies: 15%

2. **fastest_wins**
   - Urgency: 20%, Importance: 20%, Effort: 50%, Dependencies: 10%

3. **high_impact**
   - Urgency: 20%, Importance: 60%, Effort: 10%, Dependencies: 10%

4. **deadline_driven**
   - Urgency: 70%, Importance: 15%, Effort: 10%, Dependencies: 5%

## Task Model

### Fields

- `title` (required): Task title, max 200 characters
- `due_date` (optional): Due date in YYYY-MM-DD format
- `estimated_hours` (optional): Estimated completion time, default 0
- `importance` (optional): Importance level 1-10, default 5
- `dependencies` (optional): List of task IDs this task depends on
- `created_at`: Automatic timestamp
- `updated_at`: Automatic timestamp

### Validation

- Importance must be between 1 and 10
- Estimated hours cannot be negative
- Dependencies must be a list of strings or integers
- Circular dependencies are detected and rejected

## Testing

Run the test suite:

```bash
python manage.py test
```

The test suite includes:
- Model validation tests
- Scoring algorithm tests
- API endpoint tests
- Circular dependency detection tests

## Admin Interface

Access the Django admin at `http://localhost:8000/admin/` after creating a superuser.

Features:
- List view with filtering and search
- Task creation and editing
- Field validation

## Example Usage

### Python Example

```python
import requests

BASE_URL = "http://localhost:8000/api"

tasks = [
    {
        "title": "Fix critical bug",
        "due_date": "2024-12-10",
        "estimated_hours": 4.0,
        "importance": 9,
        "dependencies": []
    },
    {
        "title": "Update documentation",
        "due_date": "2024-12-20",
        "estimated_hours": 2.0,
        "importance": 5,
        "dependencies": []
    }
]

response = requests.post(
    f"{BASE_URL}/analyze/?strategy=deadline_driven",
    json=tasks
)

prioritized = response.json()["tasks"]
for task in prioritized:
    print(f"{task['title']}: {task['priority_score']}")
```

### JavaScript Example

```javascript
const tasks = [
  {
    title: "Review code",
    due_date: "2024-12-15",
    estimated_hours: 2.0,
    importance: 7,
    dependencies: []
  }
];

fetch('http://localhost:8000/api/analyze/?strategy=smart_balance', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(tasks)
})
.then(response => response.json())
.then(data => {
  console.log('Prioritized tasks:', data.tasks);
});
```

## Project Structure

```
task-analyzer/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── task_analyzer/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── tasks/
│       ├── models.py
│       ├── views.py
│       ├── serializers.py
│       ├── scoring.py
│       ├── urls.py
│       ├── admin.py
│       └── tests.py
└── frontend/
```

## Development

### Running Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Creating Superuser

```bash
python manage.py createsuperuser
```

### Running Tests

```bash
python manage.py test tasks
```

## License

This project is part of an assignment submission.

## Contributing

This is an assignment project. For questions or issues, please contact the project maintainer.

