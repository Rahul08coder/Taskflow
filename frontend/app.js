// =====================================================
// TaskFlow Ops Hub — auth-gated. Every request below sends
// the session token from login; a missing/invalid token
// bounces the user back to login.html.
// =====================================================

// =====================================================
// Configuration & Constants
// =====================================================

// Base URL for all API calls to the backend server
const API_BASE = "http://127.0.0.1:8000";

// Local storage key for caching tasks data to improve performance
const CACHE_KEY = "taskflow_tasks_v3";
const THEME_KEY = "taskflow_theme";

function applyTheme(theme) {
    const isLight = theme === "light";
    document.documentElement.dataset.theme = isLight ? "light" : "dark";
    localStorage.setItem(THEME_KEY, isLight ? "light" : "dark");
    const icon = themeToggle.querySelector("i");
    const label = themeToggle.querySelector("span");
    icon.className = `ti ${isLight ? "ti-moon" : "ti-sun"}`;
    label.textContent = isLight ? "Dark mode" : "Light mode";
    themeToggle.setAttribute("aria-label", `Switch to ${isLight ? "dark" : "light"} mode`);
}

// ---- Auth gate (runs before anything else) ----
// Check if user is authenticated by looking for token in localStorage
// If no token exists, redirect to login page
const token = localStorage.getItem("taskflow_token");
if (!token) {
    window.location.href = "login.html";
}

// Parse and store current user information from localStorage
const currentUser = JSON.parse(localStorage.getItem("taskflow_user") || "null");

// Helper function to create HTTP headers with authentication token
function authHeaders(extra) {
    return Object.assign({ Authorization: `Bearer ${token}` }, extra || {});
}

// If the token has gone stale (e.g. logged out elsewhere), any 401 from the
// backend sends the user back to login and clears the dead session.
function handleAuthFailure(res) {
    if (res.status === 401) {
        localStorage.removeItem("taskflow_token");
        localStorage.removeItem("taskflow_user");
        window.location.href = "login.html";
        return true;
    }
    return false;
}

// Global state variables
let allTasks = [];  // Stores all tasks fetched from backend
let projects = [];  // Stores all projects fetched from backend
let searchAlgo = "binary";  // Default search algorithm for task search
const TASKS_PER_PAGE = 5;
let currentTaskPage = 1;

// ---- Shared element refs ----
// Get DOM element references for navigation and main UI components
const viewTitle = document.getElementById("view-title");
const viewSubtitle = document.getElementById("view-subtitle");
const topbar = document.querySelector(".topbar");
const navItems = document.querySelectorAll(".nav-item[data-view]");
const viewPanels = document.querySelectorAll(".view-panel[data-view]");
const navAdmin = document.getElementById("nav-admin");
const appShell = document.querySelector(".app-shell");
const mobileMenuToggle = document.getElementById("mobile-menu-toggle");
const mobileControls = document.getElementById("mobile-controls");
const themeToggle = document.getElementById("theme-toggle");

// Top bar elements
const sidebarLogoutBtn = document.getElementById("sidebar-logout-btn");
const sidebarUserName = document.getElementById("sidebar-user-name");
const sidebarUserEmail = document.getElementById("sidebar-user-email");
const sidebarUserAvatar = document.getElementById("sidebar-user-avatar");
const topbarRight = document.querySelector(".topbar-right");
const topbarRightHome = document.createComment("topbar controls home");
topbarRight.after(topbarRightHome);

applyTheme(localStorage.getItem(THEME_KEY) || "dark");
themeToggle.addEventListener("click", () => {
    applyTheme(document.documentElement.dataset.theme === "light" ? "dark" : "light");
});

// Chat widget elements
const chatFab = document.getElementById("chat-fab");
const chatPanel = document.getElementById("chat-panel");
const chatCloseBtn = document.getElementById("chat-close-btn");
const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatSendBtn = document.getElementById("chat-send-btn");

// Notification elements
const notifBellBtn = document.getElementById("notif-bell-btn");
const notifCountBadge = document.getElementById("notif-count-badge");
const notifDropdown = document.getElementById("notif-dropdown");
const notifList = document.getElementById("notif-list");
const notifMarkAllBtn = document.getElementById("notif-mark-all-btn");

// Tasks view elements
const addTaskForm = document.getElementById("add-task-form");
const taskProject = document.getElementById("task-project");
const taskTitleInput = document.getElementById("task-title");
const titleError = document.getElementById("title-error");
const taskPriority = document.getElementById("task-priority");
const taskDueDate = document.getElementById("task-due-date");
const taskDueTime = document.getElementById("task-due-time");
const taskListContainer = document.getElementById("task-list-container");
const taskCountBadge = document.getElementById("task-count-badge");
const cacheIndicator = document.getElementById("cache-indicator");
const projectFilterSelect = document.getElementById("project-filter-select");
const taskPagination = document.getElementById("task-pagination");

// Edit task modal elements
const editTaskModal = document.getElementById("edit-task-modal");
const editTaskForm = document.getElementById("edit-task-form");
const editTaskTitle = document.getElementById("edit-task-title");
const editTaskPriority = document.getElementById("edit-task-priority");
const editTaskStatus = document.getElementById("edit-task-status");
const editTaskDueDate = document.getElementById("edit-task-due-date");
const editTaskError = document.getElementById("edit-task-error");
const editTaskCloseBtn = document.getElementById("edit-task-close-btn");
const editTaskCancelBtn = document.getElementById("edit-task-cancel-btn");
const markCompleteBtn = document.getElementById("mark-complete-btn");
let editingTaskId = null;

