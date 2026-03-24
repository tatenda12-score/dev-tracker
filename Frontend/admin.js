const API = "https://dev-tracker-yfvj.onrender.com";
const token = localStorage.getItem("token");

let barChart = null;
let pieChart = null;
let currentAdminTaskId = null;
let currentAdminJobId = null;


async function apiRequest(endpoint, method = "GET", data = null) {
    try {
        const res = await fetch(API + endpoint, {
            method,
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
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

    const completed = pieData[0] ?? tasks.filter(task => task.status === "Completed").length;
    const progress = pieData[1] ?? tasks.filter(task => task.status === "In Progress").length;
    const pending = pieData[2] ?? tasks.filter(task => task.status === "Pending").length;

    document.getElementById("activeTasks").innerText = progress;
    document.getElementById("completedTasks").innerText = completed;
    document.getElementById("overdueTasks").innerText = pending;

    updateCharts(chartsRes, completed, progress, pending);
}


async function loadAdminNotifications() {
    const response = await apiRequest("/tasks/notifications");
    const notifications = response?.data || [];
    const unreadCount = response?.meta?.unread_count || 0;
    const panel = document.getElementById("notificationsPanel");

    document.getElementById("adminNotificationCount").innerText = unreadCount;
    panel.innerHTML = "";

    if (!notifications.length) {
        panel.innerHTML = `<div class="notification-item">No admin notifications yet.<small>Updates will appear here.</small></div>`;
        return;
    }

    notifications.slice(0, 8).forEach(notification => {
        panel.innerHTML += `
            <div class="notification-item ${notification.is_read ? "" : "unread"}">
                <div class="notification-message">${notification.message}</div>
                <small>${formatDate(notification.created_at)}</small>
            </div>
        `;
    });
}


async function markAdminNotificationsRead() {
    await apiRequest("/tasks/notifications/read", "PUT");
    loadAdminNotifications();
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
            select.innerHTML += `<option value="${user.id}">${user.name}</option>`;
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


async function loadUsersForJobDropdown() {
    const res = await apiRequest("/users/");
    const users = res?.data || [];
    const select = document.getElementById("jobUser");
    select.innerHTML = "";

    users.forEach(user => {
        if (user.role !== "ADMIN") {
            select.innerHTML += `<option value="${user.id}">${user.name}</option>`;
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

    tasks.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

    tasks.forEach(task => {
        const row = document.createElement("tr");
        row.className = "clickable-row";
        row.innerHTML = `
            <td>${task.id}</td>
            <td>${task.owner_name || "N/A"}</td>
            <td>${task.title}</td>
            <td>${task.description || "N/A"}</td>
            <td>${task.status}</td>
            <td>${task.github_link || "-"}</td>
            <td>${formatDate(task.created_at)}</td>
            <td>${formatDuration(task.time_taken)}</td>
        `;
        row.addEventListener("click", () => viewAdminTask(task.id));
        tbody.appendChild(row);
    });
}


async function loadAllJobs() {
    const res = await apiRequest("/job-cards/");
    const jobs = res?.data || [];
    const tbody = document.querySelector("#jobsTable tbody");
    tbody.innerHTML = "";

    jobs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

    jobs.forEach(job => {
        const row = document.createElement("tr");
        row.className = "clickable-row";
        row.innerHTML = `
            <td>${job.id}</td>
            <td>${job.title}</td>
            <td>${job.status}</td>
            <td>${formatDate(job.created_at)}</td>
            <td>${formatDuration(job.duration)}</td>
        `;
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
        container.innerHTML = `<div class="update-item">No updates yet.</div>`;
        return;
    }

    updates.forEach(update => {
        container.innerHTML += `
            <div class="update-item">
                <div><strong>${update.author_name || "Unknown"} · ${update.author_role || "USER"}</strong></div>
                <div>${update.message}</div>
                <small>${formatDate(update.created_at)}</small>
            </div>
        `;
    });
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
    if (!barCanvas || !pieCanvas) return;

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
            cutout: "65%",
            plugins: { legend: { position: "bottom" } }
        }
    });
}


function updateCharts(chartPayload, completed, progress, pending) {
    if (!barChart || !pieChart) return;

    const pieLabels = chartPayload?.pie?.labels || ["Completed", "In Progress", "Pending"];
    const pieData = chartPayload?.pie?.data || [completed, progress, pending];
    const barLabels = chartPayload?.bar?.labels || ["Completed", "In Progress", "Pending"];
    const barData = chartPayload?.bar?.data || [completed, progress, pending];

    barChart.data.labels = barLabels;
    barChart.data.datasets[0].data = barData;
    pieChart.data.labels = pieLabels;
    pieChart.data.datasets[0].data = pieData;

    barChart.update();
    pieChart.update();
}


function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: "smooth" });
    }
}


function refreshAll() {
    loadAdminKPIs();
    loadAllTasks();
    loadAllJobs();
    loadAdminNotifications();
}


function logout() {
    localStorage.clear();
    window.location.href = "login.html";
}


document.addEventListener("DOMContentLoaded", () => {
    initCharts();
    getCurrentUser();
    refreshAll();
});

setInterval(loadAdminNotifications, 10000);
