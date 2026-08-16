"use strict";

/* =========================================================
   DOM & VARIABLES
========================================================= */
const cpuEl        = document.getElementById("cpu");
const ramEl        = document.getElementById("ram");
const cpuBar       = document.getElementById("cpuBar");
const ramBar       = document.getElementById("ramBar");
const volumeBar    = document.getElementById("volumeBar");
const brightnessBar= document.getElementById("brightnessBar");
const trackTitle   = document.getElementById("trackTitle");
const trackArtist  = document.getElementById("trackArtist");
const coverImg     = document.getElementById("coverImg");
const coverFallback= document.getElementById("coverFallback");
const playBtn      = document.getElementById("playBtn");
const fullscreenBtn= document.getElementById("fullscreenBtn");
const modal        = document.getElementById("modal");
const modalTitle   = document.getElementById("modalTitle");
const modalText    = document.getElementById("modalText");
const cancelBtn    = document.getElementById("cancelBtn");
const confirmBtn   = document.getElementById("confirmBtn");
const toast        = document.getElementById("toast");
const toastIcon    = document.getElementById("toastIcon");
const toastText    = document.getElementById("toastText");

// Info & Settings Modal Elements
const infoModal          = document.getElementById("infoModal");
const appsPanel          = document.getElementById("appsPanel");
const appSelectionGrid   = document.getElementById("appSelectionGrid");
const appCountBadge      = document.getElementById("appCountBadge");
const themeToggleBtn     = document.getElementById("themeToggleBtn");

let pendingPowerAction = null;
let toastTimer = null;
let lastCover = null;

/* =========================================================
   APPS LIST & SELECTION MANAGEMENT (MAX 9)
========================================================= */
const ALL_AVAILABLE_APPS = [
    { id: "chrome", name: "Chrome", icon: "🌐", endpoint: "/api/open/chrome" },
    { id: "cmd", name: "CMD", icon: ">_", endpoint: "/api/open/cmd" },
    { id: "vscode", name: "VS Code", icon: "</>", endpoint: "/api/open/vscode" },
    { id: "vs", name: "VS", icon: "▣", endpoint: "/api/open/vs" },
    { id: "settings", name: "Settings", icon: "⚙", endpoint: "/api/open/settings" },
    { id: "spotify", name: "Spotify", icon: "♪", endpoint: "/api/open/spotify" },
    { id: "explorer", name: "Explorer", icon: "📁", endpoint: "/api/open/explorer" },
    { id: "windows", name: "Windows", icon: "⊞", endpoint: "/api/open/windows" },
    { id: "powershell", name: "PowerShell", icon: "PS", endpoint: "/api/open/powershell" },
    { id: "whatsapp", name: "WhatsApp", icon: "💬", endpoint: "/api/open/whatsapp" },
    { id: "telegram", name: "Telegram", icon: "✈", endpoint: "/api/open/telegram" },
    { id: "capcut", name: "CapCut", icon: "🎬", endpoint: "/api/open/capcut" }
];

let selectedAppIds = JSON.parse(localStorage.getItem("pc_selected_apps")) || [
    "chrome", "cmd", "vscode", "vs", "settings", "spotify", "explorer", "windows", "powershell"
];

function renderAppsPanel() {
    const appsPanel = document.getElementById("appsPanel");
    if (!appsPanel) return;
    
    appsPanel.innerHTML = "";
    const activeApps = ALL_AVAILABLE_APPS.filter(a => selectedAppIds.includes(a.id)).slice(0, 9);
    
    activeApps.forEach(app => {
        const btn = document.createElement("button");
        btn.className = "app-btn";
        btn.onclick = () => sendCommand(app.endpoint);
        btn.innerHTML = `<span class="icon">${app.icon}</span>${app.name}`;
        appsPanel.appendChild(btn);
    });
}

