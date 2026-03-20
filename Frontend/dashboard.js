// ==========================
// 🔐 AUTH CHECK
// ==========================
const token = localStorage.getItem("token");

if (!token) {
    window.location.href = "login.html";
}


// ==========================
// 🚀 INIT
// ==========================
document.addEventListener("DOMContentLoaded", () => {
    loadDashboard();
});


// ==========================
// MAIN LOAD
// ==========================
async function loadDashboard() {
    await Promise.all([
        loadKPIs(),
        loadTasks(),
        loadJobs(),
        loadCharts(),
        loadPerformance()
    ]);
}


// ==========================
// KPI CARDS
// ==========================
async function loadKPIs() {

    const res = await apiRequest("/tasks/my-tasks");
    const tasks = res?.data || [];

    const total = tasks.length;
    const completed = tasks.filter(t => t.status === "Completed").length;
    const inProgress = tasks.filter(t => t.status === "In Progress").length;

    const hoursRes = await apiRequest("/analytics/total-hours");
    const hours = hoursRes?.data?.total_hours || 0;

    document.getElementById("assignedTasks").innerText = total;
    document.getElementById("completedTasks").innerText = completed;
    document.getElementById("inProgressTasks").innerText = inProgress;
    document.getElementById("hoursWorked").innerText = hours + "h";
}


// ==========================
// TASK TABLE
// ==========================
async function loadTasks() {

    const res = await apiRequest("/tasks/my-tasks");
    const tasks = res?.data || [];

    const table = document.getElementById("tasksTable");
    table.innerHTML = "";

    tasks.forEach(task => {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${task.title}</td>
            <td>${getStatusBadge(task.status)}</td>
            <td>${getTaskAction(task)}</td>
        `;

        table.appendChild(row);
    });
}


// ==========================
// JOB TABLE
// ==========================
async function loadJobs() {

    const res = await apiRequest("/job-cards/");
    const jobs = res?.data || [];

    const table = document.getElementById("jobsTable");
    table.innerHTML = "";

    jobs.forEach(job => {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>#${job.id}</td>
            <td>${job.title}</td>
            <td>${getStatusBadge(job.status)}</td>
        `;

        table.appendChild(row);
    });
}


// ==========================
// CHARTS
// ==========================
async function loadCharts(){

    const res = await apiRequest("/tasks/my-tasks");
    const tasks = res?.data || [];

    const completed = tasks.filter(t => t.status === "Completed").length;
    const inProgress = tasks.filter(t => t.status === "In Progress").length;
    const pending = tasks.filter(t => t.status === "Pending").length;

    new Chart(document.getElementById("pieChart"), {
        type: "pie",
        data: {
            labels: ["Completed", "In Progress", "Pending"],
            datasets: [{
                data: [completed, inProgress, pending]
            }]
        }
    });

    // Simple weekly mock (can improve later)
    const weekly = [1,2,3,2,4];

    new Chart(document.getElementById("barChart"), {
        type: "bar",
        data: {
            labels: ["Mon","Tue","Wed","Thu","Fri"],
            datasets: [{
                label: "Tasks",
                data: weekly
            }]
        }
    });
}

// ==========================
// PERFORMANCE
// ==========================
async function loadPerformance() {

    const res = await apiRequest("/analytics/productivity-score");

    const data = res?.data || {};

    document.getElementById("perfCompleted").innerText =
        data.weekly_hours || 0;

    document.getElementById("avgTime").innerText =
        ((data.weekly_hours || 0) / 7).toFixed(2) + " hrs";

    document.getElementById("efficiency").innerText =
        data.productivity_score + "%";
}


// ==========================
// ACTION BUTTONS
// ==========================
function getTaskAction(task) {

    if (task.status === "Pending") {
        return `<button class="btn btn-start" onclick="startTask(${task.id})">Start</button>`;
    }

    if (task.status === "In Progress") {
        return `<button class="btn btn-update" onclick="completeTask(${task.id})">Complete</button>`;
    }

    return `<button class="btn btn-view">View</button>`;
}


// ==========================
// STATUS BADGES
// ==========================
function getStatusBadge(status) {

    if (status === "Pending") {
        return `<span class="badge pending">Pending</span>`;
    }

    if (status === "In Progress") {
        return `<span class="badge progress">In Progress</span>`;
    }

    if (status === "Completed") {
        return `<span class="badge completed">Completed</span>`;
    }

    return status;
}


// ==========================
// TASK ACTIONS
// ==========================
async function startTask(id) {
    await apiRequest(`/tasks/start/${id}`, "PUT");
    loadDashboard();
}

async function completeTask(id) {
    await apiRequest(`/tasks/complete/${id}`, "PUT");
    loadDashboard();
}

function scrollToSection(section){

    const map = {
        dashboard: document.querySelector(".kpi"),
        tasks: document.querySelector("#tasksTable"),
        jobs: document.querySelector("#jobsTable"),
        performance: document.querySelector(".performance")
    };

    if(map[section]){
        map[section].scrollIntoView({ behavior: "smooth" });
    }
}


// ==========================
// LOGOUT
// ==========================
function logout() {
    localStorage.clear();
    window.location.href = "login.html";
}