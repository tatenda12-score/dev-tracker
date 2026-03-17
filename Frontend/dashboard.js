// Redirect if no token
if (!localStorage.getItem("token")) {
    window.location.href = "login.html";
}

document.addEventListener("DOMContentLoaded", function () {
    loadTasks();
    loadNotifications();
    loadUser();
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


// ================= START TASK =================
async function startTask(taskId) {

    await apiRequest(`/tasks/start/${taskId}`, "PUT");

    loadNotifications();
    loadTasks();
}


// ================= COMPLETE TASK =================
async function completeTask(taskId) {

    await apiRequest(`/tasks/complete/${taskId}`, "PUT");

    loadTasks();
}