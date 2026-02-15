/**
 * OnboardAI Dashboard — Application Logic
 * ═══════════════════════════════════════════
 * Fetches onboarding data from the MCP server REST API
 * and renders interactive employee cards with progress tracking.
 */

// ── Config ──────────────────────────────────────────────
const API_BASE = "http://localhost:8080";
const POLL_INTERVAL = 10000; // Refresh every 10s

// ── State ───────────────────────────────────────────────
let employees = [];
let pollTimer = null;

// ── Demo Data (when API is unavailable) ─────────────────
const DEMO_EMPLOYEES = [
    {
        id: "demo-001",
        name: "Sarah Chen",
        email: "sarah.chen@acme-corp.com",
        role: "Software Engineer",
        team: "Platform",
        start_date: new Date().toISOString().split("T")[0],
        progress_percent: 75,
        total_tasks: 14,
        completed_tasks: 10,
        tasks: [
            { id: "t1", name: "Send welcome DM", category: "slack", status: "completed", description: "Personalized Slack welcome" },
            { id: "t2", name: "Add to team channels", category: "slack", status: "completed", description: "Add to #engineering, #standup" },
            { id: "t3", name: "Post intro in #general", category: "slack", status: "completed", description: "Team introduction post" },
            { id: "t4", name: "Share company handbook", category: "gdrive", status: "completed", description: "Share docs & handbook" },
            { id: "t5", name: "Create personal folder", category: "gdrive", status: "completed", description: "Personal onboarding folder" },
            { id: "t6", name: "Invite to GitHub org", category: "github", status: "completed", description: "Add to acme-corp GitHub" },
            { id: "t7", name: "Grant repo access", category: "github", status: "completed", description: "Access to main-app, api-service" },
            { id: "t8", name: "Create setup issue", category: "github", status: "completed", description: "Dev environment setup tracker" },
            { id: "t9", name: "Share engineering docs", category: "gdrive", status: "completed", description: "Architecture & API docs" },
            { id: "t10", name: "Set up dev environment", category: "general", status: "completed", description: "Local dev setup" },
            { id: "t11", name: "Complete HR paperwork", category: "general", status: "pending", description: "Tax forms & agreements" },
            { id: "t12", name: "Set up 2FA", category: "general", status: "pending", description: "Enable 2FA on all accounts" },
            { id: "t13", name: "Complete security training", category: "general", status: "in_progress", description: "Engineering security module" },
            { id: "t14", name: "Meet with manager", category: "general", status: "pending", description: "Intro 1:1 with manager" },
        ],
    },
    {
        id: "demo-002",
        name: "Alex Rivera",
        email: "alex.r@acme-corp.com",
        role: "Product Designer",
        team: "Design",
        start_date: new Date().toISOString().split("T")[0],
        progress_percent: 42,
        total_tasks: 12,
        completed_tasks: 5,
        tasks: [
            { id: "t1", name: "Send welcome DM", category: "slack", status: "completed", description: "Personalized Slack welcome" },
            { id: "t2", name: "Add to team channels", category: "slack", status: "completed", description: "Add to #design, #design-reviews" },
            { id: "t3", name: "Post intro in #general", category: "slack", status: "completed", description: "Team introduction post" },
            { id: "t4", name: "Share company handbook", category: "gdrive", status: "completed", description: "Share docs & handbook" },
            { id: "t5", name: "Share brand guidelines", category: "gdrive", status: "completed", description: "Brand & design system" },
            { id: "t6", name: "Set up Figma access", category: "general", status: "in_progress", description: "Figma workspace access" },
            { id: "t7", name: "Review design system", category: "general", status: "pending", description: "Component library walkthrough" },
            { id: "t8", name: "Create personal folder", category: "gdrive", status: "pending", description: "Personal onboarding folder" },
            { id: "t9", name: "Complete HR paperwork", category: "general", status: "pending", description: "Tax forms & agreements" },
            { id: "t10", name: "Set up 2FA", category: "general", status: "pending", description: "Enable 2FA on all accounts" },
            { id: "t11", name: "Meet with manager", category: "general", status: "pending", description: "Intro 1:1 with manager" },
            { id: "t12", name: "Meet with design lead", category: "general", status: "pending", description: "Design team intro session" },
        ],
    },
    {
        id: "demo-003",
        name: "Jordan Patel",
        email: "jordan.p@acme-corp.com",
        role: "DevOps Engineer",
        team: "Infrastructure",
        start_date: new Date(Date.now() - 86400000 * 3).toISOString().split("T")[0],
        progress_percent: 100,
        total_tasks: 14,
        completed_tasks: 14,
        tasks: [
            { id: "t1", name: "Send welcome DM", category: "slack", status: "completed", description: "Personalized Slack welcome" },
            { id: "t2", name: "Add to team channels", category: "slack", status: "completed", description: "Added to channels" },
            { id: "t3", name: "Post intro in #general", category: "slack", status: "completed", description: "Team introduction" },
            { id: "t4", name: "Share company handbook", category: "gdrive", status: "completed", description: "Docs shared" },
            { id: "t5", name: "Create personal folder", category: "gdrive", status: "completed", description: "Folder created" },
            { id: "t6", name: "Invite to GitHub org", category: "github", status: "completed", description: "GitHub org invite" },
            { id: "t7", name: "Grant repo access", category: "github", status: "completed", description: "Repo access granted" },
            { id: "t8", name: "Create setup issue", category: "github", status: "completed", description: "Setup issue created" },
            { id: "t9", name: "Share engineering docs", category: "gdrive", status: "completed", description: "Engineering docs shared" },
            { id: "t10", name: "Set up dev environment", category: "general", status: "completed", description: "Local dev setup" },
            { id: "t11", name: "Complete HR paperwork", category: "general", status: "completed", description: "All forms completed" },
            { id: "t12", name: "Set up 2FA", category: "general", status: "completed", description: "2FA enabled" },
            { id: "t13", name: "Complete security training", category: "general", status: "completed", description: "Training complete" },
            { id: "t14", name: "Meet with manager", category: "general", status: "completed", description: "Intro 1:1 done" },
        ],
    },
];

