const token = localStorage.getItem("token");

let selectedUserId = null;
let selectedUserEmail = null;


// LOAD USERS
async function loadBoard(){

    const response = await fetch("https://dev-tracker-yfvj.onrender.com/users/", {
        headers:{ "Authorization": `Bearer ${token}` }
    });

    const result = await response.json();

    const users = result.data.items || result.data || [];

    const container = document.getElementById("usersContainer");
    container.innerHTML = "";

    users.filter(u => u.role !== "ADMIN").forEach(user => {

        const card = document.createElement("div");
        card.className = "userColumn";

        card.innerHTML = `
            <h3>${user.email}</h3>
            <p>${user.role}</p>
        `;

        card.onclick = () => loadUserTasks(user.id, user.email);

        container.appendChild(card);
    });
}


// LOAD USER TASKS
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


// ASSIGN TASK
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

    loadUserTasks(selectedUserId, selectedUserEmail);

    document.getElementById("taskTitle").value = "";
    document.getElementById("taskDescription").value = "";
}


// ADMIN NAME
async function getCurrentUser(){

    const response = await fetch("https://dev-tracker-yfvj.onrender.com/auth/me", {
        headers:{ "Authorization": `Bearer ${token}` }
    });

    const user = await response.json();

    document.getElementById("adminName").innerText =
        "Logged in as: " + (user.data?.name || "Admin");
}


// LOGOUT
function logout(){
    localStorage.clear();
    window.location.href = "login.html";
}


// START
loadBoard();
getCurrentUser();