function renderAppSelectionGrid() {
    const appSelectionGrid = document.getElementById("appSelectionGrid");
    const appCountBadge = document.getElementById("appCountBadge");
    if (!appSelectionGrid) return;

    appSelectionGrid.innerHTML = "";
    if (appCountBadge) appCountBadge.textContent = `${selectedAppIds.length}/9`;

    ALL_AVAILABLE_APPS.forEach(app => {
        const isChecked = selectedAppIds.includes(app.id);
        const label = document.createElement("label");
        label.className = "app-checkbox-label";
        
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = isChecked;
        
        checkbox.addEventListener("change", () => {
            if (checkbox.checked) {
                if (selectedAppIds.length >= 9) {
                    checkbox.checked = false;
                    showToast("!", "Maksimum 9 tətbiq seçilə bilər");
                    return;
                }
                selectedAppIds.push(app.id);
            } else {
                selectedAppIds = selectedAppIds.filter(id => id !== app.id);
            }
            localStorage.setItem("pc_selected_apps", JSON.stringify(selectedAppIds));
            if (appCountBadge) appCountBadge.textContent = `${selectedAppIds.length}/9`;
            renderAppsPanel();
        });

        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(` ${app.icon} ${app.name}`));
        appSelectionGrid.appendChild(label);
    });
}

/* =========================================================
   THEME TOGGLE (DARK / LIGHT)
========================================================= */
function initTheme() {
    const isDark = localStorage.getItem("pc_theme_dark") === "true";
    if (isDark) {
        document.body.classList.add("dark-mode");
        themeToggleBtn.textContent = "☀️ Light Mode";
    } else {
        document.body.classList.remove("dark-mode");
        themeToggleBtn.textContent = "🌙 Dark Mode";
    }
}

function toggleTheme() {
    const isDark = document.body.classList.toggle("dark-mode");
    localStorage.setItem("pc_theme_dark", isDark);
    themeToggleBtn.textContent = isDark ? "☀️ Light Mode" : "🌙 Dark Mode";
}

/* =========================================================
   INFO MODAL & GITHUB API
========================================================= */
function openInfoModal() {
    const modalEl = document.getElementById("infoModal");
    if (modalEl) {
        modalEl.classList.remove("hidden");
        fetchGitHubData();
    }
}

function closeInfoModal() {
    const modalEl = document.getElementById("infoModal");
    if (modalEl) {
        modalEl.classList.add("hidden");
    }
}

