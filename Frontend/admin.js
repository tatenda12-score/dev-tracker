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

        // ================= KPI CALCULATIONS =================
        const totalTasks = tasks.length;

        const completedTasks = tasks.filter(
            t => t.status === "Completed"
        );

        const completedCount = completedTasks.length;

        // Average time (seconds → minutes)
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

        // ================= UI =================
        const card = document.createElement("div");
        card.className = "userColumn";

        card.innerHTML = `
            <h3>${user.email}</h3>
            <p>✔ Completed: ${completedCount}</p>
            <p>⏱ Avg Time: ${avgTime.toFixed(2)} min</p>
            <p>📊 Performance: ${performance}%</p>
            <button onclick="loadUserTasks(${user.id}, '${user.email}')">
                Manage Tasks
            </button>
        `;

        container.appendChild(card);
    }
}


// ==========================
// LOAD USER TASKS (DETAIL PANEL)
// ==========================
async function loadUserTasks(userId, email){

    selectedUserId = userId;
    selectedUserEmail = email;

    document.getElementById("taskPanel").style.display = "block";
    document.getElementById("taskUserTitle").innerText = "Tasks for " + email;

    const response = await fetch(
        `https://dev-tracker-yfvj.onrender.com/tasks/user/${userId}`, {
        headers:{ "Authorization": `Bearer ${token}` }
    });

    const result = await response.json();

    const tasks = result.data || [];

    const taskList = document.getElementById("taskList");
    taskList.innerHTML = "";

    tasks.forEach(task => {
        taskList.innerHTML += `
            <div class="task-card">
                <h4>${task.title}</h4>
                <p>${task.description}</p>
                <small>Status: ${task.status}</small>
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

    const response = await fetch(
        "https://dev-tracker-yfvj.onrender.com/tasks/assign-task",{
        method:"POST",
        headers:{
            "Content-Type":"application/json",
            "Authorization":`Bearer ${token}`
        },
        body:JSON.stringify({
            title,
            description,
            owner_id:selectedUserId,
            status:"Pending"
        })
    });

    const data = await response.json();
    console.log("Assign:", data);

    alert("Task assigned successfully");

    loadUserTasks(selectedUserId, selectedUserEmail);

    document.getElementById("taskTitle").value = "";
    document.getElementById("taskDescription").value = "";
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


// ==========================
// START
// ==========================
loadBoard();
getCurrentUser();