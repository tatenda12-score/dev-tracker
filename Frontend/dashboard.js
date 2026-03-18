// ================= AUTH CHECK =================
if (!localStorage.getItem("token")) {
    window.location.href = "login.html";
}

document.addEventListener("DOMContentLoaded", function () {
    loadTasks();
    loadNotifications();
    loadUser();
    loadJobCards(); // 🔥 NEW
});


// ================= USER =================
async function loadUser() {

    const response = await apiRequest("/users/me");

    const user = response.data || response;

    document.getElementById("userInfo").innerHTML =
        `Logged in as: <strong>${user.name}</strong> (${user.role})`;
}


// ================= NOTIFICATIONS =================
async function loadNotifications() {

    const response = await apiRequest("/tasks/my-tasks");

    const tasks = response.data?.items || response.data || [];

    const container = document.getElementById("notifications");
    container.innerHTML = "";

    tasks.forEach(task => {

        if (task.status === "Pending") {

            container.innerHTML += `
                <div class="task-card">
                    <h4>${task.title}</h4>
                    <p>${task.description}</p>
                    <button onclick="startTask(${task.id})">Start Task</button>
                </div>
            `;
        }

    });
}


// ================= ACTIVE TASKS =================
async function loadTasks() {

    const response = await apiRequest("/tasks/my-tasks");

    const tasks = response.data?.items || response.data || [];

    const container = document.getElementById("tasks");
    container.innerHTML = "";

    tasks.forEach(task => {

        if (task.status === "In Progress") {

            container.innerHTML += `
                <div class="task-card">
                    <h4>${task.title}</h4>
                    <p>${task.description}</p>
                    <button onclick="completeTask(${task.id})">Complete</button>
                </div>
            `;
        }

    });
}


// ================= JOB CARDS (🔥 NEW FEATURE) =================
async function loadJobCards(){

    const response = await apiRequest("/job-cards/");

    const jobs = response.data || [];

    const container = document.getElementById("jobCards");
    container.innerHTML = "";

    jobs.forEach(job => {

        const assigned = job.created_at
            ? new Date(job.created_at).toLocaleString()
            : "N/A";

        const opened = job.opened_at
            ? new Date(job.opened_at).toLocaleString()
            : "Not started";

        const closed = job.closed_at
            ? new Date(job.closed_at).toLocaleString()
            : "Not completed";

        const duration = job.duration
            ? (job.duration / 60).toFixed(2) + " min"
            : "0 min";

        container.innerHTML += `
            <div class="task-card">
                <h4>${job.title}</h4>
                <p>${job.description}</p>

                <p><strong>Status:</strong> ${job.status}</p>

                <p>📅 Assigned: ${assigned}</p>
                <p>▶ Started: ${opened}</p>
                <p>✅ Closed: ${closed}</p>
                <p>⏱ Duration: ${duration}</p>

                ${
                    job.status === "Pending"
                    ? `<button onclick="openJob(${job.id})">Open Job</button>`
                    : ""
                }

                ${
                    job.status === "Open"
                    ? `
                        <input id="update-${job.id}" placeholder="Add update">
                        <button onclick="addUpdate(${job.id})">Update</button>
                        <button onclick="closeJob(${job.id})">Close Job</button>
                    `
                    : ""
                }
            </div>
        `;
    });
}


// ================= JOB ACTIONS =================
async function openJob(jobId){
    await apiRequest(`/job-cards/open/${jobId}`, "PUT");
    loadJobCards();
}

async function closeJob(jobId){
    await apiRequest(`/job-cards/close/${jobId}`, "PUT");
    loadJobCards();
}

async function addUpdate(jobId){

    const input = document.getElementById(`update-${jobId}`);
    const message = input.value;

    if(!message) return alert("Enter update");

    await apiRequest(`/job-cards/update/${jobId}`, "POST", {
        message: message
    });

    input.value = "";
    loadJobCards();
}


// ================= TASK ACTIONS =================
async function startTask(taskId) {

    await apiRequest(`/tasks/start/${taskId}`, "PUT");

    loadNotifications();
    loadTasks();
}

async function completeTask(taskId) {

    await apiRequest(`/tasks/complete/${taskId}`, "PUT");

    loadTasks();
}