// Quick Add view elements
const quickAddForm = document.getElementById("quick-add-form");
const quickAddProject = document.getElementById("quick-add-project");
const quickAddDesc = document.getElementById("quick-add-desc");
const quickAddError = document.getElementById("quick-add-error");
const previewTitle = document.getElementById("preview-title");
const previewPriority = document.getElementById("preview-priority");
const previewDue = document.getElementById("preview-due");
const previewProject = document.getElementById("preview-project");

// Search + Sort view elements
const searchTitleInput = document.getElementById("search-title-input");
const algoButtons = document.querySelectorAll(".algo-btn");
const searchBtn = document.getElementById("search-btn");
const clearSearchBtn = document.getElementById("clear-search-btn");
const notificationBanner = document.getElementById("search-notification");
const searchResults = document.getElementById("search-results");
const sortSelect = document.getElementById("sort-select");
const applySortBtn = document.getElementById("apply-sort-btn");

// Stats view elements
const statsProjectSelect = document.getElementById("stats-project-select");
const refreshStatsBtn = document.getElementById("refresh-stats-btn");
const statsContainer = document.getElementById("stats-container");

// Dashboard view elements
const kpiTotalTasks = document.getElementById("kpi-total-tasks");
const kpiProjects = document.getElementById("kpi-projects");
const kpiPending = document.getElementById("kpi-pending");
const kpiDoneRate = document.getElementById("kpi-done-rate");
const dashboardProjects = document.getElementById("dashboard-projects");
const dashboardRecent = document.getElementById("dashboard-recent");

// Projects view elements
const projectsGrid = document.getElementById("projects-grid");
const createProjectForm = document.getElementById("create-project-form");
const newProjectName = document.getElementById("new-project-name");
const projectError = document.getElementById("project-error");

// Admin view elements (was "Team")
const teamList = document.getElementById("team-list");
const adminDetailCard = document.getElementById("admin-detail-card");
const adminDetailTitle = document.getElementById("admin-detail-title");
const adminDetailProjects = document.getElementById("admin-detail-projects");
const adminDetailTasks = document.getElementById("admin-detail-tasks");
const adminDetailClose = document.getElementById("admin-detail-close");

// View metadata for title and subtitle display
const VIEW_META = {
    dashboard: ["Dashboard", "Command center for projects, tasks, and activity"],
    projects: ["Projects", "Browse ownership, progress, and project-level task grouping"],
    tasks: ["Tasks", "Full CRUD list with client validation, cache, and live backend sync"],
    quickadd: ["Quick Add", "Text sentence in, structured task out"],
    search: ["Search + Sort", "Exact title search, priority sorting, algorithm-friendly UI"],
    stats: ["Stats", "Counts and status distribution via the project stats endpoint"],
    team: ["Admin", "Every registered user, and how many projects/tasks they own"],
};

// =====================================================
// View switching functionality
// =====================================================

// Function to switch between different views (dashboard, projects, tasks, etc.)
function setActiveView(view) {
    // Update navigation items active state
    navItems.forEach((item) => item.classList.toggle("active", item.dataset.view === view));
    // Show/hide view panels
    viewPanels.forEach((panel) => panel.classList.toggle("active", panel.dataset.view === view));

    // Update title and subtitle based on selected view
    const [title, subtitle] = VIEW_META[view] || ["", ""];
    viewTitle.textContent = title;
    viewSubtitle.textContent = subtitle;
    topbar.classList.toggle("dashboard-view", view === "dashboard");

    // Render specific view content when switching
    if (view === "dashboard") renderDashboard();
    if (view === "projects") renderProjectsGrid();
    if (view === "team") loadAdminUsers();
}

// Add click event listeners to navigation items for view switching
navItems.forEach((item) => {
    item.addEventListener("click", () => {
        setActiveView(item.dataset.view);
        closeMobileMenu();
    });
});

function closeMobileMenu() {
    appShell.classList.remove("mobile-menu-open");
    mobileMenuToggle.setAttribute("aria-expanded", "false");
    mobileMenuToggle.setAttribute("aria-label", "Open menu");
}

function toggleMobileMenu() {
    const isOpen = appShell.classList.contains("mobile-menu-open");
    if (isOpen) {
        closeMobileMenu();
        return;
    }
    if (window.innerWidth <= 640 && topbarRight.parentElement !== mobileControls) {
        mobileControls.appendChild(topbarRight);
    }
    appShell.classList.add("mobile-menu-open");
    mobileMenuToggle.setAttribute("aria-expanded", "true");
    mobileMenuToggle.setAttribute("aria-label", "Close menu");
}

mobileMenuToggle.addEventListener("click", toggleMobileMenu);
window.addEventListener("resize", () => {
    if (window.innerWidth > 640 && topbarRight.parentElement === mobileControls) {
        topbarRightHome.before(topbarRight);
        closeMobileMenu();
    }
});

// =====================================================
// Logout functionality
// =====================================================

// Logout buttons clear the session and redirect to login.
async function logout() {
    try {
        await fetch(`${API_BASE}/auth/logout`, {
            method: "POST",
            headers: authHeaders(),
        });
    } catch (e) {
        console.error("Logout request failed (clearing session locally anyway):", e);
    }
    localStorage.removeItem("taskflow_token");
    localStorage.removeItem("taskflow_user");
    window.location.href = "login.html";
}

sidebarLogoutBtn.addEventListener("click", logout);

// =====================================================
// Projects management (loaded once, reused across views)
// =====================================================