function switchInfoTab(tabName, btnEvent) {
    document.querySelectorAll(".info-tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
    
    if (btnEvent && btnEvent.currentTarget) {
        btnEvent.currentTarget.classList.add("active");
    }
    const targetPane = document.getElementById(`tab-${tabName}`);
    if (targetPane) {
        targetPane.classList.add("active");
    }
}

async function fetchGitHubData() {
    try {
        // Profil Dataları (Ruaaln)
        const userRes = await fetch("https://api.github.com/users/Ruaaln");
        if (userRes.ok) {
            const user = await userRes.json();
            document.getElementById("ghAvatar").src = user.avatar_url;
            document.getElementById("ghName").textContent = user.name || user.login;
            document.getElementById("ghBio").textContent = user.bio || "Developer";
            document.getElementById("ghFollowers").textContent = `Followers: ${user.followers}`;
        }

        // Repo Dataları (pc-controller)
        const repoRes = await fetch("https://api.github.com/repos/Ruaaln/pc-controller");
        if (repoRes.ok) {
            const repo = await repoRes.json();
            document.getElementById("repoName").textContent = repo.name;
            document.getElementById("repoDesc").textContent = repo.description || "PC Control Application";
            document.getElementById("repoStars").textContent = repo.stargazers_count;
            document.getElementById("repoForks").textContent = repo.forks_count;
        }
    } catch (err) {
        console.error("GitHub data fetch failed:", err);
    }
}

/* =========================================================
   API
========================================================= */
async function sendCommand(url, body = null) {
    try {
        const options = {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        };
        if (body) options.body = JSON.stringify(body);

        const res = await fetch(url, options);
        const data = await res.json().catch(() => ({}));

        if (!res.ok || data.error) {
            throw new Error(data.error || "Request failed");
        }

        await updateStatus();
        showToast("✓", "Done");
        return data;
    } catch (err) {
        console.error(err);
        showToast("!", err.message || "Xəta");
    }
}

/* =========================================================
   STATUS UPDATE
========================================================= */
async function updateStatus() {
    try {
        const res = await fetch("/api/status", { cache: "no-store" });
        if (!res.ok) throw new Error("Status failed");
        const data = await res.json();

        // CPU
        const cpu = Number(data.cpu) || 0;
        cpuEl.textContent = `${Math.round(cpu)}%`;
        cpuBar.style.width = `${Math.min(cpu, 100)}%`;

        // RAM
        const ram = Number(data.ram) || 0;
        ramEl.textContent = `${Math.round(ram)}%`;
        ramBar.style.width = `${Math.min(ram, 100)}%`;

        // Volume
        const vol = Number(data.volume) || 0;
        if (volumeBar) {
            if (window.matchMedia("(min-width: 521px)").matches) {
                volumeBar.style.height = `${Math.min(vol, 100)}%`;
                volumeBar.style.width = "100%";
            } else {
                volumeBar.style.width = `${Math.min(vol, 100)}%`;
                volumeBar.style.height = "100%";
            }
        }

        // Brightness
        const bri = Number(data.brightness) || 0;
        if (brightnessBar) {
            if (window.matchMedia("(min-width: 521px)").matches) {
                brightnessBar.style.height = `${Math.min(bri, 100)}%`;
                brightnessBar.style.width = "100%";
            } else {
                brightnessBar.style.width = `${Math.min(bri, 100)}%`;
                brightnessBar.style.height = "100%";
            }
        }

        // Media / Spotify
        if (data.media) {
            trackTitle.textContent = data.media.title || "No media";
            trackArtist.textContent = data.media.artist || "Offline";

            if (data.media.cover && data.media.cover !== lastCover) {
                lastCover = data.media.cover;
                coverImg.src = data.media.cover;
                coverImg.classList.add("show");
                coverFallback.style.display = "none";
            } else if (!data.media.cover) {
                lastCover = null;
                coverImg.classList.remove("show");
                coverImg.removeAttribute("src");
                coverFallback.style.display = "block";
            }

            playBtn.textContent = data.media.is_playing ? "| |" : "▶";
        }
    } catch (err) {
        console.error("Status error:", err);
    }
}

/* =========================================================
   POWER MODAL
========================================================= */
function confirmPower(action) {
    pendingPowerAction = action;
    const map = {
        shutdown: { title: "Kompüteri söndürmək?", text: "Kompüter tamamilə söndürüləcək." },
        restart: { title: "Restart etmək?", text: "Kompüter yenidən başladılacaq." },
        sleep: { title: "Sleep rejiminə keçsin?", text: "Kompüter yuxu rejiminə keçiriləcək." }
    };
    const cfg = map[action];
    if (!cfg) return;
    modalTitle.textContent = cfg.title;
    modalText.textContent = cfg.text;
    modal.classList.remove("hidden");
}

function closeModal() {
    modal.classList.add("hidden");
    pendingPowerAction = null;
}

cancelBtn.addEventListener("click", closeModal);

confirmBtn.addEventListener("click", async () => {
    if (!pendingPowerAction) return;
    const action = pendingPowerAction;
    closeModal();
    await sendCommand(`/api/system/${action}`);
});

modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
});

infoModal.addEventListener("click", (e) => {
    if (e.target === infoModal) closeInfoModal();
});

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        closeModal();
        closeInfoModal();
    }
});

/* =========================================================
   FULLSCREEN
========================================================= */
fullscreenBtn.addEventListener("click", async () => {
    try {
        if (!document.fullscreenElement) {
            await document.documentElement.requestFullscreen();
        } else {
            await document.exitFullscreen();
        }
    } catch (err) {
        showToast("!", "Fullscreen dəstəklənmir");
    }
});

document.addEventListener("fullscreenchange", () => {
    const ico = fullscreenBtn.querySelector(".ico");
    if (ico) {
        ico.textContent = document.fullscreenElement ? "✕" : "⛶";
    }
});

/* =========================================================
   TOAST & TOUCH
========================================================= */
function showToast(icon, message) {
    clearTimeout(toastTimer);
    toastIcon.textContent = icon;
    toastText.textContent = message;
    toast.classList.add("show");
    toastTimer = setTimeout(() => toast.classList.remove("show"), 1800);
}

let lastTouchEnd = 0;
document.addEventListener("touchend", (e) => {
    const now = Date.now();
    if (now - lastTouchEnd <= 300) e.preventDefault();
    lastTouchEnd = now;
}, { passive: false });

/* =========================================================
   START
========================================================= */
function init() {
    initTheme();
    renderAppsPanel();
    renderAppSelectionGrid();
    updateStatus();
    setInterval(updateStatus, 1500);
}

document.addEventListener("DOMContentLoaded", init);
document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") updateStatus();
});