// ── Color util ──────────────────────────────────────────
function stringToColor(str) {
    const colors = [
        "#6C5CE7", "#00B894", "#E17055", "#74B9FF",
        "#FD79A8", "#FDCB6E", "#A29BFE", "#55EFC4",
        "#FF7675", "#0984E3", "#E84393", "#00CEC9",
    ];
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
}

function getInitials(name) {
    return name
        .split(" ")
        .map((w) => w[0])
        .join("")
        .toUpperCase()
        .slice(0, 2);
}

function getStatusIcon(status) {
    switch (status) {
        case "completed": return "✓";
        case "in_progress": return "⟳";
        case "failed": return "✗";
        default: return "○";
    }
}

// ── SVG Progress Gradient (shared) ──────────────────────
const SVG_DEFS = `
<svg width="0" height="0" style="position:absolute">
    <defs>
        <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#6C5CE7"/>
            <stop offset="100%" stop-color="#a29bfe"/>
        </linearGradient>
        <linearGradient id="progressGradientGreen" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#00B894"/>
            <stop offset="100%" stop-color="#55efc4"/>
        </linearGradient>
    </defs>
</svg>`;

document.body.insertAdjacentHTML("afterbegin", SVG_DEFS);

// ── API ─────────────────────────────────────────────────
async function fetchEmployees() {
    try {
        const resp = await fetch(`${API_BASE}/api/employees`);
        if (!resp.ok) throw new Error("API error");
        const data = await resp.json();
        return data.employees || [];
    } catch {
        // Fallback to demo data
        return null;
    }
}

async function fetchEmployeeStatus(id) {
    try {
        const resp = await fetch(`${API_BASE}/api/employees/${id}`);
        if (!resp.ok) throw new Error("API error");
        return await resp.json();
    } catch {
        return null;
    }
}

