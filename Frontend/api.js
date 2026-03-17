const BASE_URL = "https://dev-tracker-yfvj.onrender.com";

async function apiRequest(endpoint, method="GET", data=null) {

    const token = localStorage.getItem("token");

    const options = {
        method: method,
        headers: {
            "Content-Type": "application/json"
        }
    };

    if (token) {
        options.headers["Authorization"] = `Bearer ${token}`;
    }

    if (data) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(BASE_URL + endpoint, options);

    const result = await response.json();

    console.log("API:", endpoint, result); // DEBUG

    return result;
}

function logout() {
    localStorage.clear();
    window.location.href = "login.html";
}