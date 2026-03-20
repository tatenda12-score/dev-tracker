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

async function toggleNotifications() {

    const panel = document.getElementById("notificationsPanel");

    if (panel.style.display === "block") {
        panel.style.display = "none";
        return;
    }

    panel.style.display = "block";

    await apiRequest("/tasks/notifications/read", "PUT");

    document.getElementById("notifCount").innerText = 0;
    loadAdminNotifications();
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

    const title = document.getElementById("taskTitle").value;
    const description = document.getElementById("taskDescription").value;
    const owner_id = document.getElementById("taskUser").value;

    if(!title || !description){
        alert("Fill all fields");
        return;
    }

    await apiRequest("/tasks/assign-task", "POST", {
        title,
        description,
        owner_id: parseInt(owner_id)
    });

    alert("Task assigned successfully");

    closeAssignModal();
    loadAdminKPIs();
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

    const title = document.getElementById("jobService").value;
    const description = document.getElementById("jobDescription").value;
    const owner_id = document.getElementById("jobUser").value;

    const customer = document.getElementById("jobCustomer").value;
    const contact = document.getElementById("jobContact").value;

    if(!title || !description || !owner_id){
        alert("Fill all required fields");
        return;
    }

    await apiRequest("/job-cards/", "POST", {
        title: `${title} - ${customer}`,
        description: `${description} | Contact: ${contact}`,
        owner_id: parseInt(owner_id)
    });

    alert("Job created successfully");

    closeJobModal();
    loadAdminKPIs();
}


// ==========================
// 🚪 LOGOUT
// ==========================
function logout() {
    localStorage.clear();
    window.location.href = "login.html";
}


// ==========================
// 🚀 START
// ==========================
loadAdminKPIs();
getCurrentUser();
loadAdminNotifications();

setInterval(loadAdminNotifications, 5000);