// Fetch all projects from backend and populate dropdowns
async function fetchProjects() {
    try {
        const res = await fetch(`${API_BASE}/projects`, { headers: authHeaders() });
        if (handleAuthFailure(res)) return;
        projects = await res.json();
    } catch (e) {
        console.error("Failed to fetch projects:", e);
        projects = [];
    }

    // Populate project dropdowns in Tasks and Quick Add views
    [quickAddProject, taskProject].forEach((select) => {
        select.textContent = "";
        projects.forEach((p) => {
            const opt = document.createElement("option");
            opt.value = p.id;
            opt.textContent = p.name;
            select.appendChild(opt);
        });
    });

    // Populate project filter dropdown in Tasks view
    projectFilterSelect.textContent = "";
    const allOpt = document.createElement("option");
    allOpt.value = "all";
    allOpt.textContent = "All projects";
    projectFilterSelect.appendChild(allOpt);
    projects.forEach((p) => {
        const opt = document.createElement("option");
        opt.value = String(p.id);
        opt.textContent = p.name;
        projectFilterSelect.appendChild(opt);
    });

    // Populate project dropdown in Stats view
    statsProjectSelect.textContent = "";
    projects.forEach((p) => {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = p.name;
        statsProjectSelect.appendChild(opt);
    });
}

// Helper function to get project name by ID
function getProjectName(projectId) {
    const match = projects.find((p) => p.id === projectId);
    return match ? match.name : `Project #${projectId}`;
}

// =====================================================
// Task list rendering functions
// =====================================================

// Icon mapping for task statuses
const STATUS_ICONS = {
    pending: "ti-clock",
    in_progress: "ti-loader-2",
    completed: "ti-circle-check",
};

// Create status pill with icon and text
function createStatusPill(status) {
    const pill = document.createElement("span");
    pill.className = `status-pill status-${status}`;

    const icon = document.createElement("i");
    icon.className = `ti ${STATUS_ICONS[status] || "ti-circle"}`;
    icon.setAttribute("aria-hidden", "true");

    pill.appendChild(icon);
    pill.appendChild(document.createTextNode(" " + status.replace("_", " ")));
    return pill;
}

// Create complete task element with title, metadata, and action buttons
function createTaskElement(task) {
    const item = document.createElement("div");
    item.className = "task-item";
    item.dataset.id = task.id;
    item.tabIndex = 0;
    item.setAttribute("role", "button");
    item.setAttribute("aria-label", `Edit task: ${task.title}`);
    item.addEventListener("click", () => handleEdit(task.id));
    item.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            handleEdit(task.id);
        }
    });

    const info = document.createElement("div");
    info.className = "task-info";

    const titleEl = document.createElement("div");
    titleEl.className = "task-title";
    titleEl.textContent = task.title;

    const metaEl = document.createElement("div");
    metaEl.className = "task-meta";

    const contextEl = document.createElement("span");
    contextEl.textContent = `${getProjectName(task.project_id)} · due ${task.due_date ? task.due_date : "—"}`;

    const priorityPill = document.createElement("span");
    priorityPill.className = `pill pill-${task.priority}`;
    priorityPill.textContent = task.priority;

    const statusPill = createStatusPill(task.status);

    metaEl.appendChild(contextEl);
    metaEl.appendChild(priorityPill);
    metaEl.appendChild(statusPill);

    info.appendChild(titleEl);
    info.appendChild(metaEl);

    const actions = document.createElement("div");
    actions.className = "task-actions";

    // Edit button
    const editBtn = document.createElement("button");
    editBtn.className = "icon-btn edit";
    editBtn.textContent = "✎";
    editBtn.title = "Edit";
    editBtn.addEventListener("click", (event) => {
        event.stopPropagation();
        handleEdit(task.id);
    });

    // Delete button
    const deleteBtn = document.createElement("button");
    deleteBtn.className = "icon-btn delete";
    deleteBtn.textContent = "×";
    deleteBtn.title = "Delete";
    deleteBtn.addEventListener("click", (event) => {
        event.stopPropagation();
        handleDelete(task.id);
    });

    actions.appendChild(editBtn);
    actions.appendChild(deleteBtn);

    item.appendChild(info);
    item.appendChild(actions);
    return item;
}

// Render tasks into a container element
function renderTaskList(container, tasks) {
    container.textContent = "";
    if (tasks.length === 0) {
        const empty = document.createElement("p");
        empty.textContent = "No tasks to show.";
        container.appendChild(empty);
        return;
    }
    tasks.forEach((t) => container.appendChild(createTaskElement(t)));
}

function renderTaskPagination(totalTasks) {
    const totalPages = Math.ceil(totalTasks / TASKS_PER_PAGE);
    taskPagination.textContent = "";
    taskPagination.hidden = totalPages <= 1;
    if (totalPages <= 1) return;

    const addPageButton = (label, page, disabled, active) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "pagination-btn";
        button.textContent = label;
        button.disabled = disabled;
        if (active) {
            button.classList.add("active");
            button.setAttribute("aria-current", "page");
        }
        button.addEventListener("click", () => {
            currentTaskPage = page;
            renderFilteredTaskList();
        });
        taskPagination.appendChild(button);
    };

    addPageButton("Previous", currentTaskPage - 1, currentTaskPage === 1, false);
    for (let page = 1; page <= totalPages; page += 1) {
        addPageButton(String(page), page, false, page === currentTaskPage);
    }
    addPageButton("Next", currentTaskPage + 1, currentTaskPage === totalPages, false);
}

