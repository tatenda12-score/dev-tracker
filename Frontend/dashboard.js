let currentTaskId = null;
let currentJobId = null;

if (!sessionStorage.getItem("token") && localStorage.getItem("token")) {
    ["token", "user", "userId", "role", "email", "name"].forEach((key) => {
        const value = localStorage.getItem(key);
        if (value !== null) {
            sessionStorage.setItem(key, value);
        }
    });
    localStorage.clear();
}

if (!sessionStorage.getItem("token")) {
    window.location.href = "login.html";
}

document.addEventListener("DOMContentLoaded", () => {
    const user = JSON.parse(sessionStorage.getItem("user"));

    if (user?.name) {
        const title = document.getElementById("dashboardTitle");
        if (title) {
            title.innerText = "Welcome, " + user.name;
        }
    }

    loadDashboard();
    setInterval(loadNotifications, 10000);
    document.getElementById("inProgressCard")?.addEventListener("click", () => {
        focusRowsByStatus();
    });
});


async function loadDashboard() {
    await Promise.all([
        loadKPIs(),
        loadTasks(),
        loadJobs(),
        loadCharts(),
        loadPerformance(),
        loadNotifications()
    ]);
}


async function loadKPIs() {
    const [taskRes, jobRes] = await Promise.all([
        apiRequest("/tasks/my-tasks"),
        apiRequest("/job-cards/")
    ]);
    const tasks = taskRes?.data || [];
    const jobs = jobRes?.data || [];

    const total = tasks.length;
    const completed = tasks.filter(task => task.status === "Completed").length +
        jobs.filter(job => job.status === "Closed").length;
    const inProgress = tasks.filter(task => task.status === "In Progress").length +
        jobs.filter(job => job.status === "Open").length;
    const totalSeconds = tasks.reduce((sum, task) => sum + (task.time_taken || 0), 0) +
        jobs.reduce((sum, job) => sum + (job.duration || 0), 0);

    document.getElementById("assignedTasks").innerText = total;
    document.getElementById("completedTasks").innerText = completed;
    document.getElementById("inProgressTasks").innerText = inProgress;
    document.getElementById("hoursWorked").innerText = (totalSeconds / 3600).toFixed(2) + "h";
}


async function loadNotifications() {
    const res = await apiRequest("/tasks/notifications");
    const notifications = res?.data || [];
    const unreadNotifications = notifications.filter(notification => !notification.is_read);
    const unreadCount = res?.meta?.unread_count || 0;
    const panel = document.getElementById("notificationsPanel");

    document.getElementById("notificationCount").innerText = unreadCount;

    panel.innerHTML = "";

    if (!unreadNotifications.length) {
        panel.appendChild(createEmptyState("notification-item", "No notifications yet.", "Everything is quiet for now."));
        return;
    }

    const visibleNotifications = unreadNotifications.slice(0, 6);

    visibleNotifications.forEach(notification => {
        const item = document.createElement("div");
        item.className = `notification-item ${notification.is_read ? "" : "unread"}`.trim();
        const message = document.createElement("div");
        message.className = "notification-message";
        message.textContent = notification.message;
        const timestamp = document.createElement("small");
        timestamp.textContent = formatDate(notification.created_at);
        item.append(message, timestamp);
        item.addEventListener("click", () => handleNotificationClick(notification));
        panel.appendChild(item);
    });
}


async function markNotificationsRead() {
    await apiRequest("/tasks/notifications/read", "PUT");
    loadNotifications();
}


async function handleNotificationClick(notification) {
    await apiRequest(`/tasks/notifications/${notification.id}/read`, "PUT");
    await loadNotifications();

    const target = extractNotificationTarget(notification.message);
    if (!target) return;

    if (target.type === "task") {
        scrollToSection("tasks");
        await focusRowByTitle("#tasksTable", "task", target.title);
    } else {
        scrollToSection("jobs");
        await focusRowByTitle("#jobsTable", "job", target.title);
    }
}


