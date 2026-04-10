# OpenTron

Local multiplayer Snake/Tron in the browser. Up to 6 players on the same network.

---

## Requirements

- [Python 3.10+](https://www.python.org/downloads/) – make sure to check **"Add Python to PATH"** during installation

---

## Getting Started

**Double-click `start.bat`**

The script installs all dependencies and starts the server automatically.  
A link will appear in the console, e.g.:

```
► http://192.168.1.42:8080
```

Share this link with your friends – open it in any browser and you're in.

---

## Rules

- Every player starts with **5 segments**
- Snakes grow by 1 every **0.5 seconds**
- You die if you hit a **wall**, your **own tail**, or **another snake**
- Last one alive wins the round
- A **leaderboard** shows round wins after each match

## Controls

| Key | Action |
|-----|--------|
| `↑ ↓ ← →` | Move |
| `W A S D` | Move (alternative) |