// Render filtered task list based on project filter selection
function renderFilteredTaskList() {
    let list = allTasks;
    const pf = projectFilterSelect.value;
    if (pf !== "all") {
        list = list.filter((t) => String(t.project_id) === pf);
    }
    taskCountBadge.textContent = list.length;
    const totalPages = Math.max(1, Math.ceil(list.length / TASKS_PER_PAGE));
    currentTaskPage = Math.min(currentTaskPage, totalPages);
    const start = (currentTaskPage - 1) * TASKS_PER_PAGE;
    renderTaskList(taskListContainer, list.slice(start, start + TASKS_PER_PAGE));
    renderTaskPagination(list.length);
}

// Event listener for project filter change
projectFilterSelect.addEventListener("change", () => {
    currentTaskPage = 1;
    renderFilteredTaskList();
});

// =====================================================
// Caching + fetching tasks
// =====================================================

// Save tasks to localStorage cache
function saveCache(tasks) {
    try {
        localStorage.setItem(CACHE_KEY, JSON.stringify(tasks));
    } catch (e) {
        console.error("Failed to cache tasks:", e);
    }
}

// Load tasks from cache and render immediately for better UX
function loadCacheAndRender() {
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) return;
    try {
        allTasks = JSON.parse(cached);
        cacheIndicator.hidden = false;
        renderFilteredTaskList();
    } catch (e) {
        console.error("Failed to parse cached tasks:", e);
    }
}

// Fetch tasks from backend with optional sort parameter
async function loadTasks(sort) {
    const sortParam = sort || "none";
    const url = sortParam === "none" ? `${API_BASE}/tasks` : `${API_BASE}/tasks?sort=${sortParam}`;

    try {
        const res = await fetch(url, { headers: authHeaders() });
        if (handleAuthFailure(res)) return;
        const data = await res.json();
        allTasks = data;
        currentTaskPage = 1;
        saveCache(data);
        cacheIndicator.hidden = true;
        renderFilteredTaskList();
    } catch (e) {
        console.error("Failed to fetch tasks:", e);
    }
}

// =====================================================
// Add Task functionality (Tasks view)
// =====================================================

// Clear error message when user types in title field
taskTitleInput.addEventListener("input", () => {
    if (taskTitleInput.value.trim() !== "") titleError.textContent = "";
});

// Handle task creation form submission
addTaskForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    // Validate title
    const title = taskTitleInput.value.trim();
    if (!title) {
        titleError.textContent = "Title cannot be empty.";
        return;
    }
    titleError.textContent = "";

    // Combine date and time into single due_date string if both provided
    const dateVal = taskDueDate.value;
    const timeVal = taskDueTime.value;
    let due_date = null;
    if (dateVal) due_date = timeVal ? `${dateVal} ${timeVal}` : dateVal;

    const payload = {
        title,
        priority: taskPriority.value,
        status: "pending",
        due_date,
        project_id: Number(taskProject.value),
    };

    try {
        const res = await fetch(`${API_BASE}/tasks`, {
            method: "POST",
            headers: authHeaders({ "Content-Type": "application/json" }),
            body: JSON.stringify(payload),
        });
        if (handleAuthFailure(res)) return;
        if (!res.ok) {
            titleError.textContent = "Could not create task — check the fields.";
            return;
        }
        addTaskForm.reset();  // Clear form after successful creation
        await loadTasks(sortSelect.value);  // Refresh task list
        await refreshNotifications();  // Update notifications
    } catch (e) {
        console.error("Add task failed:", e);
        titleError.textContent = "Network error — check the backend is running.";
    }
});

// =====================================================
// Edit / Delete task functionality
// =====================================================

function handleEdit(taskId) {
    const task = allTasks.find((t) => t.id === taskId);
    if (!task) return;

    editingTaskId = taskId;
    editTaskTitle.value = task.title;
    editTaskPriority.value = task.priority;
    editTaskStatus.value = task.status;
    editTaskDueDate.value = task.due_date ? task.due_date.slice(0, 10) : "";
    editTaskError.textContent = "";
    editTaskModal.hidden = false;
    document.body.classList.add("modal-open");
    editTaskTitle.focus();
}

function closeEditTaskModal() {
    editTaskModal.hidden = true;
    document.body.classList.remove("modal-open");
    editingTaskId = null;
}

async function saveTaskChanges(statusOverride) {
    if (!editingTaskId) return;
    const trimmed = editTaskTitle.value.trim();
    if (!trimmed) {
        editTaskError.textContent = "Title cannot be empty.";
        return;
    }

    const payload = {
        title: trimmed,
        priority: editTaskPriority.value,
        status: statusOverride || editTaskStatus.value,
        due_date: editTaskDueDate.value || null,
    };

    try {
        const res = await fetch(`${API_BASE}/tasks/${editingTaskId}`, {
            method: "PUT",
            headers: authHeaders({ "Content-Type": "application/json" }),
            body: JSON.stringify(payload),
        });
        if (handleAuthFailure(res)) return;
        if (!res.ok) {
            editTaskError.textContent = "Could not save changes. Please check the fields.";
            return;
        }
        closeEditTaskModal();
        await loadTasks(sortSelect.value);
        await refreshNotifications();
    } catch (e) {
        console.error("Edit failed:", e);
        editTaskError.textContent = "Network error. Please try again.";
    }
}

editTaskForm.addEventListener("submit", (event) => {
    event.preventDefault();
    saveTaskChanges();
});

markCompleteBtn.addEventListener("click", () => saveTaskChanges("completed"));
editTaskCloseBtn.addEventListener("click", closeEditTaskModal);
editTaskCancelBtn.addEventListener("click", closeEditTaskModal);
editTaskModal.addEventListener("click", (event) => {
    if (event.target === editTaskModal) closeEditTaskModal();
});
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !editTaskModal.hidden) closeEditTaskModal();
});

