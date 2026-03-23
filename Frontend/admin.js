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
function renderTasks(tasks){

tasksTable.innerHTML="";

tasks.forEach(t=>{
tasksTable.innerHTML+=`
<tr>
<td>${t.title}</td>
<td>${t.status}</td>
<td><button onclick='viewTask(${JSON.stringify(t)})'>View</button></td>
</tr>`;
});
}

// JOBS
function renderJobs(jobs){

jobsTable.innerHTML="";

jobs.forEach(j=>{
jobsTable.innerHTML+=`
<tr>
<td>${j.id}</td>
<td>${j.title}</td>
<td>${j.status}</td>
<td><button>View</button></td>
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