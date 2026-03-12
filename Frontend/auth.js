document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const response = await fetch("http://127.0.0.1:8000/auth/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: formData
    });

    const data = await response.json();

    if (!response.ok) {
        alert(data.detail || "Login failed");
        return;
    }

    // save token
    localStorage.setItem("token", data.access_token);

    // redirect
    if (data.user.role === "ADMIN") {
        window.location.href = "admin.html";
    } else {
        window.location.href = "dashboard.html";
    }
});