// Handle task deletion
async function handleDelete(taskId) {
    try {
        const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
            method: "DELETE",
            headers: authHeaders(),
        });
        if (handleAuthFailure(res)) return;
        if (!res.ok) throw new Error("Delete failed");
        await loadTasks(sortSelect.value);
    } catch (e) {
        console.error("Delete failed:", e);
    }
}

// =====================================================
// Quick Add functionality - parse natural language to create tasks
// =====================================================

// Handle quick add form submission
quickAddForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    quickAddError.textContent = "";

    const description = quickAddDesc.value.trim();
    if (!description) {
        quickAddError.textContent = "Description cannot be empty.";
        return;
    }

    const projectId = Number(quickAddProject.value);

    try {
        const res = await fetch(`${API_BASE}/tasks/quick-add`, {
            method: "POST",
            headers: authHeaders({ "Content-Type": "application/json" }),
            body: JSON.stringify({ description, project_id: projectId }),
        });
        if (handleAuthFailure(res)) return;

        if (!res.ok) {
            const err = await res.json();
            quickAddError.textContent = typeof err.detail === "string" ? err.detail : "Could not create task.";
            return;
        }

        // Display preview of created task
        const created = await res.json();
        previewTitle.textContent = created.title;
        previewPriority.textContent = created.priority;
        previewDue.textContent = created.due_date || "—";
        previewProject.textContent = getProjectName(created.project_id);

        quickAddForm.reset();  // Clear form
        await loadTasks(sortSelect.value);  // Refresh task list
        await refreshNotifications();  // Update notifications
    } catch (e) {
        console.error("Quick-add failed:", e);
        quickAddError.textContent = "Network error — check the backend is running.";
    }
});

// =====================================================
// Search + Sort view functionality
// =====================================================

// Handle search algorithm selection
algoButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
        algoButtons.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        searchAlgo = btn.dataset.algo;
    });
});

// Show notification banner with message
function showNotification(message, type) {
    notificationBanner.textContent = message;
    notificationBanner.className = `notification-banner ${type}`;
    notificationBanner.hidden = false;
}

// Execute search with selected algorithm
async function runSearch() {
    const title = searchTitleInput.value.trim();
    if (!title) {
        showNotification("Enter a title to search.", "error");
        return;
    }

    try {
        const res = await fetch(
            `${API_BASE}/tasks/search?title=${encodeURIComponent(title)}&algo=${searchAlgo}`,
            { headers: authHeaders() }
        );
        if (handleAuthFailure(res)) return;

        if (res.status === 404) {
            showNotification(`No task found with title "${title}".`, "error");
            renderTaskList(searchResults, []);
            return;
        }

        const task = await res.json();
        showNotification(`Found via ${searchAlgo} search.`, "success");
        renderTaskList(searchResults, [task]);
    } catch (e) {
        console.error("Search failed:", e);
        showNotification("Search failed — check the backend is running.", "error");
    }
}

// Event listeners for search
searchBtn.addEventListener("click", runSearch);

clearSearchBtn.addEventListener("click", () => {
    searchTitleInput.value = "";
    notificationBanner.hidden = true;
    searchResults.textContent = "";
});

// Apply sorting to task list
applySortBtn.addEventListener("click", async () => {
    notificationBanner.hidden = true;
    await loadTasks(sortSelect.value);
    renderTaskList(searchResults, allTasks);
    showNotification(
        sortSelect.value === "none" ? "Showing default order." : `Sorted by ${sortSelect.value} (insertion sort).`,
        "success"
    );
});

// =====================================================
// Stats view - display project statistics
// =====================================================

// Create statistic tile for dashboard
function createStatTile(label, value, accentClass) {
    const tile = document.createElement("div");
    tile.className = `kpi-tile ${accentClass}`;

    const labelEl = document.createElement("div");
    labelEl.className = "kpi-label";
    labelEl.textContent = label;

    const valueEl = document.createElement("div");
    valueEl.className = "kpi-value";
    valueEl.textContent = value;

    tile.appendChild(labelEl);
    tile.appendChild(valueEl);
    return tile;
}

