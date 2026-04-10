// game.js – Client

const BLOCK = 18;
const GRID  = 30;
const W     = GRID * BLOCK;
const H     = GRID * BLOCK;

const canvas = document.getElementById("canvas");
const ctx    = canvas.getContext("2d");
ctx.fillStyle = "#000";
ctx.fillRect(0, 0, W, H);

let myPid = null;

// Local state: pid → { body:[[x,y],...], color, name, length }
// Completely overwritten every tick → no pixel bug possible
const snakes = {};

// ── Name screen ───────────────────────────────────────────
document.getElementById("name-input").addEventListener("keydown", e => {
    if (e.key === "Enter") submitName();
});
document.getElementById("name-btn").addEventListener("click", submitName);

function submitName() {
    const n = document.getElementById("name-input").value.trim().slice(0,15);
    if (!n) { document.getElementById("name-error").textContent = "Please enter a name."; return; }
    document.getElementById("name-screen").style.display = "none";
    document.getElementById("game-screen").style.display = "flex";
    connectWS(n);
}

// ── WebSocket ─────────────────────────────────────────────
let ws = null;

function connectWS(name) {
    ws = new WebSocket(`ws://${location.hostname}:${WS_PORT}`);
    ws.onopen  = () => {
        ws.send(JSON.stringify({ type: "join", name }));
        document.getElementById("waiting").textContent = "";
    };
    ws.onerror = () => {
        document.getElementById("waiting").textContent = "Connection error.";
    };
    ws.onclose = () => {
        document.getElementById("hud-players").textContent = "Disconnected – reload page";
    };
    ws.onmessage = e => handle(JSON.parse(e.data));
}

// ── Input ─────────────────────────────────────────────────
const DIRS = {
    ArrowUp:{x:0,y:-1}, ArrowDown:{x:0,y:1},
    ArrowLeft:{x:-1,y:0}, ArrowRight:{x:1,y:0},
    w:{x:0,y:-1}, s:{x:0,y:1}, a:{x:-1,y:0}, d:{x:1,y:0},
    W:{x:0,y:-1}, S:{x:0,y:1}, A:{x:-1,y:0}, D:{x:1,y:0},
};
document.addEventListener("keydown", e => {
    const d = DIRS[e.key];
    if (!d || !ws || ws.readyState !== WebSocket.OPEN) return;
    e.preventDefault();
    ws.send(JSON.stringify({ type:"dir", dir:d }));
});

// ── Messages ──────────────────────────────────────────────
function handle(msg) {
    switch (msg.type) {

        case "welcome":
            myPid = msg.pid;
            document.getElementById("waiting").textContent = "";
            break;

        // "S" = full state tick
        case "S":
            applyState(msg);
            render();
            updateHud(msg.a, msg.t);
            // Remove dead players from local state
            for (const pid of (msg.dead || [])) {
                delete snakes[String(pid)];
            }
            break;

        case "round_over":
            showLeaderboard(msg);
            break;

        case "countdown": {
            const s = Math.round(msg.seconds);
            const el = document.getElementById("msg");
            el.style.color = "#aaa";
            el.textContent = s > 0 ? `Next round in ${s}...` : "";
            break;
        }

        case "round_start":
            hideLeaderboard();
            document.getElementById("msg").textContent = "";
            // Clear canvas – new state packet arrives immediately after
            ctx.fillStyle = "#000";
            ctx.fillRect(0, 0, W, H);
            // Clear local state
            for (const k of Object.keys(snakes)) delete snakes[k];
            break;
    }
}

// ── Apply state ───────────────────────────────────────────
function applyState(msg) {
    // Remove players no longer in state
    for (const k of Object.keys(snakes)) {
        if (!(k in msg.s)) delete snakes[k];
    }
    // Apply state – reconstruct body from flat array
    for (const [pidStr, info] of Object.entries(msg.s)) {
        const flat = info.b;
        const body = [];
        for (let i = 0; i < flat.length; i += 2)
            body.push([flat[i], flat[i+1]]);
        snakes[pidStr] = {
            body,
            color:  info.c,
            name:   info.n,
            length: info.l,
        };
    }
}

// ── Render – full redraw every frame ──────────────────────
function render() {
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, W, H);
    for (const [pidStr, s] of Object.entries(snakes)) {
        ctx.fillStyle = s.color;
        for (const [x, y] of s.body)
            ctx.fillRect(x * BLOCK, y * BLOCK, BLOCK, BLOCK);
    }
}

// ── HUD ───────────────────────────────────────────────────
function updateHud(alive, total) {
    document.getElementById("hud-players").textContent =
        `Players: ${alive}/${total}`;
    const parts = [];
    for (const [pidStr, s] of Object.entries(snakes)) {
        const isMe = parseInt(pidStr) === myPid;
        parts.push(
            `<span style="color:${s.color}">● ${isMe ? s.name+" (you)" : s.name} [${s.length}]</span>`
        );
    }
    document.getElementById("hud-scores").innerHTML = parts.join("  ");
}

// ── Leaderboard ───────────────────────────────────────────
function showLeaderboard(msg) {
    const lb    = document.getElementById("leaderboard");
    const title = document.getElementById("lb-title");
    const tbody = document.getElementById("lb-body");

    if (msg.winner_name) {
        title.textContent = `${msg.winner_name} wins!`;
        title.style.color = msg.winner_color ?? "#fff";
    } else {
        title.textContent = "Draw!";
        title.style.color = "#aaa";
    }

    tbody.innerHTML = "";
    (msg.leaderboard || []).forEach((e, i) => {
        const tr = document.createElement("tr");
        const isMe = e.pid === myPid;
        tr.innerHTML = `
            <td style="color:#555">${i+1}.</td>
            <td style="color:${e.color}">${e.name}${isMe ? " ←" : ""}</td>
            <td style="color:#fff;text-align:right">${e.wins}</td>`;
        tbody.appendChild(tr);
    });

    lb.style.display = "block";
    document.getElementById("msg").textContent = "";
}

function hideLeaderboard() {
    document.getElementById("leaderboard").style.display = "none";
}