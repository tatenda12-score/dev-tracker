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

    // 🔥 SET USER NAME IMMEDIATELY
    const user = JSON.parse(localStorage.getItem("user"));

    if (user && user.name) {
        const title = document.getElementById("dashboardTitle");
        if (title) {
            title.innerText = "Welcome, " + user.name;
        }
    }

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

    const totalSeconds = tasks.reduce((sum, t) => sum + (t.time_taken || 0), 0);
    const hours = (totalSeconds / 3600).toFixed(2);

    document.getElementById("assignedTasks").innerText = total;
    document.getElementById("completedTasks").innerText = completed;
    document.getElementById("inProgressTasks").innerText = inProgress;
    document.getElementById("hoursWorked").innerText = hours + "h";

    const user = JSON.parse(localStorage.getItem("user"));

    if (user && user.name) {
        const title = document.getElementById("dashboardTitle");
    if (title) {
        title.innerText = "Welcome, " + user.name;
    }
    }
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

    // ✅ FIX: correct structure (same as tasks)
    const jobs = res?.data || [];

    const table = document.getElementById("jobsTable");
    table.innerHTML = "";

    jobs.forEach(job => {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>#${job.id}</td>
            <td>${job.title}</td>
            <td>${getStatusBadge(job.status)}</td>
            <td><button class="btn btn-view" onclick='viewJob(${JSON.stringify(job)})'>View</button></td>
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

    if (window.pieChartInstance) {
        window.pieChartInstance.destroy();
    }

    if (window.barChartInstance) {
        window.barChartInstance.destroy();
    }

    window.pieChartInstance = new Chart(document.getElementById("pieChart"), {
        type: "pie",
        data: {
            labels: ["Completed", "In Progress", "Pending"],
            datasets: [{
                data: [completed, inProgress, pending]
            }]
        }
    });

    const weekly = [1, 2, 3, 2, 4];

    window.barChartInstance = new Chart(document.getElementById("barChart"), {
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

    try {
        const res = await apiRequest("/analytics/productivity-score");
        const data = res?.data || {};

        document.getElementById("perfCompleted").innerText =
            data.weekly_hours || 0;

        document.getElementById("avgTime").innerText =
            ((data.weekly_hours || 0) / 7).toFixed(2) + " hrs";

        document.getElementById("efficiency").innerText =
            (data.productivity_score || 0) + "%";

    } catch (err) {
        console.log("Performance API not working yet");
    }
}


// ==========================
// ACTION BUTTONS
// ==========================
function getTaskAction(task) {
    return `<button class="btn btn-view" onclick='viewTask(${JSON.stringify(task)})'>View</button>`;
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


// ==========================
// NAVIGATION
// ==========================
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

async function viewJob(id) {
    alert("Viewing job ID: " + id);
    // later we can replace with modal popup
}

async function closeJob(id) {
    await apiRequest(`/job-cards/close/${id}`, "PUT");
    loadDashboard(); // refresh after closing
}
function viewTask(task) {

    document.getElementById("modalTitle").innerText = task.title;
    document.getElementById("modalDescription").innerText = task.description || "N/A";
    document.getElementById("modalStatus").innerText = task.status;

    document.getElementById("modalGithub").innerText = task.github_link || "N/A";
    document.getElementById("modalGithub").href = task.github_link || "#";

    document.getElementById("modalStart").innerText = task.start_time || "N/A";
    document.getElementById("modalEnd").innerText = task.end_time || "N/A";

    document.getElementById("modalTime").innerText = formatTime(task.time_taken);

    // 🔥 ADD THIS BLOCK HERE
    const actions = document.getElementById("modalActions");

    if (task.status === "Pending") {
        actions.innerHTML = `
            <button class="btn btn-start" onclick="startTask(${task.id}); closeModal();">
                Start Task
            </button>
        `;
    }
    else if (task.status === "In Progress") {
        actions.innerHTML = `
            <button class="btn btn-update" onclick="completeTask(${task.id}); closeModal();">
                Complete Task
            </button>
        `;
    }
    else {
        actions.innerHTML = `<span class="badge completed">Completed</span>`;
    }

    document.getElementById("taskModal").style.display = "flex";
}

function closeModal() {
    document.getElementById("taskModal").style.display = "none";
}

function formatTime(seconds) {

    if (!seconds) return "0 min";

    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);

    if (hrs > 0) {
        return `${hrs}h ${mins}m`;
    }

    return `${mins} min`;
}

function viewJob(job) {

    currentJobId = job.id;

    document.getElementById("jobTitle").innerText = job.title;
    document.getElementById("jobDescription").innerText = job.description || "N/A";
    document.getElementById("jobStatus").innerText = job.status;

    document.getElementById("jobGithub").innerText = job.github_link || "N/A";
    document.getElementById("jobGithub").href = job.github_link || "#";

    document.getElementById("jobCreated").innerText = job.created_at || "N/A";
    document.getElementById("jobOpened").innerText = job.opened_at || "N/A";
    document.getElementById("jobClosed").innerText = job.closed_at || "N/A";

    const actions = document.getElementById("jobActions");
    const updateSection = document.getElementById("jobUpdateSection");

    // 🔥 STATUS LOGIC
    if (job.status === "Pending") {

        updateSection.style.display = "none";

        actions.innerHTML = `
            <button class="btn btn-start" onclick="startJob(${job.id}); closeJobModal();">
                Start Job
            </button>
        `;
    }
    else if (job.status === "Open" || job.status === "In Progress") {

        updateSection.style.display = "block";

        actions.innerHTML = `
            <button class="btn btn-update" onclick="closeJob(${job.id}); closeJobModal();">
                Close Job
            </button>
        `;
    }
    else {

        updateSection.style.display = "none";

        actions.innerHTML = `<span class="badge completed">Closed</span>`;
    }

    document.getElementById("jobModal").style.display = "flex";
}

function closeJobModal() {
    document.getElementById("jobModal").style.display = "none";
}

async function startJob(id) {
    await apiRequest(`/job-cards/open/${id}`, "PUT"); 
    loadDashboard();
}

async function closeJob(id) {
    await apiRequest(`/job-cards/close/${id}`, "PUT");
    loadDashboard();
}

async function addJobUpdate() {

    const message = document.getElementById("jobUpdateInput").value.trim();

    if (!message) {
        alert("Write an update first");
        return;
    }

    await apiRequest(`/job-cards/update/${currentJobId}`, "POST", {
        message: message
    });

    document.getElementById("jobUpdateInput").value = "";

    alert("Update added");

    loadDashboard();
}
// ==========================
// LOGOUT
// ==========================
function logout() {
    localStorage.clear();
    window.location.href = "login.html";
}