async function loadTasks() {
    const res = await apiRequest("/tasks/my-tasks");
    const tasks = res?.data || [];
    const table = document.getElementById("tasksTable");

    table.innerHTML = "";

    tasks.forEach(task => {
        const row = document.createElement("tr");
        row.className = "clickable-row";
        row.id = `task-row-${task.id}`;
        row.dataset.title = (task.title || "").trim().toLowerCase();
        row.dataset.status = getNormalizedStatus(task.status);
        row.append(
            createCell(task.title),
            createStatusCell(task.status),
            createActionCell("View", "btn btn-view", () => viewTask(task.id))
        );
        row.addEventListener("click", () => viewTask(task.id));
        table.appendChild(row);
    });
}


async function loadJobs() {
    const res = await apiRequest("/job-cards/");
    const jobs = res?.data || [];
    const table = document.getElementById("jobsTable");

    table.innerHTML = "";

    jobs.forEach(job => {
        const row = document.createElement("tr");
        row.className = "clickable-row";
        row.id = `job-row-${job.id}`;
        row.dataset.title = (job.title || "").trim().toLowerCase();
        row.dataset.status = getNormalizedStatus(job.status);
        row.append(
            createCell(`#${job.id}`),
            createCell(job.title),
            createStatusCell(job.status),
            createActionCell("View", "btn btn-view", () => viewJob(job.id))
        );
        row.addEventListener("click", () => viewJob(job.id));
        table.appendChild(row);
    });
}


async function loadCharts() {
    const res = await apiRequest("/analytics/my-charts");
    const chartData = res?.data || {};
    const pie = chartData.pie || {};
    const bar = chartData.bar || {};

    if (window.pieChartInstance) window.pieChartInstance.destroy();
    if (window.barChartInstance) window.barChartInstance.destroy();

    window.pieChartInstance = new Chart(document.getElementById("pieChart"), {
        type: "pie",
        data: {
            labels: pie.labels || ["Completed", "In Progress", "Pending"],
            datasets: [{
                data: pie.data || [0, 0, 0]
            }]
        }
    });

    window.barChartInstance = new Chart(document.getElementById("barChart"), {
        type: "bar",
        data: {
            labels: bar.labels || [],
            datasets: [{
                label: "Completed Work Items",
                data: bar.items || [],
                backgroundColor: "rgba(59, 130, 246, 0.45)",
                borderColor: "#2563eb",
                borderWidth: 1,
                borderRadius: 8
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0 }
                }
            }
        }
    });
}


