from datetime import date, timedelta
from typing import Dict, List, Optional, Set, Set, Tuple

def calculate_urgency_score(due_date: Optional[str], current_date: date = None) -> float:
    if current_date is None:
        current_date = date.today()
    
    if not due_date:
        return 0.5
    
    try:
        due = date.fromisoformat(due_date) if isinstance(due_date, str) else due_date
    except (ValueError, AttributeError):
        return 0.5
    
    days_until_due = (due - current_date).days
    
    if days_until_due < 0:
        overdue_penalty = abs(days_until_due) * 0.1
        return min(1.0, 0.9 + overdue_penalty)
    
    if days_until_due == 0:
        return 1.0
    
    if days_until_due <= 1:
        return 0.95
    elif days_until_due <= 3:
        return 0.85
    elif days_until_due <= 7:
        return 0.70
    elif days_until_due <= 14:
        return 0.50
    elif days_until_due <= 30:
        return 0.30
    else:
        return 0.10

def calculate_importance_score(importance: int) -> float:
    if importance < 1:
        importance = 1
    elif importance > 10:
        importance = 10
    return importance / 10.0

def calculate_effort_score(estimated_hours: float) -> float:
    if estimated_hours <= 0:
        return 1.0
    
    if estimated_hours <= 1:
        return 1.0
    elif estimated_hours <= 2:
        return 0.9
    elif estimated_hours <= 4:
        return 0.7
    elif estimated_hours <= 8:
        return 0.5
    elif estimated_hours <= 16:
        return 0.3
    else:
        return 0.1

def count_blocked_tasks(task_id: str, all_tasks: List[Dict]) -> int:
    count = 0
    for task in all_tasks:
        if task.get('id') == task_id:
            continue
        deps = task.get('dependencies', [])
        if task_id in deps or str(task_id) in [str(d) for d in deps]:
            count += 1
    return count

def calculate_dependency_score(task: Dict, all_tasks: List[Dict]) -> float:
    task_id = task.get('id') or task.get('title', '')
    blocked_count = count_blocked_tasks(task_id, all_tasks)
    
    if blocked_count == 0:
        return 0.5
    
    if blocked_count >= 5:
        return 1.0
    elif blocked_count >= 3:
        return 0.9
    elif blocked_count >= 2:
        return 0.8
    else:
        return 0.7

def calculate_priority_score(
    task: Dict,
    all_tasks: List[Dict],
    weights: Optional[Dict[str, float]] = None
) -> float:
    if weights is None:
        weights = {
            'urgency': 0.35,
            'importance': 0.30,
            'effort': 0.20,
            'dependencies': 0.15
        }
    
    urgency = calculate_urgency_score(task.get('due_date'))
    importance = calculate_importance_score(task.get('importance', 5))
    effort = calculate_effort_score(task.get('estimated_hours', 0))
    dependencies = calculate_dependency_score(task, all_tasks)
    
    total_score = (
        urgency * weights['urgency'] +
        importance * weights['importance'] +
        effort * weights['effort'] +
        dependencies * weights['dependencies']
    )
    
    return round(total_score, 4)

def get_score_explanation(
    task: Dict,
    all_tasks: List[Dict],
    weights: Optional[Dict[str, float]] = None
) -> str:
    if weights is None:
        weights = {
            'urgency': 0.35,
            'importance': 0.30,
            'effort': 0.20,
            'dependencies': 0.15
        }
    
    urgency = calculate_urgency_score(task.get('due_date'))
    importance = calculate_importance_score(task.get('importance', 5))
    effort = calculate_effort_score(task.get('estimated_hours', 0))
    dependencies = calculate_dependency_score(task, all_tasks)
    
    parts = []
    
    if urgency >= 0.8:
        parts.append("high urgency")
    elif urgency >= 0.5:
        parts.append("moderate urgency")
    else:
        parts.append("low urgency")
    
    if importance >= 0.8:
        parts.append("high importance")
    elif importance >= 0.5:
        parts.append("moderate importance")
    else:
        parts.append("low importance")
    
    if effort >= 0.8:
        parts.append("quick win")
    elif effort <= 0.3:
        parts.append("high effort")
    
    blocked = count_blocked_tasks(task.get('id') or task.get('title', ''), all_tasks)
    if blocked > 0:
        parts.append(f"blocks {blocked} task(s)")
    
    return ", ".join(parts) if parts else "standard priority"

