const API_BASE_URL = 'http://localhost:8000/api';

let tasks = [];
let editingTaskId = null;

const taskListEl = document.getElementById('taskList');
const taskModal = document.getElementById('taskModal');
const taskForm = document.getElementById('taskForm');
const addTaskBtn = document.getElementById('addTaskBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const cancelBtn = document.getElementById('cancelBtn');
const closeModal = document.querySelector('.close');
const toast = document.getElementById('toast');

addTaskBtn.addEventListener('click', () => openModal());
cancelBtn.addEventListener('click', () => closeModalFunc());
closeModal.addEventListener('click', () => closeModalFunc());
window.addEventListener('click', (e) => {
    if (e.target === taskModal) closeModalFunc();
});

taskForm.addEventListener('submit', handleTaskSubmit);
analyzeBtn.addEventListener('click', analyzeTasks);

loadTasks();

async function loadTasks() {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/`);
        if (response.ok) {
            tasks = await response.json();
            renderTasks();
        } else {
            showToast('Failed to load tasks', 'error');
        }
    } catch (error) {
        showToast('Error connecting to server', 'error');
        console.error('Error loading tasks:', error);
    }
}

function renderTasks() {
    if (tasks.length === 0) {
        taskListEl.innerHTML = '<div class="empty-state"><p>No tasks yet. Click "Add New Task" to get started.</p></div>';
        return;
    }

    taskListEl.innerHTML = tasks.map(task => `
        <div class="task-item">
            <h3>${escapeHtml(task.title)}</h3>
            <div class="task-meta">
                ${task.due_date ? `<span>📅 Due: ${formatDate(task.due_date)}</span>` : ''}
                ${task.estimated_hours > 0 ? `<span>⏱️ ${task.estimated_hours}h</span>` : ''}
                <span>⭐ Importance: ${task.importance}/10</span>
                ${task.dependencies && task.dependencies.length > 0 ? `<span>🔗 Depends on: ${task.dependencies.join(', ')}</span>` : ''}
            </div>
            <div class="task-actions">
                <button class="btn btn-edit" onclick="editTask(${task.id})">Edit</button>
                <button class="btn btn-danger" onclick="deleteTask(${task.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

function openModal(task = null) {
    editingTaskId = task ? task.id : null;
    document.getElementById('modalTitle').textContent = task ? 'Edit Task' : 'Add Task';
    document.getElementById('taskId').value = task ? task.id : '';
    document.getElementById('title').value = task ? task.title : '';
    document.getElementById('dueDate').value = task && task.due_date ? task.due_date : '';
    document.getElementById('estimatedHours').value = task ? task.estimated_hours : 0;
    document.getElementById('importance').value = task ? task.importance : 5;
    document.getElementById('dependencies').value = task && task.dependencies ? task.dependencies.join(', ') : '';
    taskModal.style.display = 'block';
}

function closeModalFunc() {
    taskModal.style.display = 'none';
    taskForm.reset();
    editingTaskId = null;
}

async function handleTaskSubmit(e) {
    e.preventDefault();
    
    const formData = {
        title: document.getElementById('title').value,
        due_date: document.getElementById('dueDate').value || null,
        estimated_hours: parseFloat(document.getElementById('estimatedHours').value) || 0,
        importance: parseInt(document.getElementById('importance').value) || 5,
        dependencies: document.getElementById('dependencies').value
            ? document.getElementById('dependencies').value.split(',').map(d => d.trim()).filter(d => d)
            : []
    };

    try {
        let response;
        if (editingTaskId) {
            response = await fetch(`${API_BASE_URL}/tasks/${editingTaskId}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
        } else {
            response = await fetch(`${API_BASE_URL}/tasks/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
        }

        if (response.ok) {
            showToast(editingTaskId ? 'Task updated successfully' : 'Task created successfully', 'success');
            closeModalFunc();
            loadTasks();
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to save task', 'error');
        }
    } catch (error) {
        showToast('Error saving task', 'error');
        console.error('Error saving task:', error);
    }
}

async function editTask(id) {
    const task = tasks.find(t => t.id === id.toString() || t.id === id);
    if (task) {
        openModal(task);
    }
}

async function deleteTask(id) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/tasks/${id}/`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showToast('Task deleted successfully', 'success');
            loadTasks();
        } else {
            showToast('Failed to delete task', 'error');
        }
    } catch (error) {
        showToast('Error deleting task', 'error');
        console.error('Error deleting task:', error);
    }
}

async function analyzeTasks() {
    if (tasks.length === 0) {
        showToast('Please add some tasks first', 'error');
        return;
    }

    const strategy = document.getElementById('strategy').value;
    const tasksForAnalysis = tasks.map(task => ({
        id: task.id,
        title: task.title,
        due_date: task.due_date,
        estimated_hours: task.estimated_hours,
        importance: task.importance,
        dependencies: task.dependencies || []
    }));

    try {
        const response = await fetch(`${API_BASE_URL}/analyze/?strategy=${strategy}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(tasksForAnalysis)
        });

        if (response.ok) {
            const result = await response.json();
            renderAnalysisResults(result);
            showToast('Analysis completed successfully', 'success');
        } else {
            const error = await response.json();
            showToast(error.error || 'Analysis failed', 'error');
            if (error.cycles) {
                console.error('Circular dependencies:', error.cycles);
            }
        }
    } catch (error) {
        showToast('Error analyzing tasks', 'error');
        console.error('Error analyzing tasks:', error);
    }
}

function renderAnalysisResults(result) {
    const resultsEl = document.getElementById('analysisResults');
    
    if (!result.tasks || result.tasks.length === 0) {
        resultsEl.innerHTML = '<div class="empty-state"><p>No results to display</p></div>';
        return;
    }

    resultsEl.innerHTML = `
        <div style="margin-bottom: 15px; padding: 12px; background: #e7f3ff; border-radius: 6px;">
            <strong>Strategy:</strong> ${formatStrategyName(result.strategy)} | 
            <strong>Total Tasks:</strong> ${result.total_tasks}
        </div>
        ${result.tasks.map(task => `
            <div class="analysis-item">
                <h3>
                    ${escapeHtml(task.title)}
                    <span class="priority-score">Score: ${task.priority_score.toFixed(3)}</span>
                </h3>
                <div class="task-meta">
                    ${task.due_date ? `<span>📅 Due: ${formatDate(task.due_date)}</span>` : ''}
                    ${task.estimated_hours > 0 ? `<span>⏱️ ${task.estimated_hours}h</span>` : ''}
                    <span>⭐ Importance: ${task.importance}/10</span>
                    ${task.dependencies && task.dependencies.length > 0 ? `<span>🔗 Depends on: ${task.dependencies.join(', ')}</span>` : ''}
                </div>
                <div class="explanation">
                    💡 ${escapeHtml(task.explanation)}
                </div>
            </div>
        `).join('')}
    `;
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatStrategyName(strategy) {
    const names = {
        'smart_balance': 'Smart Balance',
        'fastest_wins': 'Fastest Wins',
        'high_impact': 'High Impact',
        'deadline_driven': 'Deadline Driven'
    };
    return names[strategy] || strategy;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = 'success') {
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

