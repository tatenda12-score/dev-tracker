const params = new URLSearchParams(window.location.search);

const userId = params.get("userId");
const email = params.get("email");

if (email) {
    document.getElementById("taskUserTitle").innerText =
        "Tasks for " + email;
}

// Redirect if no token
if (!localStorage.getItem("token")) {
    window.location.href = "index.html";
}

// When page loads
document.addEventListener("DOMContentLoaded", function () {
    loadTasks(userId);
    loadNotifications();
    loadUser();
});

console.log("Dashboard JS loaded");


// CREATE TASK
document.getElementById("taskForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const title = document.getElementById("title").value;
    const description = document.getElementById("description").value;
    const hours_spent = parseFloat(document.getElementById("hours").value);
    const github_link = document.getElementById("github_link").value || null;

    await apiRequest("/tasks/", "POST", {
        title: title,
        description: description,
        hours_spent: hours_spent,
        github_link: github_link
    });

    loadTasks(userId);
});


// LOAD TASKS
async function loadTasks(userId) {

    let endpoint = "/tasks/my-tasks";

    if (userId) {
        endpoint = `/tasks/user/${userId}`;
    }

    const response = await apiRequest(endpoint);

    console.log("Tasks response:", response);

    if (!response.success) return;

    const tasks = response.data.items;

    const container = document.getElementById("tasks");
    container.innerHTML = "";

    tasks.forEach(task => {

        const formattedDate = task.completed_at
            ? new Date(task.completed_at).toLocaleString()
            : "No date";

        container.innerHTML += `
        <div class="task-card">
            <div class="task-header">
                <span>${task.title}</span>
                <span>${task.hours_spent} hrs</span>
            </div>

            <p>${task.description}</p>

            <div class="task-footer">
                <span>Date: ${formattedDate}</span>
                ${task.github_link ? `<a href="${task.github_link}" target="_blank">GitHub</a>` : ""}
            </div>
        </div>
        `;
    });
}


// LOAD USER INFO
async function loadUser() {

    const response = await apiRequest("/users/me");

    console.log(response);

    if (response.success) {
        const user = response.data;

        document.getElementById("userInfo").innerHTML =
            `Logged in as: <strong>${user.name}</strong> (${user.role})`;
    }
}


// LOAD NOTIFICATIONS
async function loadNotifications(){

    const token = localStorage.getItem("token");

    const res = await fetch(
    "http://127.0.0.1:8000/tasks/notifications",
    {
        headers:{
            "Authorization":`Bearer ${token}`
        }
    });

    const data = await res.json();

    const container = document.getElementById("notifications");

    if (!container) return;

    container.innerHTML = "";

    data.forEach(n =>{

       container.innerHTML += `
<div class="notification">
    ${n.message || ""}
</div>
`;
    });

}


// LOGOUT
function logout() {

    localStorage.removeItem("token");
    localStorage.clear();

    window.location.href = "login.html";
}