// Load and display project statistics
async function loadStats() {
    const projectId = statsProjectSelect.value;
    statsContainer.textContent = "";

    if (!projectId) {
        const p = document.createElement("p");
        p.className = "hint-text";
        p.textContent = "No projects yet — add one to see stats.";
        statsContainer.appendChild(p);
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/projects/${projectId}/stats`, { headers: authHeaders() });
        if (handleAuthFailure(res)) return;
        const data = await res.json();

        statsContainer.appendChild(createStatTile("Total", data.total_tasks, "accent-teal"));
        statsContainer.appendChild(createStatTile("Pending", data.status_breakdown.pending, "accent-amber"));
        statsContainer.appendChild(createStatTile("In progress", data.status_breakdown.in_progress, "accent-blue"));
        statsContainer.appendChild(createStatTile("Completed", data.status_breakdown.completed, "accent-green"));
    } catch (e) {
        console.error("Failed to load stats:", e);
        const p = document.createElement("p");
        p.className = "hint-text";
        p.textContent = "Could not load stats.";
        statsContainer.appendChild(p);
    }
}

// Event listeners for stats view
statsProjectSelect.addEventListener("change", loadStats);
refreshStatsBtn.addEventListener("click", loadStats);

// =====================================================
// Projects view - display all projects
// =====================================================

// Render projects as clickable cards
function renderProjectsGrid() {
    projectsGrid.textContent = "";

    if (projects.length === 0) {
        const p = document.createElement("p");
        p.className = "hint-text";
        p.textContent = "No projects yet — add one from the Tasks view.";
        projectsGrid.appendChild(p);
        return;
    }

    projects.forEach((project) => {
        // Calculate project progress
        const projectTasks = allTasks.filter((t) => t.project_id === project.id);
        const total = projectTasks.length;
        const completed = projectTasks.filter((t) => t.status === "completed").length;
        const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

        const card = document.createElement("div");
        card.className = "project-card";
        // Clicking a project card filters tasks view by that project
        card.addEventListener("click", () => {
            setActiveView("tasks");
            projectFilterSelect.value = String(project.id);
            renderFilteredTaskList();
        });

        const nameEl = document.createElement("div");
        nameEl.className = "project-name";
        nameEl.textContent = project.name;

        const ownerEl = document.createElement("div");
        ownerEl.className = "project-owner";
        ownerEl.textContent = "Owner: you";

        const countEl = document.createElement("div");
        countEl.className = "project-count";
        countEl.textContent = `${total} task${total === 1 ? "" : "s"}`;

        const track = document.createElement("div");
        track.className = "progress-track";
        const fill = document.createElement("div");
        fill.className = "progress-fill";
        fill.style.width = `${pct}%`;
        track.appendChild(fill);

        const pctEl = document.createElement("div");
        pctEl.className = "progress-pct";
        pctEl.textContent = `${pct}% done`;

        card.appendChild(nameEl);
        card.appendChild(ownerEl);
        card.appendChild(countEl);
        card.appendChild(track);
        card.appendChild(pctEl);
        projectsGrid.appendChild(card);
    });
}

// =====================================================
// Create Project functionality
// =====================================================

// Handle project creation form submission
createProjectForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    projectError.textContent = "";

    const name = newProjectName.value.trim();
    if (!name) {
        projectError.textContent = "Project name cannot be empty.";
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/projects`, {
            method: "POST",
            headers: authHeaders({ "Content-Type": "application/json" }),
            body: JSON.stringify({ name }),
        });
        if (handleAuthFailure(res)) return;

        if (!res.ok) {
            projectError.textContent = "Could not create project.";
            return;
        }

        createProjectForm.reset();
        await fetchProjects();     // Refresh dropdowns everywhere
        renderProjectsGrid();      // Update projects view
        await loadStats();         // Update stats
        await refreshNotifications(); // Update notifications
    } catch (e) {
        console.error("Create project failed:", e);
        projectError.textContent = "Network error — check the backend is running.";
    }
});

// =====================================================
// Dashboard view - KPI cards and activity overview
// =====================================================

// Render dashboard with KPIs, project progress, and recent tasks
function renderDashboard() {
    // Calculate KPIs
    const total = allTasks.length;
    const pending = allTasks.filter((t) => t.status === "pending").length;
    const completed = allTasks.filter((t) => t.status === "completed").length;
    const doneRate = total > 0 ? Math.round((completed / total) * 100) : 0;

    // Update KPI cards
    kpiTotalTasks.textContent = total;
    kpiProjects.textContent = projects.length;
    kpiPending.textContent = pending;
    kpiDoneRate.textContent = `${doneRate}%`;

    // Render projects in motion section
    dashboardProjects.textContent = "";
    if (projects.length === 0) {
        const p = document.createElement("p");
        p.className = "hint-text";
        p.textContent = "No projects yet — create one to get started.";
        dashboardProjects.appendChild(p);
    } else {
        projects.slice(0, 5).forEach((project) => {
            const projectTasks = allTasks.filter((t) => t.project_id === project.id);
            const total_ = projectTasks.length;
            const completed_ = projectTasks.filter((t) => t.status === "completed").length;
            const pct = total_ > 0 ? Math.round((completed_ / total_) * 100) : 0;

            const row = document.createElement("div");
            row.className = "motion-row";

            const top = document.createElement("div");
            top.className = "motion-top";
            const name = document.createElement("span");
            name.textContent = project.name;
            const pctSpan = document.createElement("span");
            pctSpan.textContent = `${pct}% done`;
            top.appendChild(name);
            top.appendChild(pctSpan);

            const track = document.createElement("div");
            track.className = "progress-track";
            const fill = document.createElement("div");
            fill.className = "progress-fill";
            fill.style.width = `${pct}%`;
            track.appendChild(fill);

            row.appendChild(top);
            row.appendChild(track);
            dashboardProjects.appendChild(row);
        });
    }

    // Render recent tasks (most recently created)
    dashboardRecent.textContent = "";
    const recent = [...allTasks].sort((a, b) => b.id - a.id).slice(0, 5);
    if (recent.length === 0) {
        const p = document.createElement("p");
        p.className = "hint-text";
        p.textContent = "No tasks yet — add your first one.";
        dashboardRecent.appendChild(p);
    } else {
        recent.forEach((task) => {
            const row = document.createElement("div");
            row.className = "recent-row";

            const info = document.createElement("div");
            const titleEl = document.createElement("div");
            titleEl.className = "recent-title";
            titleEl.textContent = task.title;
            const subEl = document.createElement("div");
            subEl.className = "recent-sub";
            subEl.textContent = getProjectName(task.project_id);
            info.appendChild(titleEl);
            info.appendChild(subEl);

            const pill = document.createElement("span");
            pill.className = `pill pill-${task.priority}`;
            pill.textContent = task.priority;

            row.appendChild(info);
            row.appendChild(pill);
            dashboardRecent.appendChild(row);
        });
    }
}

