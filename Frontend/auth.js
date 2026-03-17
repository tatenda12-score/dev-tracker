document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const response = await fetch("https://dev-tracker-yfvj.onrender.com/auth/login", {
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

    // ✅ SAVE EVERYTHING
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("userId", data.user.id);
    localStorage.setItem("role", data.user.role);
    localStorage.setItem("email", data.user.email);

    // redirect
    if (data.user.role === "ADMIN") {
        window.location.href = "admin.html";
    } else {
        window.location.href = "dashboard.html";
    }
});