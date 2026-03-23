// ==========================
// 🔥 API CONFIG
// ==========================
const API = "https://dev-tracker-yfvj.onrender.com";
const token = localStorage.getItem("token");

// ==========================
// 🔥 API HELPER
// ==========================
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

        return await res.json();

    } catch (err) {
        console.error("API Error:", err);
        alert("Network error");
        return null;
    }
}

// ==========================
// 👤 USER INFO
// ==========================
async function getCurrentUser() {
    const res = await apiRequest("/auth/me");

    document.getElementById("adminName").innerText =
        "Logged in as: " + (res?.data?.name || "Admin");
}

// ==========================
// 📊 KPI DASHBOARD
// ==========================
async function loadAdminKPIs() {

    const tasksRes = await apiRequest("/tasks/");
    const jobsRes = await apiRequest("/job-cards/");

    const tasks = tasksRes?.data || [];
    const jobs = jobsRes?.data || [];

    document.getElementById("totalJobs").innerText = jobs.length;

    document.getElementById("activeTasks").innerText =
        tasks.filter(t => t.status === "In Progress").length;

    document.getElementById("completedTasks").innerText =
        tasks.filter(t => t.status === "Completed").length;

    document.getElementById("overdueTasks").innerText =
        tasks.filter(t => t.status === "Pending").length;
}

// ==========================
// 🔔 NOTIFICATIONS
// ==========================
async function loadAdminNotifications(){
    const panel = document.getElementById("notificationsPanel");
    if (!panel) return;

    const response = await apiRequest("/tasks/notifications");
    const notifications = response?.data || [];

    panel.innerHTML = "";

    notifications.forEach(n => {
        panel.innerHTML += `<div class="notif-item">${n.message}</div>`;
    });
}

// ==========================
// 📝 ASSIGN TASK MODAL
// ==========================
function openAssignModal(){
    document.getElementById("assignModal").style.display = "block";
    loadUsersForDropdown();
}

function closeAssignModal(){
    document.getElementById("assignModal").style.display = "none";
}

async function loadUsersForDropdown(){
    const res = await apiRequest("/users/");
    const users = res?.data || [];

    const select = document.getElementById("taskUser");
    select.innerHTML = "";

    users.forEach(u => {
        if(u.role !== "ADMIN"){
            select.innerHTML += `<option value="${u.id}">${u.name}</option>`;
        }
    });
}

async function submitTask(){
    const title = taskTitle.value;
    const description = taskDescription.value;
    const owner_id = taskUser.value;

    await apiRequest("/tasks/assign-task", "POST", {
        title,
        description,
        owner_id: parseInt(owner_id)
    });

    closeAssignModal();
    refreshAll();
}

// ==========================
// 🧰 CREATE JOB MODAL
// ==========================
function openJobModal(){
    document.getElementById("jobModal").style.display = "block";
    loadUsersForJobDropdown();
}

function closeJobModal(){
    document.getElementById("jobModal").style.display = "none";
}

async function loadUsersForJobDropdown(){
    const res = await apiRequest("/users/");
    const users = res?.data || [];

    const select = document.getElementById("jobUser");
    select.innerHTML = "";

    users.forEach(u => {
        if(u.role !== "ADMIN"){
            select.innerHTML += `<option value="${u.id}">${u.name}</option>`;
        }
    });
}

async function submitJob(){
    const title = jobService.value;
    const description = jobDescription.value;
    const owner_id = jobUser.value;

    await apiRequest("/job-cards/", "POST", {
        title,
        description,
        owner_id: parseInt(owner_id)
    });

    closeJobModal();
    refreshAll();
}

// ==========================
// 📋 TASK TABLE
// ==========================
async function loadAllTasks() {

    const res = await apiRequest("/tasks/");
    let tasks = res?.data || [];

    // 🔥 SORT latest first
    tasks.sort((a,b)=>new Date(b.created_at)-new Date(a.created_at));

    const tbody = document.querySelector("#adminTasksTable tbody");
    if (!tbody) return;

    tbody.innerHTML = "";

    tasks.forEach(task => {
        tbody.innerHTML += `
        <tr>
            <td>${task.id}</td>
            <td>${task.owner_name || "N/A"}</td>
            <td>${task.title}</td>
            <td>${task.description || "N/A"}</td>
            <td>${task.status}</td>
            <td>${task.github_link || "-"}</td>
            <td>${formatDate(task.created_at)}</td>
            <td>${formatDuration(task.time_taken)}</td>
        </tr>`;
    });
}

// ==========================
// 📋 JOB CARDS TABLE
// ==========================
async function loadAllJobs(){

    const res = await apiRequest("/job-cards/");
    let jobs = res?.data || [];

    jobs.sort((a,b)=>new Date(b.created_at)-new Date(a.created_at));

    const tbody = document.querySelector("#jobsTable tbody");
    if (!tbody) return;

    tbody.innerHTML = "";

    jobs.forEach(job => {
        tbody.innerHTML += `
        <tr>
            <td>${job.id}</td>
            <td>${job.title}</td>
            <td>${job.status}</td>
            <td>${formatDate(job.created_at)}</td>
            <td>${formatDuration(job.time_taken)}</td>
        </tr>`;
    });
}

// ==========================
// 🧠 HELPERS
// ==========================
function formatDate(date){
    return date ? new Date(date).toLocaleString() : "N/A";
}

function formatDuration(seconds){
    if(!seconds) return "0 min";
    const mins = Math.floor(seconds/60);
    const hrs = Math.floor(mins/60);
    return hrs>0 ? `${hrs}h ${mins%60}m` : `${mins} min`;
}

// ==========================
// 🔄 REFRESH
// ==========================
function refreshAll(){
    loadAdminKPIs();
    loadAllTasks();
    loadAllJobs();
}

// ==========================
// 🚪 LOGOUT
// ==========================
function logout(){
    localStorage.clear();
    window.location.href = "login.html";
}

// ==========================
// 🚀 START
// ==========================
document.addEventListener("DOMContentLoaded", ()=>{
    getCurrentUser();
    loadAdminKPIs();
    loadAdminNotifications();
    loadAllTasks();
    loadAllJobs();
});

setInterval(loadAdminNotifications, 5000);