// =====================================================
// Admin view - visible only to is_admin accounts
// =====================================================

// Load list of all users for admin view
async function loadAdminUsers() {
    teamList.textContent = "";

    try {
        const res = await fetch(`${API_BASE}/admin/users`, { headers: authHeaders() });
        if (handleAuthFailure(res)) return;

        if (res.status === 403) {
            const p = document.createElement("p");
            p.className = "hint-text";
            p.textContent = "Admin access required.";
            teamList.appendChild(p);
            return;
        }

        const adminUsers = await res.json();

        if (adminUsers.length === 0) {
            const p = document.createElement("p");
            p.className = "hint-text";
            p.textContent = "No registered users yet.";
            teamList.appendChild(p);
            return;
        }

        // Create user cards with click handler for details
        adminUsers.forEach((user) => {
            const card = document.createElement("div");
            card.className = "user-card";
            card.style.cursor = "pointer";
            card.addEventListener("click", () => loadAdminUserDetail(user.id, user.name));

            // Avatar with initials
            const avatar = document.createElement("div");
            avatar.className = "user-avatar";
            avatar.textContent = user.name
                .split(" ")
                .map((w) => w[0])
                .join("")
                .slice(0, 2)
                .toUpperCase();

            const info = document.createElement("div");
            const nameEl = document.createElement("div");
            nameEl.className = "user-name";
            nameEl.textContent = user.is_admin ? `${user.name} (admin)` : user.name;
            const emailEl = document.createElement("div");
            emailEl.className = "user-email";
            emailEl.textContent = user.email;
            const countsEl = document.createElement("div");
            countsEl.className = "user-email";
            countsEl.textContent = `${user.project_count} project${user.project_count === 1 ? "" : "s"} · ${user.task_count} task${user.task_count === 1 ? "" : "s"}`;

            info.appendChild(nameEl);
            info.appendChild(emailEl);
            info.appendChild(countsEl);

            card.appendChild(avatar);
            card.appendChild(info);
            teamList.appendChild(card);
        });
    } catch (e) {
        console.error("Failed to load admin users:", e);
        const p = document.createElement("p");
        p.className = "hint-text";
        p.textContent = "Could not load users.";
        teamList.appendChild(p);
    }
}

// Load detailed information about a specific user
async function loadAdminUserDetail(userId, userName) {
    try {
        const res = await fetch(`${API_BASE}/admin/users/${userId}/detail`, { headers: authHeaders() });
        if (handleAuthFailure(res)) return;

        if (res.status === 403) {
            alert("Admin access required.");
            return;
        }

        const data = await res.json();

        // Show detail card with user's projects and tasks
        adminDetailTitle.textContent = `${userName}'s projects & tasks`;
        adminDetailCard.hidden = false;
        adminDetailCard.scrollIntoView({ behavior: "smooth", block: "nearest" });

        // Render user's projects
        adminDetailProjects.textContent = "";
        if (data.projects.length === 0) {
            const p = document.createElement("p");
            p.className = "hint-text";
            p.textContent = "No projects.";
            adminDetailProjects.appendChild(p);
        } else {
            data.projects.forEach((proj) => {
                const card = document.createElement("div");
                card.className = "project-card";
                card.style.cursor = "default";
                const nameEl = document.createElement("div");
                nameEl.className = "project-name";
                nameEl.textContent = proj.name;
                card.appendChild(nameEl);
                adminDetailProjects.appendChild(card);
            });
        }

        // Render user's tasks using project name mapping
        const projectNameById = {};
        data.projects.forEach((p) => { projectNameById[p.id] = p.name; });

        adminDetailTasks.textContent = "";
        if (data.tasks.length === 0) {
            const p = document.createElement("p");
            p.textContent = "No tasks.";
            adminDetailTasks.appendChild(p);
        } else {
            data.tasks.forEach((task) => {
                const item = document.createElement("div");
                item.className = "task-item";

                const info = document.createElement("div");
                info.className = "task-info";

                const titleEl = document.createElement("div");
                titleEl.className = "task-title";
                titleEl.textContent = task.title;

                const metaEl = document.createElement("div");
                metaEl.className = "task-meta";
                const contextEl = document.createElement("span");
                contextEl.textContent = `${projectNameById[task.project_id] || "Project #" + task.project_id} · due ${task.due_date || "—"}`;
                const priorityPill = document.createElement("span");
                priorityPill.className = `pill pill-${task.priority}`;
                priorityPill.textContent = task.priority;
                const statusPill = createStatusPill(task.status);

                metaEl.appendChild(contextEl);
                metaEl.appendChild(priorityPill);
                metaEl.appendChild(statusPill);
                info.appendChild(titleEl);
                info.appendChild(metaEl);
                item.appendChild(info);
                adminDetailTasks.appendChild(item);
            });
        }
    } catch (e) {
        console.error("Failed to load user detail:", e);
    }
}

// Close admin detail card
adminDetailClose.addEventListener("click", () => {
    adminDetailCard.hidden = true;
});

// =====================================================
// Notifications system
// =====================================================

// Icon mapping for different notification types
const NOTIF_ICONS = {
    task: "ti-checklist",
    project: "ti-folder",
    quick_add: "ti-sparkles",
    registration: "ti-user-plus",
};

// Fetch notifications from backend
async function fetchNotifications() {
    try {
        const res = await fetch(`${API_BASE}/notifications`, { headers: authHeaders() });
        if (handleAuthFailure(res)) return [];
        return await res.json();
    } catch (e) {
        console.error("Failed to fetch notifications:", e);
        return [];
    }
}

