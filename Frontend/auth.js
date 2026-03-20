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
            body: formData
        });

        const result = await response.json();

        // ❌ Handle backend error
        if (!response.ok) {
            alert(result.message || result.detail || "Login failed");
            return;
        }

        const data = result;

        // ✅ Save auth data
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("userId", data.user.id);
        localStorage.setItem("role", data.user.role);
        localStorage.setItem("email", data.user.email);
        localStorage.setItem("name", data.user.name);

        // 🔥 Redirect based on role
        if (data.user.role === "ADMIN") {
            window.location.href = "admin.html";
        } else {
            window.location.href = "dashboard.html";
        }

    } catch (error) {
        console.error("Login error:", error);
        alert("Network error. Please try again.");
    }
});