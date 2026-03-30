const API = "";

let barChart = null;
let pieChart = null;
let companyLineChart = null;
let currentAdminTaskId = null;
let currentAdminJobId = null;

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


async function apiRequest(endpoint, method = "GET", data = null) {
    try {
        const res = await fetch(API + endpoint, {
            method,
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${sessionStorage.getItem("token") || ""}`
            },
            body: data ? JSON.stringify(data) : null
        });

        if (res.status === 401) {
            alert("Session expired. Login again.");
            logout();
            return null;
        }

        const result = await res.json();

        if (!res.ok) {
            alert(result.detail || result.message || "Something went wrong");
            return null;
        }

        return result;
    } catch (err) {
        console.error("API Error:", err);
        alert("Network error");
        return null;
    }
}


async function getCurrentUser() {
    const res = await apiRequest("/auth/me");
    document.getElementById("adminName").innerText =
        "Logged in as: " + (res?.data?.name || "Admin");
}


async function loadAdminKPIs() {
    const tasksRes = await apiRequest("/tasks/");
    const jobsRes = await apiRequest("/job-cards/");
    const chartsRes = await apiRequest("/analytics/charts");

    const tasks = tasksRes?.data || [];
    const jobs = jobsRes?.data || [];
    const pieData = chartsRes?.pie?.data || [];

    document.getElementById("totalJobs").innerText = jobs.length;

    const completed = pieData[0] ?? (
        tasks.filter(task => task.status === "Completed").length +
        jobs.filter(job => job.status === "Closed").length
    );
    const progress = pieData[1] ?? (
        tasks.filter(task => task.status === "In Progress").length +
        jobs.filter(job => job.status === "Open").length
    );
    const pending = pieData[2] ?? (
        tasks.filter(task => task.status === "Pending").length +
        jobs.filter(job => job.status === "Pending").length
    );

    document.getElementById("activeTasks").innerText = progress;
    document.getElementById("completedTasks").innerText = completed;
    document.getElementById("overdueTasks").innerText = pending;
    document.getElementById("taskBadgeCount").innerText =
        tasks.filter(task => task.status === "In Progress").length;
    document.getElementById("jobBadgeCount").innerText =
        jobs.filter(job => job.status === "Open").length;
    document.getElementById("taskPendingBadgeCount").innerText =
        tasks.filter(task => task.status === "Pending").length;
    document.getElementById("jobPendingBadgeCount").innerText =
        jobs.filter(job => job.status === "Pending").length;

    updateCharts(chartsRes, completed, progress, pending);
}


async function loadAdminNotifications() {
    const response = await apiRequest("/tasks/notifications");
    const notifications = response?.data || [];
    const unreadNotifications = notifications.filter(notification => !notification.is_read);
    const unreadCount = response?.meta?.unread_count || 0;
    const panel = document.getElementById("notificationsPanel");

    document.getElementById("adminNotificationCount").innerText = unreadCount;
    panel.innerHTML = "";

    if (!unreadNotifications.length) {
        panel.appendChild(createEmptyState("notification-item", "No admin notifications yet.", "Updates will appear here."));
        return;
    }

    unreadNotifications.slice(0, 8).forEach(notification => {
        const item = document.createElement("div");
        item.className = `notification-item ${notification.is_read ? "" : "unread"}`.trim();
        const message = document.createElement("div");
        message.className = "notification-message";
        message.textContent = notification.message;
        const timestamp = document.createElement("small");
        timestamp.textContent = formatDate(notification.created_at);
        item.append(message, timestamp);
        item.addEventListener("click", () => handleAdminNotificationClick(notification));
        panel.appendChild(item);
    });
}


async function markAdminNotificationsRead() {
    await apiRequest("/tasks/notifications/read", "PUT");
    loadAdminNotifications();
}


async function handleAdminNotificationClick(notification) {
    await apiRequest(`/tasks/notifications/${notification.id}/read`, "PUT");
    await loadAdminNotifications();

    const target = extractNotificationTarget(notification.message);
    if (!target) return;

    if (target.type === "task") {
        scrollToSection("tasks");
        await focusRowByTitle("#adminTasksTable", "task", target.title);
    } else {
        scrollToSection("jobs");
        await focusRowByTitle("#jobsTable", "job", target.title);
    }
}


function openAssignModal() {
    document.getElementById("assignModal").style.display = "block";
    loadUsersForDropdown();
}


function closeAssignModal() {
    document.getElementById("assignModal").style.display = "none";
}


async function loadUsersForDropdown() {
    const res = await apiRequest("/users/");
    const users = res?.data || [];
    const select = document.getElementById("taskUser");
    select.innerHTML = "";

    users.forEach(user => {
        if (user.role !== "ADMIN") {
            select.appendChild(createOption(user.id, user.name));
        }
    });
}


async function submitTask() {
    const title = taskTitle.value;
    const description = taskDescription.value;
    const owner_id = taskUser.value;

    const result = await apiRequest("/tasks/assign-task", "POST", {
        title,
        description,
        owner_id: parseInt(owner_id)
    });

    if (!result) return;

    alert(result.message || "Task assigned successfully");
    closeAssignModal();
    refreshAll();
}


function openCreateJobModal() {
    document.getElementById("createJobModal").style.display = "block";
    loadUsersForJobDropdown();
}


function closeCreateJobModal() {
    document.getElementById("createJobModal").style.display = "none";
}


function getAdminRowClass(status) {
    if (status === "In Progress" || status === "Open") return "status-active";
    if (status === "Pending") return "status-pending";
    if (status === "Completed" || status === "Closed") return "status-completed";
    return "";
}


async function loadUsersForJobDropdown() {
    const res = await apiRequest("/users/");
    const users = res?.data || [];
    const select = document.getElementById("jobUser");
    select.innerHTML = "";

    users.forEach(user => {
        if (user.role !== "ADMIN") {
            select.appendChild(createOption(user.id, user.name));
        }
    });
}


async function submitJob() {
    const title = jobService.value;
    const description = jobDescription.value;
    const owner_id = jobUser.value;

    const result = await apiRequest("/job-cards/", "POST", {
        title,
        description,
        owner_id: parseInt(owner_id)
    });

    if (!result) return;

    alert(result.message || "Job created successfully");
    closeCreateJobModal();
    refreshAll();
}


async function loadAllTasks() {
    const res = await apiRequest("/tasks/");
    const tasks = res?.data || [];
    const tbody = document.querySelector("#adminTasksTable tbody");
    tbody.innerHTML = "";

    tasks.sort((a, b) => {
        const statusOrder = {
            "In Progress": 0,
            "Pending": 1,
            "Overdue": 2,
            "Completed": 3
        };
        const aRank = statusOrder[a.status] ?? 99;
        const bRank = statusOrder[b.status] ?? 99;

        if (aRank !== bRank) return aRank - bRank;
        return new Date(b.created_at) - new Date(a.created_at);
    });

    tasks.forEach(task => {
        const row = document.createElement("tr");
        row.className = `clickable-row ${getAdminRowClass(task.status)}`.trim();
        row.id = `admin-task-row-${task.id}`;
        row.dataset.title = (task.title || "").trim().toLowerCase();
        row.dataset.status = task.status;
        row.append(
            createCell(task.id),
            createCell(task.owner_name || "N/A"),
            createCell(task.title),
            createCell(task.description || "N/A"),
            createCell(task.status),
            createCell(task.github_link || "-"),
            createCell(formatDate(task.created_at)),
            createCell(formatDuration(task.time_taken))
        );
        row.addEventListener("click", () => viewAdminTask(task.id));
        tbody.appendChild(row);
    });
}


async function loadAllJobs() {
    const res = await apiRequest("/job-cards/");
    const jobs = res?.data || [];
    const tbody = document.querySelector("#jobsTable tbody");
    tbody.innerHTML = "";

    jobs.sort((a, b) => {
        const statusOrder = {
            "Open": 0,
            "Pending": 1,
            "Overdue": 2,
            "Closed": 3
        };
        const aRank = statusOrder[a.status] ?? 99;
        const bRank = statusOrder[b.status] ?? 99;

        if (aRank !== bRank) return aRank - bRank;
        return new Date(b.created_at) - new Date(a.created_at);
    });

    jobs.forEach(job => {
        const row = document.createElement("tr");
        row.className = `clickable-row ${getAdminRowClass(job.status)}`.trim();
        row.id = `admin-job-row-${job.id}`;
        row.dataset.title = (job.title || "").trim().toLowerCase();
        row.dataset.status = job.status;
        row.append(
            createCell(job.id),
            createCell(job.title),
            createCell(job.status),
            createCell(formatDate(job.created_at)),
            createCell(formatDuration(job.duration))
        );
        row.addEventListener("click", () => viewAdminJob(job.id));
        tbody.appendChild(row);
    });
}


async function viewAdminTask(taskId) {
    const res = await apiRequest(`/tasks/${taskId}`);
    const task = res?.data?.task;
    const updates = res?.data?.updates || [];
    if (!task) return;

    currentAdminTaskId = task.id;

    document.getElementById("adminTaskTitle").innerText = task.title;
    document.getElementById("adminTaskDescription").innerText = task.description || "No description provided";
    document.getElementById("adminTaskOwner").innerText = task.owner_name || "Unknown";
    document.getElementById("adminTaskAssignedBy").innerText = task.assigned_by_name || "Unknown";
    document.getElementById("adminTaskStatus").innerText = task.status;
    document.getElementById("adminTaskGithub").innerText = task.github_link || "N/A";
    document.getElementById("adminTaskGithub").href = task.github_link || "#";
    document.getElementById("adminTaskCreated").innerText = formatDate(task.created_at);
    document.getElementById("adminTaskDuration").innerText = formatDuration(task.time_taken);
    document.getElementById("adminTaskStart").innerText = formatDate(task.start_time);
    document.getElementById("adminTaskEnd").innerText = formatDate(task.end_time);

    renderUpdates("adminTaskUpdates", updates);
    document.getElementById("adminTaskModal").style.display = "block";
}


async function addAdminTaskReply() {
    if (!currentAdminTaskId) return;

    const textarea = document.getElementById("adminTaskReply");
    const message = textarea.value.trim();
    if (!message) {
        alert("Write a comment first");
        return;
    }

    await apiRequest(`/tasks/update/${currentAdminTaskId}`, "POST", { message });
    textarea.value = "";
    await loadAdminNotifications();
    await viewAdminTask(currentAdminTaskId);
}


function closeAdminTaskModal() {
    document.getElementById("adminTaskModal").style.display = "none";
}


async function viewAdminJob(jobId) {
    const res = await apiRequest(`/job-cards/${jobId}`);
    const job = res?.data?.job;
    const updates = res?.data?.updates || [];
    if (!job) return;

    currentAdminJobId = job.id;

    document.getElementById("adminJobTitle").innerText = job.title;
    document.getElementById("adminJobDescription").innerText = job.description || "No description provided";
    document.getElementById("adminJobOwner").innerText = job.owner_name || "Unknown";
    document.getElementById("adminJobAssignedBy").innerText = job.assigned_by_name || "Unknown";
    document.getElementById("adminJobStatus").innerText = job.status;
    document.getElementById("adminJobGithub").innerText = job.github_link || "N/A";
    document.getElementById("adminJobGithub").href = job.github_link || "#";
    document.getElementById("adminJobCreated").innerText = formatDate(job.created_at);
    document.getElementById("adminJobOpened").innerText = formatDate(job.opened_at);
    document.getElementById("adminJobClosed").innerText = formatDate(job.closed_at);
    document.getElementById("adminJobDuration").innerText = formatDuration(job.duration);

    renderUpdates("adminJobUpdates", updates);
    document.getElementById("adminJobModal").style.display = "block";
}


async function addAdminJobReply() {
    if (!currentAdminJobId) return;

    const textarea = document.getElementById("adminJobReply");
    const message = textarea.value.trim();
    if (!message) {
        alert("Write an update first");
        return;
    }

    await apiRequest(`/job-cards/update/${currentAdminJobId}`, "POST", { message });
    textarea.value = "";
    await loadAdminNotifications();
    await viewAdminJob(currentAdminJobId);
}


function closeAdminJobModal() {
    document.getElementById("adminJobModal").style.display = "none";
}


function renderUpdates(elementId, updates) {
    const container = document.getElementById(elementId);
    container.innerHTML = "";

    if (!updates.length) {
        container.appendChild(createEmptyState("update-item", "No updates yet."));
        return;
    }

    updates.forEach(update => {
        container.appendChild(createUpdateItem(update));
    });
}


function extractNotificationTarget(message) {
    const taskMatch = message.match(/task:\s*(.+)$/i);
    if (taskMatch) {
        return { type: "task", title: taskMatch[1].trim().toLowerCase() };
    }

    const jobMatch = message.match(/job:\s*(.+)$/i);
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
        await viewAdminTask(targetRow.id.replace("admin-task-row-", ""));
    } else {
        await viewAdminJob(targetRow.id.replace("admin-job-row-", ""));
    }

    setTimeout(() => targetRow.classList.remove("focus-row"), 4000);
}


function formatDate(date) {
    return date ? new Date(date).toLocaleString() : "N/A";
}


function formatDuration(seconds) {
    if (!seconds) return "0 min";
    const mins = Math.floor(seconds / 60);
    const hrs = Math.floor(mins / 60);
    return hrs > 0 ? `${hrs}h ${mins % 60}m` : `${mins} min`;
}


function initCharts() {
    const barCanvas = document.getElementById("barChart");
    const pieCanvas = document.getElementById("pieChart");
    const lineCanvas = document.getElementById("companyLineChart");
    if (!barCanvas || !pieCanvas || !lineCanvas) return;

    barChart = new Chart(barCanvas, {
        type: "bar",
        data: {
            labels: ["Completed", "In Progress", "Pending"],
            datasets: [{
                label: "Tasks",
                data: [0, 0, 0],
                backgroundColor: ["#22c55e", "#f59e0b", "#ef4444"],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });

    pieChart = new Chart(pieCanvas, {
        type: "doughnut",
        data: {
            labels: ["Completed", "In Progress", "Pending"],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: ["#22c55e", "#f59e0b", "#ef4444"]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            cutout: "65%",
            plugins: { legend: { position: "bottom" } }
        }
    });

    companyLineChart = new Chart(lineCanvas, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: "Company Hours",
                data: [],
                borderColor: "#2563eb",
                backgroundColor: "rgba(37, 99, 235, 0.14)",
                fill: true,
                tension: 0.35,
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: { y: { beginAtZero: true } }
        }
    });
}


function updateCharts(chartPayload, completed, progress, pending) {
    if (!barChart || !pieChart || !companyLineChart) return;

    const pieLabels = chartPayload?.pie?.labels || ["Completed", "In Progress", "Pending"];
    const pieData = chartPayload?.pie?.data || [completed, progress, pending];
    const barLabels = chartPayload?.bar?.labels || [];
    const barData = chartPayload?.bar?.data || [completed, progress, pending];
    const lineLabels = chartPayload?.line?.labels || [];
    const lineData = chartPayload?.line?.data || [];

    barChart.data.labels = barLabels;
    barChart.data.datasets[0].data = barData;
    barChart.data.datasets[0].label = "Completed Work Items";
    pieChart.data.labels = pieLabels;
    pieChart.data.datasets[0].data = pieData;
    companyLineChart.data.labels = lineLabels;
    companyLineChart.data.datasets[0].data = lineData;

    barChart.update();
    pieChart.update();
    companyLineChart.update();
}


function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: "smooth" });
        if (sectionId === "tasks") highlightStatusRows("#adminTasksTable", ["In Progress"], "focus-row");
        if (sectionId === "jobs") highlightStatusRows("#jobsTable", ["Open"], "focus-row");
    }
}


function highlightStatusRows(tableSelector, statuses, highlightClass = "focus-row") {
    const rows = Array.from(document.querySelectorAll(`${tableSelector} tbody tr`));
    rows.forEach(row => row.classList.remove("focus-row", "warning-row", "danger-row"));

    const matches = rows.filter(row => statuses.includes(row.dataset.status));
    matches.forEach(row => row.classList.add(highlightClass));

    const first = matches[0];
    if (first) {
        first.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    setTimeout(() => matches.forEach(row => row.classList.remove(highlightClass)), 4000);
}


function refreshAll() {
    loadAdminKPIs();
    loadAllTasks();
    loadAllJobs();
    loadAdminNotifications();
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

function createOption(value, label) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    return option;
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

function createUpdateItem(update) {
    const item = document.createElement("div");
    item.className = "update-item";
    const authorRow = document.createElement("div");
    const author = document.createElement("strong");
    author.textContent = `${update.author_name || "Unknown"} · ${update.author_role || "USER"}`;
    authorRow.appendChild(author);
    const message = document.createElement("div");
    message.textContent = update.message || "";
    const time = document.createElement("small");
    time.textContent = formatDate(update.created_at);
    item.append(authorRow, message, time);
    return item;
}


document.addEventListener("DOMContentLoaded", () => {
    initCharts();
    getCurrentUser();
    refreshAll();
});

setInterval(loadAdminNotifications, 10000);
