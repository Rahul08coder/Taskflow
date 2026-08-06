// ===== Config & State =====
const API_BASE = "http://127.0.0.1:8000";
let tasks = [];   // in-memory list of tasks, kept in sync with backend + localStorage

const taskListEl = document.getElementById("task-list");
const taskFormEl = document.getElementById("task-form");
const titleInput = document.getElementById("title");
const priorityInput = document.getElementById("priority");
const dueDateInput = document.getElementById("due_date");
const titleError = document.getElementById("title-error");


// ===== Rendering (Requirement #11) =====
function renderTasks() {
    // Clear existing content
    taskListEl.textContent = "";

    if (tasks.length === 0) {
        const emptyMsg = document.createElement("p");
        emptyMsg.textContent = "No tasks yet. Add one above!";
        taskListEl.appendChild(emptyMsg);
        return;
    }

    tasks.forEach((task) => {
        const item = document.createElement("div");
        item.className = "task-item";
        item.dataset.id = task.id;

        // Left side: title + meta info
        const info = document.createElement("div");
        info.className = "task-info";

        const titleEl = document.createElement("div");
        titleEl.className = "task-title";
        titleEl.textContent = task.title;   // textContent, NOT innerHTML — safe from injection

        const metaEl = document.createElement("div");
        metaEl.className = "task-meta";
        metaEl.textContent = `Priority: ${task.priority} | Status: ${task.status} | Due: ${task.due_date || "N/A"}`;

        info.appendChild(titleEl);
        info.appendChild(metaEl);

        // Right side: action buttons
        const actions = document.createElement("div");
        actions.className = "task-actions";

        const editBtn = document.createElement("button");
        editBtn.className = "btn-edit";
        editBtn.textContent = "Edit";
        editBtn.addEventListener("click", () => handleEdit(task.id));

        const deleteBtn = document.createElement("button");
        deleteBtn.className = "btn-delete";
        deleteBtn.textContent = "Delete";
        deleteBtn.addEventListener("click", () => handleDelete(task.id));

        actions.appendChild(editBtn);
        actions.appendChild(deleteBtn);

        item.appendChild(info);
        item.appendChild(actions);
        taskListEl.appendChild(item);
    });
}


// ===== localStorage Caching (Requirement #14) =====
function saveToCache() {
    localStorage.setItem("taskflow_tasks", JSON.stringify(tasks));
}

function loadFromCache() {
    const cached = localStorage.getItem("taskflow_tasks");
    return cached ? JSON.parse(cached) : [];
}


// ===== API Calls =====
async function fetchTasks() {
    try {
        const response = await fetch(`${API_BASE}/tasks`);
        const data = await response.json();
        tasks = data;
        saveToCache();
        renderTasks();
    } catch (error) {
        console.error("Failed to fetch tasks from backend:", error);
        // Cached copy (already rendered on load) stays visible — no blank screen
    }
}

async function createTaskOnServer(taskData) {
    const response = await fetch(`${API_BASE}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(taskData),
    });
    if (!response.ok) throw new Error("Failed to create task");
    return response.json();
}

async function deleteTaskOnServer(taskId) {
    const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
        method: "DELETE",
    });
    if (!response.ok) throw new Error("Failed to delete task");
}

async function updateTaskOnServer(taskId, taskData) {
    const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(taskData),
    });
    if (!response.ok) throw new Error("Failed to update task");
    return response.json();
}


// ===== Validation (Requirement #13) =====
function validateTitle() {
    const value = titleInput.value.trim();
    if (value === "") {
        titleError.textContent = "Title cannot be empty.";
        return false;
    }
    titleError.textContent = "";
    return true;
}

// Clear error as soon as the field becomes valid (live feedback)
titleInput.addEventListener("input", () => {
    if (titleInput.value.trim() !== "") {
        titleError.textContent = "";
    }
});


// ===== Add Task (Requirement #12) =====
taskFormEl.addEventListener("submit", async (event) => {
    event.preventDefault();   // stop default form submission/page reload

    if (!validateTitle()) {
        return;   // don't submit if title is blank
    }

    const newTaskData = {
        title: titleInput.value.trim(),
        priority: priorityInput.value,
        due_date: dueDateInput.value.trim() || null,
        project_id: 1,   // TODO: replace with real project selection if needed
    };

    try {
        const createdTask = await createTaskOnServer(newTaskData);
        tasks.push(createdTask);
        saveToCache();
        renderTasks();
        taskFormEl.reset();
    } catch (error) {
        console.error("Error adding task:", error);
    }
});


// ===== Delete Task (Requirement #12) =====
async function handleDelete(taskId) {
    try {
        await deleteTaskOnServer(taskId);
        tasks = tasks.filter((t) => t.id !== taskId);
        saveToCache();
        renderTasks();
    } catch (error) {
        console.error("Error deleting task:", error);
    }
}


// ===== Edit Task (Requirement #12) =====
async function handleEdit(taskId) {
    const task = tasks.find((t) => t.id === taskId);
    if (!task) return;

    const newTitle = prompt("Edit task title:", task.title);
    if (newTitle === null) return;   // user cancelled

    const trimmedTitle = newTitle.trim();
    if (trimmedTitle === "") {
        alert("Title cannot be empty.");
        return;
    }

    try {
        const updatedTask = await updateTaskOnServer(taskId, { title: trimmedTitle });
        const index = tasks.findIndex((t) => t.id === taskId);
        tasks[index] = updatedTask;
        saveToCache();
        renderTasks();
    } catch (error) {
        console.error("Error updating task:", error);
    }
}


// ===== Initial Load (Requirement #14) =====
// 1. Render from cache immediately (no blank screen)
tasks = loadFromCache();
renderTasks();

// 2. Then fetch fresh data from backend and re-render
fetchTasks();