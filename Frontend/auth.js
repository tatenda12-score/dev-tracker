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

        if (!response.ok) {
            alert(result.detail || "Login failed");
            return;
        }

        // ✅ FIX: extract from result.data
        const data = result.data;

        if (!data || !data.user) {
            alert("Invalid server response");
            return;
        }

        // ✅ SAVE CORRECTLY
        persistAuth(data);

        // ✅ REDIRECT
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