// Render notifications in dropdown
function renderNotifications(notifications) {
    // Update unread count badge
    const unreadCount = notifications.filter((n) => !n.is_read).length;
    if (unreadCount > 0) {
        notifCountBadge.textContent = unreadCount > 9 ? "9+" : unreadCount;
        notifCountBadge.hidden = false;
    } else {
        notifCountBadge.hidden = true;
    }

    // Clear and populate notification list
    notifList.textContent = "";

    if (notifications.length === 0) {
        const p = document.createElement("p");
        p.className = "hint-text small";
        p.textContent = "No notifications yet.";
        notifList.appendChild(p);
        return;
    }

    notifications.forEach((n) => {
        const item = document.createElement("div");
        item.className = `notif-item${n.is_read ? "" : " unread"}`;

        const icon = document.createElement("div");
        icon.className = "notif-icon";
        const iconTag = document.createElement("i");
        iconTag.className = `ti ${NOTIF_ICONS[n.type] || "ti-bell"}`;
        icon.appendChild(iconTag);

        const body = document.createElement("div");
        body.className = "notif-item-body";
        const msg = document.createElement("div");
        msg.className = "notif-item-message";
        msg.textContent = n.message;
        body.appendChild(msg);

        item.appendChild(icon);
        item.appendChild(body);

        // Show unread dot
        if (!n.is_read) {
            const dot = document.createElement("div");
            dot.className = "notif-item-dot";
            item.appendChild(dot);
        }

        // Click to mark as read
        item.addEventListener("click", () => markNotificationRead(n.id));
        notifList.appendChild(item);
    });
}

// Refresh notifications
async function refreshNotifications() {
    const notifications = await fetchNotifications();
    renderNotifications(notifications);
}

// Mark individual notification as read
async function markNotificationRead(id) {
    try {
        const res = await fetch(`${API_BASE}/notifications/${id}/read`, {
            method: "PUT",
            headers: authHeaders(),
        });
        if (handleAuthFailure(res)) return;
        await refreshNotifications();
    } catch (e) {
        console.error("Failed to mark notification read:", e);
    }
}

// Mark all notifications as read
notifMarkAllBtn.addEventListener("click", async () => {
    try {
        const res = await fetch(`${API_BASE}/notifications/mark-all-read`, {
            method: "POST",
            headers: authHeaders(),
        });
        if (handleAuthFailure(res)) return;
        await refreshNotifications();
    } catch (e) {
        console.error("Failed to mark all notifications read:", e);
    }
});

// Toggle notification dropdown
notifBellBtn.addEventListener("click", async (event) => {
    event.stopPropagation();
    const isOpen = !notifDropdown.hidden;
    notifDropdown.hidden = isOpen;
    notifBellBtn.setAttribute("aria-expanded", String(!isOpen));
    if (!isOpen) await refreshNotifications();
});

// Close dropdown when clicking outside
document.addEventListener("click", (event) => {
    if (!notifDropdown.hidden && !event.target.closest(".notif-wrap")) {
        notifDropdown.hidden = true;
        notifBellBtn.setAttribute("aria-expanded", "false");
    }
});

// =====================================================
// Chat widget - AI-powered help assistant
// =====================================================

// Add message to chat interface
function addChatMessage(text, sender) {
    const row = document.createElement("div");
    row.className = `chat-message ${sender}`;

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";
    bubble.textContent = text;

    row.appendChild(bubble);
    chatMessages.appendChild(row);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return row;
}

// Open chat panel
chatFab.addEventListener("click", () => {
    chatPanel.hidden = false;
    chatFab.hidden = true;
    chatInput.focus();
});

// Close chat panel
chatCloseBtn.addEventListener("click", () => {
    chatPanel.hidden = true;
    chatFab.hidden = false;
});

// Handle chat form submission
chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = chatInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addChatMessage(message, "user");
    chatInput.value = "";
    chatSendBtn.disabled = true;

    // Add typing indicator
    const typingRow = addChatMessage("Thinking…", "bot typing");

    try {
        const res = await fetch(`${API_BASE}/chat`, {
            method: "POST",
            headers: authHeaders({ "Content-Type": "application/json" }),
            body: JSON.stringify({ message }),
        });
        if (handleAuthFailure(res)) return;

        typingRow.remove();

        if (!res.ok) {
            const err = await res.json();
            addChatMessage(
                typeof err.detail === "string" ? err.detail : "Something went wrong.",
                "bot"
            );
            return;
        }

        const data = await res.json();
        addChatMessage(data.reply, "bot");
    } catch (e) {
        console.error("Chat failed:", e);
        typingRow.remove();
        addChatMessage("Network error — check the backend is running.", "bot");
    } finally {
        chatSendBtn.disabled = false;
    }
});

// =====================================================
// Application Initialization
// =====================================================

// Main initialization function - called when DOM is ready
async function init() {
    // Set user name in top bar and show admin nav if applicable
    if (currentUser) {
        const displayName = currentUser.name || "TaskFlow User";
        sidebarUserName.textContent = displayName;
        sidebarUserEmail.textContent = currentUser.email || "";
        sidebarUserAvatar.textContent = displayName.slice(0, 2).toUpperCase();
        if (currentUser.is_admin) {
            navAdmin.hidden = false;
        }
    }

    topbar.classList.add("dashboard-view");

    // Load cached tasks for immediate display
    loadCacheAndRender();
    // Fetch fresh data from backend
    await fetchProjects();
    await loadTasks();
    await loadStats();
    renderDashboard();
    await refreshNotifications();
}

// Initialize application when DOM is fully loaded
document.addEventListener("DOMContentLoaded", init);