async function submitOnboarding(formData) {
    try {
        const resp = await fetch(`${API_BASE}/api/onboard`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData),
        });
        if (!resp.ok) throw new Error("API error");
        return await resp.json();
    } catch {
        // Demo mode: add to demo list
        const demoEmp = {
            id: `demo-${Date.now()}`,
            ...formData,
            start_date: new Date().toISOString().split("T")[0],
            progress_percent: 0,
            total_tasks: 12,
            completed_tasks: 0,
            tasks: [
                { id: "t1", name: "Send welcome DM", category: "slack", status: "in_progress", description: "Sending..." },
                { id: "t2", name: "Add to team channels", category: "slack", status: "pending", description: "Pending" },
                { id: "t3", name: "Post intro in #general", category: "slack", status: "pending", description: "Pending" },
                { id: "t4", name: "Share company handbook", category: "gdrive", status: "pending", description: "Pending" },
                { id: "t5", name: "Create personal folder", category: "gdrive", status: "pending", description: "Pending" },
                { id: "t6", name: "Complete HR paperwork", category: "general", status: "pending", description: "Pending" },
                { id: "t7", name: "Set up 2FA", category: "general", status: "pending", description: "Pending" },
                { id: "t8", name: "Meet with manager", category: "general", status: "pending", description: "Pending" },
            ],
        };
        DEMO_EMPLOYEES.unshift(demoEmp);

        // Simulate progressive onboarding
        simulateOnboarding(demoEmp);

        return { employee_id: demoEmp.id, success: true, demo: true };
    }
}

function simulateOnboarding(emp) {
    let idx = 0;
    const timer = setInterval(() => {
        if (idx >= emp.tasks.length) {
            clearInterval(timer);
            return;
        }
        emp.tasks[idx].status = "completed";
        emp.completed_tasks++;
        emp.progress_percent = Math.round((emp.completed_tasks / emp.tasks.length) * 100);
        idx++;
        if (idx < emp.tasks.length) {
            emp.tasks[idx].status = "in_progress";
        }
        render(employees.length > 0 ? employees : DEMO_EMPLOYEES);
    }, 1500);
}

// ── Render ───────────────────────────────────────────────
function render(data) {
    const grid = document.getElementById("employeeGrid");
    const emptyState = document.getElementById("emptyState");

    if (!data || data.length === 0) {
        grid.innerHTML = "";
        emptyState.classList.add("visible");
        updateStats([]);
        return;
    }

    emptyState.classList.remove("visible");
    updateStats(data);

    grid.innerHTML = data
        .map((emp, i) => renderCard(emp, i))
        .join("");

    // Attach toggle listeners
    document.querySelectorAll(".tasks-toggle").forEach((btn) => {
        btn.addEventListener("click", () => {
            btn.classList.toggle("open");
            btn.nextElementSibling.classList.toggle("open");
        });
    });
}

function renderCard(emp, index) {
    const color = stringToColor(emp.name);
    const initials = getInitials(emp.name);
    const circumference = 2 * Math.PI * 22;
    const offset = circumference - (emp.progress_percent / 100) * circumference;
    const gradientId = emp.progress_percent === 100 ? "progressGradientGreen" : "progressGradient";
    const statusBadge = emp.progress_percent === 100
        ? `<span style="color:var(--accent-green);font-size:0.75rem;font-weight:600">✓ Complete</span>`
        : `<span style="color:var(--text-muted);font-size:0.75rem">${emp.start_date}</span>`;

    const tasksHtml = (emp.tasks || [])
        .map(
            (t) => `
        <li class="task-item">
            <span class="task-icon ${t.status}">${getStatusIcon(t.status)}</span>
            <span class="task-name ${t.status}">${t.name}</span>
            <span class="task-category ${t.category}">${t.category}</span>
        </li>`
        )
        .join("");

    return `
    <div class="employee-card" style="animation-delay:${index * 0.08}s">
        <div class="card-header">
            <div class="card-avatar" style="background:${color}">
                ${initials}
            </div>
            <div class="card-info">
                <div class="card-name">${emp.name}</div>
                <div class="card-role">${emp.role}</div>
                <span class="card-team">${emp.team}</span>
            </div>
            ${statusBadge}
        </div>
        <div class="card-progress">
            <div class="progress-ring-container">
                <svg class="progress-ring" width="56" height="56" viewBox="0 0 56 56">
                    <circle class="progress-ring-bg" cx="28" cy="28" r="22"/>
                    <circle class="progress-ring-fill"
                        cx="28" cy="28" r="22"
                        stroke="url(#${gradientId})"
                        stroke-dasharray="${circumference}"
                        stroke-dashoffset="${offset}"/>
                </svg>
                <span class="progress-percent">${Math.round(emp.progress_percent)}%</span>
            </div>
            <div class="progress-details">
                <div class="progress-text">${emp.completed_tasks} of ${emp.total_tasks} tasks</div>
                <div class="progress-bar">
                    <div class="progress-bar-fill" style="width:${emp.progress_percent}%"></div>
                </div>
            </div>
        </div>
        <div class="card-tasks">
            <button class="tasks-toggle">
                <svg class="tasks-toggle-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"/>
                </svg>
                View Checklist (${emp.tasks ? emp.tasks.length : 0} tasks)
            </button>
            <ul class="task-list">
                ${tasksHtml}
            </ul>
        </div>
    </div>`;
}