def detect_circular_dependencies(all_tasks: List[Dict]) -> List[List[str]]:
    graph = {}
    task_ids = {}
    
    for idx, task in enumerate(all_tasks):
        task_id = str(task.get('id', idx))
        task_ids[task_id] = task
        graph[task_id] = []
        deps = task.get('dependencies', [])
        for dep in deps:
            dep_str = str(dep)
            graph[task_id].append(dep_str)
    
    def dfs(node: str, visited: Set[str], rec_stack: Set[str], path: List[str]) -> Optional[List[str]]:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                cycle = dfs(neighbor, visited, rec_stack, path)
                if cycle:
                    return cycle
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor)
                return path[cycle_start:] + [neighbor]
        
        rec_stack.remove(node)
        path.pop()
        return None
    
    cycles = []
    visited = set()
    
    for task_id in graph:
        if task_id not in visited:
            cycle = dfs(task_id, visited, set(), [])
            if cycle:
                cycles.append(cycle)
    
    return cycles

def get_strategy_weights(strategy: str) -> Dict[str, float]:
    strategies = {
        'fastest_wins': {
            'urgency': 0.20,
            'importance': 0.20,
            'effort': 0.50,
            'dependencies': 0.10
        },
        'high_impact': {
            'urgency': 0.20,
            'importance': 0.60,
            'effort': 0.10,
            'dependencies': 0.10
        },
        'deadline_driven': {
            'urgency': 0.70,
            'importance': 0.15,
            'effort': 0.10,
            'dependencies': 0.05
        },
        'smart_balance': {
            'urgency': 0.35,
            'importance': 0.30,
            'effort': 0.20,
            'dependencies': 0.15
        }
    }
    return strategies.get(strategy, strategies['smart_balance'])

def detect_circular_dependencies(all_tasks: List[Dict]) -> List[List[str]]:
    graph = {}
    task_ids = {}
    
    for idx, task in enumerate(all_tasks):
        task_id = str(task.get('id', idx))
        task_ids[task_id] = task
        graph[task_id] = []
        deps = task.get('dependencies', [])
        for dep in deps:
            dep_str = str(dep)
            graph[task_id].append(dep_str)
    
    def dfs(node: str, visited: Set[str], rec_stack: Set[str], path: List[str]) -> Optional[List[str]]:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                cycle = dfs(neighbor, visited, rec_stack, path)
                if cycle:
                    return cycle
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor)
                return path[cycle_start:] + [neighbor]
        
        rec_stack.remove(node)
        path.pop()
        return None
    
    cycles = []
    visited = set()
    
    for task_id in graph:
        if task_id not in visited:
            cycle = dfs(task_id, visited, set(), [])
            if cycle:
                cycles.append(cycle)
    
    return cycles

def get_strategy_weights(strategy: str) -> Dict[str, float]:
    strategies = {
        'fastest_wins': {
            'urgency': 0.20,
            'importance': 0.20,
            'effort': 0.50,
            'dependencies': 0.10
        },
        'high_impact': {
            'urgency': 0.20,
            'importance': 0.60,
            'effort': 0.10,
            'dependencies': 0.10
        },
        'deadline_driven': {
            'urgency': 0.70,
            'importance': 0.15,
            'effort': 0.10,
            'dependencies': 0.05
        },
        'smart_balance': {
            'urgency': 0.35,
            'importance': 0.30,
            'effort': 0.20,
            'dependencies': 0.15
        }
    }
    return strategies.get(strategy, strategies['smart_balance'])

