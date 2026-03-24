const token = localStorage.getItem("token");
let currentTaskId = null;
let currentJobId = null;

if (!token) {
    window.location.href = "login.html";
}

document.addEventListener("DOMContentLoaded", () => {
    const user = JSON.parse(localStorage.getItem("user"));

    if (user?.name) {
        const title = document.getElementById("dashboardTitle");
        if (title) {
            title.innerText = "Welcome, " + user.name;
        }
    }

    loadDashboard();
    setInterval(loadNotifications, 10000);
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
    const res = await apiRequest("/tasks/my-tasks");
    const tasks = res?.data || [];

    const total = tasks.length;
    const completed = tasks.filter(task => task.status === "Completed").length;
    const inProgress = tasks.filter(task => task.status === "In Progress").length;
    const totalSeconds = tasks.reduce((sum, task) => sum + (task.time_taken || 0), 0);

    document.getElementById("assignedTasks").innerText = total;
    document.getElementById("completedTasks").innerText = completed;
    document.getElementById("inProgressTasks").innerText = inProgress;
    document.getElementById("hoursWorked").innerText = (totalSeconds / 3600).toFixed(2) + "h";
}


async function loadNotifications() {
    const res = await apiRequest("/tasks/notifications");
    const notifications = res?.data || [];
    const unreadCount = res?.meta?.unread_count || 0;
    const panel = document.getElementById("notificationsPanel");

    document.getElementById("notificationCount").innerText = unreadCount;

    panel.innerHTML = "";

    if (!notifications.length) {
        panel.innerHTML = `<div class="notification-item">No notifications yet.<small>Everything is quiet for now.</small></div>`;
        return;
    }

    notifications.slice(0, 6).forEach(notification => {
        panel.innerHTML += `
            <div class="notification-item">
                <div>${notification.message}</div>
                <small>${formatDate(notification.created_at)}</small>
            </div>
        `;
    });
}


async function markNotificationsRead() {
    await apiRequest("/tasks/notifications/read", "PUT");
    loadNotifications();
}


async function loadTasks() {
    const res = await apiRequest("/tasks/my-tasks");
    const tasks = res?.data || [];
    const table = document.getElementById("tasksTable");

    table.innerHTML = "";

    tasks.forEach(task => {
        const row = document.createElement("tr");
        row.className = "clickable-row";
        row.innerHTML = `
            <td>${task.title}</td>
            <td>${getStatusBadge(task.status)}</td>
            <td><button class="btn btn-view" onclick="event.stopPropagation(); viewTask(${task.id})">View</button></td>
        `;
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
        row.innerHTML = `
            <td>#${job.id}</td>
            <td>${job.title}</td>
            <td>${getStatusBadge(job.status)}</td>
            <td><button class="btn btn-view" onclick="event.stopPropagation(); viewJob(${job.id})">View</button></td>
        `;
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
                label: "Tasks Completed",
                data: bar.tasks || [],
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
    if (status === "Pending") return `<span class="badge pending">Pending</span>`;
    if (status === "In Progress") return `<span class="badge progress">In Progress</span>`;
    if (status === "Completed") return `<span class="badge completed">Completed</span>`;
    if (status === "Open") return `<span class="badge progress">Open</span>`;
    if (status === "Closed") return `<span class="badge completed">Closed</span>`;
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
    if (task.status === "Pending") {
        actions.innerHTML = `<button class="btn btn-start" onclick="startTask(${task.id})">Start Task</button>`;
    } else if (task.status === "In Progress") {
        actions.innerHTML = `<button class="btn btn-update" onclick="completeTask(${task.id})">Complete Task</button>`;
    } else {
        actions.innerHTML = `<span class="badge completed">Completed</span>`;
    }

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
    if (job.status === "Pending") {
        actions.innerHTML = `<button class="btn btn-start" onclick="startJob(${job.id})">Start Job</button>`;
    } else if (job.status === "Open") {
        actions.innerHTML = `<button class="btn btn-update" onclick="closeJob(${job.id})">Close Job</button>`;
    } else {
        actions.innerHTML = `<span class="badge completed">Closed</span>`;
    }

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
        container.innerHTML = `<div class="update-item">No updates yet.</div>`;
        return;
    }

    updates.forEach(update => {
        container.innerHTML += `
            <div class="update-item">
                <strong>${update.author_name || "User"} · ${update.author_role || "USER"}</strong>
                <div>${update.message}</div>
                <small>${formatDate(update.created_at)}</small>
            </div>
        `;
    });
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
    localStorage.clear();
    window.location.href = "login.html";
}
