const token = localStorage.getItem("token");

let selectedUserId = null;
let selectedUserEmail = null;


// ==========================
// LOAD KPI DASHBOARD
// ==========================
async function loadBoard(){

    const response = await fetch("https://dev-tracker-yfvj.onrender.com/users/", {
        headers:{ "Authorization": `Bearer ${token}` }
    });

    const result = await response.json();

    const users = result.data?.items || result.data || [];

    const container = document.getElementById("usersContainer");
    container.innerHTML = "";

    for (const user of users) {

        if (user.role === "ADMIN") continue;

        // GET USER TASKS
        const res = await fetch(
            `https://dev-tracker-yfvj.onrender.com/tasks/user/${user.id}`, {
            headers:{ "Authorization": `Bearer ${token}` }
        });

        const taskData = await res.json();
        const tasks = taskData.data || [];

        // KPI CALCULATIONS
        const totalTasks = tasks.length;

        const completedTasks = tasks.filter(
            t => t.status === "Completed"
        );

        const completedCount = completedTasks.length;

        let avgTime = 0;

        if (completedCount > 0) {
            const totalTime = completedTasks.reduce(
                (sum, t) => sum + (t.time_taken || 0),
                0
            );

            avgTime = (totalTime / completedCount) / 60;
        }

        const performance = totalTasks > 0
            ? Math.round((completedCount / totalTasks) * 100)
            : 0;

        // UI
        const card = document.createElement("div");
        card.className = "userColumn";

        card.innerHTML = `
            <h3>${user.email}</h3>
            <p>✔ Completed: ${completedCount}</p>
            <p>⏱ Avg Time: ${avgTime.toFixed(2)} min</p>
            <p>📊 Performance: ${performance}%</p>
            <button onclick="loadUserTasks(${user.id}, '${user.email}')">
                Manage Work
            </button>
        `;

        container.appendChild(card);
    }
}


// ==========================
// LOAD USER TASKS + JOB CARDS
// ==========================
async function loadUserTasks(userId, email){

    selectedUserId = userId;
    selectedUserEmail = email;

    document.getElementById("taskPanel").style.display = "block";
    document.getElementById("taskUserTitle").innerText = "Work for " + email;

    const taskList = document.getElementById("taskList");
    taskList.innerHTML = "";

    // ================= TASKS =================
    const response = await fetch(
        `https://dev-tracker-yfvj.onrender.com/tasks/user/${userId}`, {
        headers:{ "Authorization": `Bearer ${token}` }
    });

    const result = await response.json();
    const tasks = result.data || [];

    taskList.innerHTML += `<h3>Tasks</h3>`;

    tasks.forEach(task => {

        const assigned = task.created_at
            ? new Date(task.created_at).toLocaleString()
            : "N/A";

        const started = task.start_time
            ? new Date(task.start_time).toLocaleString()
            : "Not started";

        const completed = task.end_time
            ? new Date(task.end_time).toLocaleString()
            : "Not completed";

        const duration = task.time_taken
            ? (task.time_taken / 60).toFixed(2) + " min"
            : "0 min";

        taskList.innerHTML += `
            <div class="task-card">
                <h4>${task.title}</h4>
                <p>${task.description}</p>

                <p><strong>Status:</strong> ${task.status}</p>

                <p>📅 Assigned: ${assigned}</p>
                <p>▶ Started: ${started}</p>
                <p>✅ Completed: ${completed}</p>
                <p>⏱ Duration: ${duration}</p>
            </div>
        `;
    });

    // ================= JOB CARDS =================
    const jobRes = await fetch(
        `https://dev-tracker-yfvj.onrender.com/job-cards/`, {
        headers:{ "Authorization": `Bearer ${token}` }
    });

    const jobData = await jobRes.json();
    const jobs = jobData.data || [];

    taskList.innerHTML += `<h3>Job Cards</h3>`;

    jobs
    .filter(j => j.owner_id === userId)
    .forEach(job => {

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

        taskList.innerHTML += `
            <div class="task-card">
                <h4>${job.title}</h4>
                <p>${job.description}</p>

                <p><strong>Status:</strong> ${job.status}</p>

                <p>📅 Assigned: ${assigned}</p>
                <p>▶ Started: ${opened}</p>
                <p>✅ Closed: ${closed}</p>
                <p>⏱ Duration: ${duration}</p>
            </div>
        `;
    });
}


// ==========================
// ASSIGN TASK
// ==========================
async function assignTask(){

    const title = document.getElementById("taskTitle").value;
    const description = document.getElementById("taskDescription").value;

    if(!title || !description || !selectedUserId){
        alert("Fill all fields and select user");
        return;
    }

    await fetch(
        "https://dev-tracker-yfvj.onrender.com/tasks/assign-task",{
        method:"POST",
        headers:{
            "Content-Type":"application/json",
            "Authorization":`Bearer ${token}`
        },
        body:JSON.stringify({
            title,
            description,
            owner_id:selectedUserId
        })
    });

    alert("Task assigned successfully");

    loadUserTasks(selectedUserId, selectedUserEmail);

    document.getElementById("taskTitle").value = "";
    document.getElementById("taskDescription").value = "";
}


// ==========================
// CREATE JOB CARD (🔥 NEW)
// ==========================
async function createJobCard(){

    const title = document.getElementById("jobTitle").value;
    const description = document.getElementById("jobDescription").value;

    if(!title || !description || !selectedUserId){
        alert("Fill all fields and select user");
        return;
    }

    await fetch(
        "https://dev-tracker-yfvj.onrender.com/job-cards/",{
        method:"POST",
        headers:{
            "Content-Type":"application/json",
            "Authorization":`Bearer ${token}`
        },
        body:JSON.stringify({
            title,
            description,
            owner_id:selectedUserId
        })
    });

    alert("Job card created successfully");

    loadUserTasks(selectedUserId, selectedUserEmail);

    document.getElementById("jobTitle").value = "";
    document.getElementById("jobDescription").value = "";
}


// ==========================
// ADMIN NAME
// ==========================
async function getCurrentUser(){

    const response = await fetch("https://dev-tracker-yfvj.onrender.com/auth/me", {
        headers:{ "Authorization": `Bearer ${token}` }
    });

    const user = await response.json();

    document.getElementById("adminName").innerText =
        "Logged in as: " + (user.data?.name || "Admin");
}


// ==========================
// LOGOUT
// ==========================
function logout(){
    localStorage.clear();
    window.location.href = "login.html";
}

function openDrawer(userId, email){
    selectedUserId = userId;
    selectedUserEmail = email;

    document.getElementById("drawerUserTitle").innerText = "Work for " + email;
    document.getElementById("workDrawer").classList.add("active");

    loadDrawerTasks(userId);
}

function closeDrawer(){
    document.getElementById("workDrawer").classList.remove("active");
}

async function loadDrawerTasks(userId){

    const response = await fetch(
        `https://dev-tracker-yfvj.onrender.com/tasks/user/${userId}`, {
        headers:{ "Authorization": `Bearer ${token}` }
    });

    const result = await response.json();
    const tasks = result.data || [];

    const container = document.getElementById("drawerTaskList");
    container.innerHTML = "";

    tasks.forEach(task => {

        container.innerHTML += `
            <div class="task-card">
                <h4>${task.title}</h4>
                <p>${task.description}</p>
                <p>Status: ${task.status}</p>
            </div>
        `;
    });
}


// ==========================
// START
// ==========================
loadBoard();
getCurrentUser();