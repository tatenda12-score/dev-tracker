// ==========================
// 🔥 API CONFIG
// ==========================
const API_BASE = "https://dev-tracker-yfvj.onrender.com";


// ==========================
// 🔑 GET TOKEN
// ==========================
function getToken() {
    return localStorage.getItem("token");
}


// ==========================
// 🚀 MAIN API REQUEST
// ==========================
async function apiRequest(endpoint, method = "GET", data = null) {
    try {
        const token = getToken();

        const options = {
            method,
            headers: {
                "Content-Type": "application/json"
            }
        };

        // ✅ Attach token
        if (token) {
            options.headers["Authorization"] = `Bearer ${token}`;
        }

        // ✅ Attach body
        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(API_BASE + endpoint, options);

        // ❌ Handle unauthorized
        if (response.status === 401) {
            console.warn("Session expired or invalid token");

            alert("Session expired. Please login again.");
            logout();
            return null;
        }

        const result = await response.json();

        if (!response.ok) {
            console.error("API Error:", result);
            alert(result.detail || result.message || "Something went wrong");
            return null;
        }

        return result;

    } catch (error) {
        console.error("Network Error:", error);
        alert("Network error. Check your connection.");
        return null;
    }
}


// ==========================
// 🔐 LOGIN FUNCTION (FIXED)
// ==========================
async function loginUser(email, password) {

    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    try {
        const response = await fetch(API_BASE + "/auth/login", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            alert(result.detail || "Login failed");
            return null;
        }

        // ✅ CORRECT STRUCTURE (IMPORTANT)
        localStorage.setItem("token", result.access_token);
        localStorage.setItem("userId", result.user.id);
        localStorage.setItem("role", result.user.role);
        localStorage.setItem("email", result.user.email);
        localStorage.setItem("name", result.user.name);

        return result.user;

    } catch (error) {
        console.error("Login error:", error);
        alert("Network error. Try again.");
        return null;
    }
}


// ==========================
// 👤 CURRENT USER
// ==========================
async function getCurrentUser() {
    return await apiRequest("/auth/me");
}


// ==========================
// 🚪 LOGOUT
// ==========================
function logout() {
    localStorage.clear();
    window.location.href = "login.html";
}