async function loadPerformance() {
    const res = await apiRequest("/analytics/my-charts");
    const line = res?.data?.line || {};

    if (window.performanceChartInstance) window.performanceChartInstance.destroy();

    window.performanceChartInstance = new Chart(document.getElementById("performanceChart"), {
        type: "line",
        data: {
            labels: line.labels || [],
            datasets: [{
                label: "Hours Worked",
                data: line.hours || [],
                borderColor: "#0ea5e9",
                backgroundColor: "rgba(14, 165, 233, 0.16)",
                fill: true,
                tension: 0.35,
                pointRadius: 4
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}


function getStatusBadge(status) {
    const badge = document.createElement("span");
    badge.textContent = status;
    if (status === "Pending") badge.className = "badge pending";
    else if (status === "In Progress" || status === "Open") badge.className = "badge progress";
    else if (status === "Completed" || status === "Closed") badge.className = "badge completed";
    return badge;
}


function getNormalizedStatus(status) {
    if (status === "Open") return "In Progress";
    if (status === "Closed") return "Completed";
    return status;
}


async function startTask(id) {
    await apiRequest(`/tasks/start/${id}`, "PUT");
    await loadDashboard();
    await viewTask(id);
}


async function completeTask(id) {
    await apiRequest(`/tasks/complete/${id}`, "PUT");
    await loadDashboard();
    await viewTask(id);
}


async function addTaskUpdate() {
    if (!currentTaskId) return;

    const message = document.getElementById("taskUpdateInput").value.trim();
    if (!message) {
        alert("Write a task comment first");
        return;
    }

    await apiRequest(`/tasks/update/${currentTaskId}`, "POST", { message });
    document.getElementById("taskUpdateInput").value = "";
    await loadNotifications();
    await viewTask(currentTaskId);
}


async function viewTask(taskId) {
    const res = await apiRequest(`/tasks/${taskId}`);
    const task = res?.data?.task;
    const updates = res?.data?.updates || [];
    if (!task) return;

    currentTaskId = task.id;

    document.getElementById("modalTitle").innerText = task.title;
    document.getElementById("modalDescription").innerText = task.description || "No description provided";
    document.getElementById("modalStatus").innerText = task.status;
    document.getElementById("modalGithub").innerText = task.github_link || "N/A";
    document.getElementById("modalGithub").href = task.github_link || "#";
    document.getElementById("modalStart").innerText = formatDate(task.start_time);
    document.getElementById("modalEnd").innerText = formatDate(task.end_time);
    document.getElementById("modalTime").innerText = formatTime(task.time_taken);
    document.getElementById("modalAssignedBy").innerText = task.assigned_by_name || "Admin";

    const actions = document.getElementById("modalActions");
    renderTaskActions(actions, task);

    renderUpdates("taskUpdatesList", updates);
    document.getElementById("taskModal").style.display = "block";
}


function closeModal() {
    document.getElementById("taskModal").style.display = "none";
}


async function startJob(id) {
    await apiRequest(`/job-cards/open/${id}`, "PUT");
    await loadDashboard();
    await viewJob(id);
}


async function closeJob(id) {
    await apiRequest(`/job-cards/close/${id}`, "PUT");
    await loadDashboard();
    await viewJob(id);
}


async function addJobUpdate() {
    if (!currentJobId) return;

    const message = document.getElementById("jobUpdateInput").value.trim();
    if (!message) {
        alert("Write an update first");
        return;
    }

    await apiRequest(`/job-cards/update/${currentJobId}`, "POST", { message });
    document.getElementById("jobUpdateInput").value = "";
    await loadNotifications();
    await viewJob(currentJobId);
}


async function viewJob(jobId) {
    const res = await apiRequest(`/job-cards/${jobId}`);
    const job = res?.data?.job;
    const updates = res?.data?.updates || [];
    if (!job) return;

    currentJobId = job.id;

    document.getElementById("jobTitle").innerText = job.title;
    document.getElementById("jobDescription").innerText = job.description || "No description provided";
    document.getElementById("jobStatus").innerText = job.status;
    document.getElementById("jobGithub").innerText = job.github_link || "N/A";
    document.getElementById("jobGithub").href = job.github_link || "#";
    document.getElementById("jobCreated").innerText = formatDate(job.created_at);
    document.getElementById("jobOpened").innerText = formatDate(job.opened_at);
    document.getElementById("jobClosed").innerText = formatDate(job.closed_at);
    document.getElementById("jobAssignedBy").innerText = job.assigned_by_name || "Admin";

    const actions = document.getElementById("jobActions");
    renderJobActions(actions, job);

    renderUpdates("jobUpdatesList", updates);
    document.getElementById("jobModal").style.display = "block";
}


function closeJobModal() {
    document.getElementById("jobModal").style.display = "none";
}


function renderUpdates(elementId, updates) {
    const container = document.getElementById(elementId);
    container.innerHTML = "";

    if (!updates.length) {
        container.appendChild(createEmptyState("update-item", "No updates yet."));
        return;
    }

    updates.forEach(update => {
        container.appendChild(createUpdateItem(update, "User"));
    });
}


function extractNotificationTarget(message) {
    const taskMatch = message.match(/task(?:\s+\w+)*:\s*(.+)$/i);
    if (taskMatch) {
        return { type: "task", title: taskMatch[1].trim().toLowerCase() };
    }

    const jobMatch = message.match(/job(?:\s+\w+)*:\s*(.+)$/i);
    if (jobMatch) {
        return { type: "job", title: jobMatch[1].trim().toLowerCase() };
    }

    return null;
}


async function focusRowByTitle(tableSelector, type, title) {
    const table = document.querySelector(tableSelector);
    if (!table) return;

    const rows = Array.from(table.querySelectorAll("tr"));
    const targetRow = rows.find(row => row.dataset.title === title);
    if (!targetRow) return;

    rows.forEach(row => row.classList.remove("focus-row"));
    targetRow.classList.add("focus-row");
    targetRow.scrollIntoView({ behavior: "smooth", block: "center" });

    if (type === "task") {
        await viewTask(targetRow.id.replace("task-row-", ""));
    } else {
        await viewJob(targetRow.id.replace("job-row-", ""));
    }

    setTimeout(() => targetRow.classList.remove("focus-row"), 4000);
}


function clearFocusedRows() {
    document.querySelectorAll(".focus-row").forEach(row => row.classList.remove("focus-row"));
}


async function focusRowsByStatus() {
    await Promise.all([loadTasks(), loadJobs()]);
    clearFocusedRows();

    scrollToSection("tasks");

    const taskRows = Array.from(document.querySelectorAll("#tasksTable tr"))
        .filter(row => row.dataset.status === "In Progress");
    const jobRows = Array.from(document.querySelectorAll("#jobsTable tr"))
        .filter(row => row.dataset.status === "In Progress");

    [...taskRows, ...jobRows].forEach(row => row.classList.add("focus-row"));

    const firstTarget = taskRows[0] || jobRows[0];
    if (firstTarget) {
        firstTarget.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    setTimeout(clearFocusedRows, 4000);
}


function formatTime(seconds) {
    if (!seconds) return "0 min";
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return hrs > 0 ? `${hrs}h ${mins}m` : `${mins} min`;
}


function formatDate(value) {
    return value ? new Date(value).toLocaleString() : "N/A";
}


function scrollToSection(section) {
    const target = document.getElementById(section) || document.querySelector(`.${section}`);
    if (target) target.scrollIntoView({ behavior: "smooth" });
}


function logout() {
    sessionStorage.clear();
    localStorage.clear();
    window.location.href = "login.html";
}

function createCell(value) {
    const cell = document.createElement("td");
    cell.textContent = value ?? "N/A";
    return cell;
}

function createStatusCell(status) {
    const cell = document.createElement("td");
    cell.appendChild(getStatusBadge(status));
    return cell;
}

function createActionCell(label, className, handler) {
    const cell = document.createElement("td");
    const button = document.createElement("button");
    button.className = className;
    button.textContent = label;
    button.addEventListener("click", (event) => {
        event.stopPropagation();
        handler();
    });
    cell.appendChild(button);
    return cell;
}

function createEmptyState(className, title, subtitle = "") {
    const wrapper = document.createElement("div");
    wrapper.className = className;
    wrapper.textContent = title;
    if (subtitle) {
        const small = document.createElement("small");
        small.textContent = subtitle;
        wrapper.appendChild(small);
    }
    return wrapper;
}

function createUpdateItem(update, fallbackAuthor) {
    const item = document.createElement("div");
    item.className = "update-item";
    const author = document.createElement("strong");
    author.textContent = `${update.author_name || fallbackAuthor} · ${update.author_role || "USER"}`;
    const message = document.createElement("div");
    message.textContent = update.message || "";
    const time = document.createElement("small");
    time.textContent = formatDate(update.created_at);
    item.append(author, message, time);
    return item;
}

function renderTaskActions(container, task) {
    container.innerHTML = "";
    if (task.status === "Pending") {
        const button = document.createElement("button");
        button.className = "btn btn-start";
        button.textContent = "Start Task";
        button.addEventListener("click", () => startTask(task.id));
        container.appendChild(button);
        return;
    }
    if (task.status === "In Progress") {
        const button = document.createElement("button");
        button.className = "btn btn-update";
        button.textContent = "Complete Task";
        button.addEventListener("click", () => completeTask(task.id));
        container.appendChild(button);
        return;
    }
    container.appendChild(getStatusBadge("Completed"));
}

function renderJobActions(container, job) {
    container.innerHTML = "";
    if (job.status === "Pending") {
        const button = document.createElement("button");
        button.className = "btn btn-start";
        button.textContent = "Start Job";
        button.addEventListener("click", () => startJob(job.id));
        container.appendChild(button);
        return;
    }
    if (job.status === "Open") {
        const button = document.createElement("button");
        button.className = "btn btn-update";
        button.textContent = "Close Job";
        button.addEventListener("click", () => closeJob(job.id));
        container.appendChild(button);
        return;
    }
    container.appendChild(getStatusBadge("Closed"));
}
