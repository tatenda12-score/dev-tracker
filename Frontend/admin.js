const token = localStorage.getItem("token");

let selectedUserId = null;
let selectedUserEmail = null;


// LOAD USERS BOARD
async function loadBoard(){

    const response = await fetch("https://dev-tracker-yfvj.onrender.com/users/", {
        headers:{
            "Authorization": `Bearer ${token}`
        }
    });

    const result = await response.json();

    const users = result.data.items
        ? result.data.items.filter(user => user.role !== "ADMIN")
        : result.data.filter(user => user.role !== "ADMIN");

    const container = document.getElementById("usersContainer");
    container.innerHTML = "";

    users.forEach(user => {

        const card = document.createElement("div");
        card.className = "userColumn";

        card.innerHTML = `
            <h3>${user.email}</h3>
            <p>${user.role}</p>
        `;

        // open tasks page
        card.onclick = () => {
            window.location.href =
            `admin_tasks.html?userId=${user.id}&name=${user.name}`;
        };

        container.appendChild(card);
    });
}


// GET CURRENT ADMIN
async function getCurrentUser(){

    const response = await fetch("https://dev-tracker-yfvj.onrender.com/auth/me", {
        headers:{
            "Authorization": `Bearer ${token}`
        }
    });

    const user = await response.json();

    document.getElementById("adminName").innerText =
        "Logged in as: " + user.name;
}


// LOAD USER TASKS
async function loadUserTasks(userId, email){

    selectedUserId = userId;
    selectedUserEmail = email;

    document.getElementById("taskPanel").style.display = "block";

    document.getElementById("taskUserTitle").innerText =
        "Tasks for " + email;

    const response = await fetch(`https://dev-tracker-yfvj.onrender.com/tasks/user/${userId}`,{
        headers:{
            "Authorization": `Bearer ${token}`
        }
    });

    const result = await response.json();

    const taskList = document.getElementById("taskList");

    taskList.innerHTML = "";

    result.data.forEach(task =>{

        const div = document.createElement("div");
        div.innerText = task.title;

        taskList.appendChild(div);

    });

}


// ASSIGN TASK TO USER
async function assignTask(){

    const title = document.getElementById("taskTitle").value;

    if(!title){
        alert("Please enter a task title");
        return;
    }

    await fetch("https://dev-tracker-yfvj.onrender.com/tasks/assign-task",{
        method:"POST",
        headers:{
            "Content-Type":"application/json",
            "Authorization":`Bearer ${token}`
        },
        body:JSON.stringify({
            title:title,
            description:"Assigned by admin",
            owner_id:selectedUserId
        })
    });

    // reload tasks
    loadUserTasks(selectedUserId, selectedUserEmail);

    // clear input
    document.getElementById("taskTitle").value = "";
}
function logout() {

    // remove the saved token
    localStorage.removeItem("token");

    // optional: clear everything
    localStorage.clear();

    // redirect to login page
    window.location.href = "login.html";
}

// START PAGE
loadBoard();
getCurrentUser();