function updateStats(data) {
    const total = data.length;
    const complete = data.filter((e) => e.progress_percent === 100).length;
    const inProgress = data.filter(
        (e) => e.progress_percent > 0 && e.progress_percent < 100
    ).length;
    const pending = data.filter((e) => e.progress_percent === 0).length;

    animateValue("statTotal", total);
    animateValue("statComplete", complete);
    animateValue("statInProgress", inProgress);
    animateValue("statPending", pending);
}

function animateValue(id, target) {
    const el = document.getElementById(id);
    const current = parseInt(el.textContent) || 0;
    if (current === target) return;
    el.textContent = target;
    el.style.transform = "scale(1.15)";
    el.style.transition = "transform 0.2s ease";
    setTimeout(() => (el.style.transform = "scale(1)"), 200);
}

// ── Toast ───────────────────────────────────────────────
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    const icons = {
        success: "✓",
        error: "✗",
        info: "ℹ",
    };

    toast.innerHTML = `<span>${icons[type] || "ℹ"}</span> ${message}`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("toast-leaving");
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ── Modal ───────────────────────────────────────────────
const modalOverlay = document.getElementById("modalOverlay");
const newHireBtn = document.getElementById("newHireBtn");
const modalClose = document.getElementById("modalClose");
const cancelBtn = document.getElementById("cancelBtn");
const onboardForm = document.getElementById("onboardForm");
const refreshBtn = document.getElementById("refreshBtn");

function openModal() {
    modalOverlay.classList.add("active");
    document.getElementById("hireName").focus();
}

function closeModal() {
    modalOverlay.classList.remove("active");
    onboardForm.reset();
}

newHireBtn.addEventListener("click", openModal);
modalClose.addEventListener("click", closeModal);
cancelBtn.addEventListener("click", closeModal);
modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) closeModal();
});

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
});

onboardForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = {
        name: document.getElementById("hireName").value.trim(),
        email: document.getElementById("hireEmail").value.trim(),
        role: document.getElementById("hireRole").value,
        team: document.getElementById("hireTeam").value.trim(),
    };

    const github = document.getElementById("hireGithub").value.trim();
    if (github) formData.github_username = github;

    closeModal();
    showToast(`🚀 Starting onboarding for ${formData.name}...`, "info");

    const result = await submitOnboarding(formData);

    if (result) {
        showToast(`✅ ${formData.name} is being onboarded!`, "success");
        await refreshData();
    } else {
        showToast(`❌ Failed to start onboarding`, "error");
    }
});

// ── Refresh ─────────────────────────────────────────────
refreshBtn.addEventListener("click", async () => {
    refreshBtn.style.transform = "rotate(360deg)";
    refreshBtn.style.transition = "transform 0.5s ease";
    setTimeout(() => {
        refreshBtn.style.transform = "";
        refreshBtn.style.transition = "";
    }, 500);
    await refreshData();
    showToast("Data refreshed", "info");
});

async function refreshData() {
    const data = await fetchEmployees();
    if (data && data.length > 0) {
        employees = data;
        // Fetch detailed status for each
        const detailed = await Promise.all(
            data.map(async (emp) => {
                const status = await fetchEmployeeStatus(emp.id);
                return status && status.tasks ? { ...emp, tasks: status.tasks } : emp;
            })
        );
        render(detailed);
    } else {
        // Use demo data
        employees = [];
        render(DEMO_EMPLOYEES);
    }
}

// ── Poll ────────────────────────────────────────────────
function startPolling() {
    pollTimer = setInterval(refreshData, POLL_INTERVAL);
}

// ── Init ────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
    await refreshData();
    startPolling();
});
