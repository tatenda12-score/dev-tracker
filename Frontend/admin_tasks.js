document.addEventListener("DOMContentLoaded", function () {

    const params = new URLSearchParams(window.location.search);
    const userId = params.get("userId");
    const name = params.get("name");

    document.getElementById("taskUserTitle").innerText =
    "Tasks for " + name;

    const token = localStorage.getItem("token");

    const tasksContainer = document.getElementById("tasks");
    const showFormBtn = document.getElementById("showFormBtn");
    const taskFormContainer = document.getElementById("taskFormContainer");
    const closeModalBtn = document.getElementById("closeModalBtn");
    const taskForm = document.getElementById("taskForm");



    // LOAD TASKS
    async function loadTasks() {

        const response = await fetch(
            `https://dev-tracker-yfvj.onrender.com/tasks/user/${userId}`,
            {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        const result = await response.json();

        tasksContainer.innerHTML = "";

        const tasks = result.data;

        tasks.sort((a, b) => {
            const dateA = a.completed_at ? new Date(a.completed_at) : new Date(0);
            const dateB = b.completed_at ? new Date(b.completed_at) : new Date(0);
            return dateB - dateA;
        });

        tasks.forEach(task => {

            const date = task.completed_at
                ? new Date(task.completed_at).toLocaleString()
                : "No date";

            const github = task.github_link
                ? `<a href="${task.github_link}" target="_blank">View GitHub</a>`
                : "";

            tasksContainer.innerHTML += `
                <div class="task-card">
                    <h3>${task.title}</h3>
                    <p>${task.description}</p>

                    <div class="task-meta">
                        <span><strong>Hours:</strong> ${task.hours_spent}</span>
                        <span><strong>Date:</strong> ${date}</span>
                    </div>

                    ${github}
                </div>
            `;
        });

    }



    // OPEN MODAL
    showFormBtn.addEventListener("click", function () {
        taskFormContainer.style.display = "flex";
    });



    // CLOSE MODAL (CANCEL BUTTON)
    closeModalBtn.addEventListener("click", function () {
        taskFormContainer.style.display = "none";
    });



    // SUBMIT TASK FORM
    taskForm.addEventListener("submit", async function (e) {

        e.preventDefault();

        const title = document.getElementById("title").value;
        const description = document.getElementById("description").value;
        const hours = document.getElementById("hours").value;
        const github = document.getElementById("github_link").value;

       await fetch("https://dev-tracker-yfvj.onrender.com/assign-task", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({
                title: title,
                description: description,
                hours_spent: hours,
                github_link: github,
                owner_id: userId
            })
        });
        alert("Task assigned successfully");

        taskFormContainer.style.display = "none";

        loadTasks();

    });



    // INITIAL LOAD
    loadTasks();

});