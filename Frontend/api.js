// ==========================
// 🔥 API CONFIG
// ==========================
const API_BASE = "";

function getStorage() {
    return window.sessionStorage;
}

function persistAuth(data) {
    const storage = getStorage();
    storage.setItem("token", data.access_token);
    storage.setItem("user", JSON.stringify(data.user));
    storage.setItem("userId", data.user.id);
    storage.setItem("role", data.user.role);
    storage.setItem("email", data.user.email);
    storage.setItem("name", data.user.name);
}

function migrateLegacyAuth() {
    const session = getStorage();
    if (!session.getItem("token") && localStorage.getItem("token")) {
        const keys = ["token", "user", "userId", "role", "email", "name"];
        keys.forEach((key) => {
            const value = localStorage.getItem(key);
            if (value !== null) {
                session.setItem(key, value);
            }
        });
        localStorage.clear();
    }
}

migrateLegacyAuth();


// ==========================
// 🔑 GET TOKEN
// ==========================
function getToken() {
    return getStorage().getItem("token");
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
        const authData = result.data || result;
        if (!authData?.access_token || !authData?.user) {
            alert("Invalid server response");
            return null;
        }

        persistAuth(authData);

        return authData.user;

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
    sessionStorage.clear();
    localStorage.clear();
    window.location.href = "login.html";
}
