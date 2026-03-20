document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!email || !password) {
        alert("Please enter email and password");
        return;
    }

    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    try {
        const response = await fetch("https://dev-tracker-yfvj.onrender.com/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: formData
        });

        let result;
        try {
            result = await response.json();
        } catch (e) {
            alert("Server waking up... please try again in a few seconds.");
            return;
        }

        if (!response.ok) {
            alert(result.message || result.detail || "Login failed");
            return;
        }

        // ✅ Save auth data
        localStorage.setItem("token", result.access_token);
        localStorage.setItem("userId", result.user.id);
        localStorage.setItem("role", result.user.role);
        localStorage.setItem("email", result.user.email);
        localStorage.setItem("name", result.user.name);

        // 🔥 Redirect
        if (result.user.role === "ADMIN") {
            window.location.href = "admin.html";
        } else {
            window.location.href = "dashboard.html";
        }

    } catch (error) {
        console.error("Login error:", error);
        alert("Network error. Please try again.");
    }
});