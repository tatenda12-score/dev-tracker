const API = "https://dev-tracker-yfvj.onrender.com";
const token = localStorage.getItem("token");

async function apiRequest(endpoint){
const res = await fetch(API+endpoint,{
headers:{Authorization:`Bearer ${token}`}
});
return await res.json();
}

document.addEventListener("DOMContentLoaded", loadDashboard);

async function loadDashboard(){

const tasksRes = await apiRequest("/tasks/");
const jobsRes = await apiRequest("/job-cards/");

const tasks = tasksRes.data || [];
const jobs = jobsRes.data || [];

loadKPIs(tasks);
loadCharts(tasks);
renderTasks(tasks);
renderJobs(jobs);
}

// KPI
function loadKPIs(tasks){

totalTasks.innerText = tasks.length;

completedTasks.innerText =
tasks.filter(t=>t.status==="Completed").length;

inProgressTasks.innerText =
tasks.filter(t=>t.status==="In Progress").length;

const seconds = tasks.reduce((s,t)=>s+(t.time_taken||0),0);
hoursWorked.innerText = (seconds/3600).toFixed(1)+"h";
}

// CHARTS
function loadCharts(tasks){

const c = tasks.filter(t=>t.status==="Completed").length;
const p = tasks.filter(t=>t.status==="In Progress").length;
const d = tasks.filter(t=>t.status==="Pending").length;

if(window.pie) pie.destroy();
if(window.bar) bar.destroy();

window.pie = new Chart(pieChart,{
type:"pie",
data:{labels:["Completed","Progress","Pending"],datasets:[{data:[c,p,d]}]}
});

window.bar = new Chart(barChart,{
type:"bar",
data:{labels:["Completed","Progress","Pending"],datasets:[{data:[c,p,d]}]}
});
}

// TASKS
async function loadAllTasks() {

    const res = await apiRequest("/tasks/");
    const tasks = res?.data || [];

    const tbody = document.querySelector("#adminTasksTable tbody");
    tbody.innerHTML = "";

    tasks.forEach(task => {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${task.title}</td>
            <td>${task.description || "N/A"}</td>
            <td>${task.owner_name || "N/A"}</td>
            <td>${getStatusBadge(task.status)}</td>
            <td>${formatDate(task.created_at)}</td>
            <td>${formatDuration(task.time_taken)}</td>
        `;

        tbody.appendChild(row);
    });
}

// JOBS
function renderJobs(jobs){

    const tbody = document.getElementById("jobsTable");
    tbody.innerHTML = "";

    jobs.forEach(job=>{
        tbody.innerHTML += `
        <tr>
            <td>${job.id}</td>
            <td>${job.title}</td>
            <td>${job.status}</td>
        </tr>`;
    });
}

// MODAL
function viewTask(t){
modalTitle.innerText=t.title;
modalDescription.innerText=t.description;
modalStatus.innerText=t.status;
modalTime.innerText=(t.time_taken||0)+" sec";
taskModal.style.display="flex";
}

function closeModal(){
taskModal.style.display="none";
}

// NAV
function scrollToSection(section){

const map={
dashboard:document.querySelector(".kpi"),
tasks:tasksSection,
jobs:jobsSection
};

map[section]?.scrollIntoView({behavior:"smooth"});
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

function getStatusBadge(status) {
    if (status === "Pending") return `<span class="badge pending">Pending</span>`;
    if (status === "In Progress") return `<span class="badge progress">In Progress</span>`;
    if (status === "Completed") return `<span class="badge completed">Completed</span>`;
    return status;
}