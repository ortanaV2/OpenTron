"""
game.py – Game logic
"""

import asyncio
import random

# ── Constants ──────────────────────────────────────────────
GRID        = 30
TICK_MS     = 130
GROW_EVERY  = 0.5
START_LEN   = 5
MIN_SPACING = 8
WALL_MARGIN = 4

COLORS = [
    "#ff0000", "#9842f5", "#00ff00",
    "#0064ff", "#ffff00", "#00ffff",
]

# ── Spawn ──────────────────────────────────────────────────
def _chebyshev(a, b):
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]))

def spawn_pos(occupied: set, heads: list) -> tuple:
    m = WALL_MARGIN
    candidates = [
        (x, y)
        for x in range(m, GRID - m)
        for y in range(m, GRID - m)
        if (x, y) not in occupied
        and all(_chebyshev((x,y), h) >= MIN_SPACING for h in heads)
    ]
    if candidates:
        return random.choice(candidates)
    fallback = [(x,y) for x in range(m, GRID-m) for y in range(m, GRID-m)
                if (x,y) not in occupied]
    return random.choice(fallback) if fallback else (m, m)

def _rand_dir():
    return random.choice([(1,0),(-1,0),(0,1),(0,-1)])

def _opposite(a, b):
    return a[0] == -b[0] and a[1] == -b[1]

# ── Player ─────────────────────────────────────────────────
_next_pid  = 0
_color_idx = 0

class Player:
    def __init__(self, pos, pid=None, color=None, name=None):
        global _next_pid, _color_idx
        self.pid   = _next_pid if pid is None else pid
        if pid is None: _next_pid += 1
        self.color = COLORS[_color_idx % len(COLORS)] if color is None else color
        if color is None: _color_idx += 1
        self.name       = (name or f"Player {self.pid+1}")[:15]
        d               = _rand_dir()
        self.dir        = d
        self.next_dir   = d
        self.body       = [(pos[0]-d[0]*i, pos[1]-d[1]*i) for i in range(START_LEN)]
        self.alive      = True
        self.target_len = START_LEN

    @property
    def head(self): return self.body[0]

    def queue_dir(self, d):
        d = (d["x"], d["y"])
        if not _opposite(d, self.dir):
            self.next_dir = d

    def step(self):
        if not self.alive: return
        self.dir = self.next_dir
        hx, hy = self.head
        self.body.insert(0, (hx + self.dir[0], hy + self.dir[1]))
        if len(self.body) > self.target_len:
            self.body.pop()

# ── State ──────────────────────────────────────────────────
players: dict[int, Player] = {}   # alive only
sockets: dict              = {}   # all connected pid→ws
_wins:   dict[int, int]    = {}
_names:  dict[int, str]    = {}
_colors: dict[int, str]    = {}
_round_over_task           = None

def add_player(name=None) -> Player:
    occupied = {c for p in players.values() for c in p.body}
    heads    = [p.head for p in players.values()]
    pos      = spawn_pos(occupied, heads)
    p        = Player(pos, name=name)
    players[p.pid] = p
    _wins[p.pid]   = 0
    _names[p.pid]  = p.name
    _colors[p.pid] = p.color
    return p

def remove_player(pid: int):
    players.pop(pid, None)
    sockets.pop(pid, None)
    _wins.pop(pid, None)
    _names.pop(pid, None)
    _colors.pop(pid, None)

def _leaderboard():
    return sorted(
        [{"pid": pid, "name": _names[pid], "color": _colors[pid], "wins": _wins.get(pid,0)}
         for pid in sockets],
        key=lambda x: -x["wins"]
    )

# ── Broadcast ──────────────────────────────────────────────
_broadcast_fn = None

def set_broadcast(fn):
    global _broadcast_fn
    _broadcast_fn = fn

async def _broadcast(obj):
    if _broadcast_fn:
        await _broadcast_fn(obj)

# ── State packet ───────────────────────────────────────────
def build_state() -> dict:
    """
    Compact full state every tick.
    Body as flat array [x0,y0, x1,y1, ...] instead of list of dicts.
    """
    snakes = {}
    for pid, p in players.items():
        flat = []
        for (x, y) in p.body:
            flat.append(x)
            flat.append(y)
        snakes[str(pid)] = {
            "b": flat,          # body (flat)
            "c": p.color,       # color
            "n": p.name,        # name
            "l": p.target_len,  # length
        }
    return {
        "type": "S",
        "s":    snakes,
        "a":    len(players),
        "t":    len(sockets),
    }

# ── Tick ───────────────────────────────────────────────────
async def game_tick():
    if not players: return

    for p in players.values():
        p.step()

    # Tail set
    tail_set = set()
    for p in players.values():
        for c in p.body[1:]:
            tail_set.add(c)

    # Wall + tail collisions
    for p in list(players.values()):
        if not p.alive: continue
        hx, hy = p.head
        if not (0 <= hx < GRID and 0 <= hy < GRID):
            p.alive = False
        elif p.head in tail_set:
            p.alive = False

    # Head-on-head collisions
    head_map = {}
    for p in players.values():
        if not p.alive: continue
        if p.head in head_map:
            p.alive = False
            head_map[p.head].alive = False
        else:
            head_map[p.head] = p

    # Remove dead players immediately
    dead_pids = [pid for pid, p in list(players.items()) if not p.alive]
    for pid in dead_pids:
        players.pop(pid)

    # Send state
    msg = build_state()
    if dead_pids:
        msg["dead"] = dead_pids
    await _broadcast(msg)

    await _check_round_over()

async def grow_tick():
    for p in players.values():
        p.target_len += 1

# ── Round management ───────────────────────────────────────
async def _check_round_over():
    global _round_over_task
    if _round_over_task: return
    alive = list(players.values())
    total = len(sockets)
    if total == 0: return
    over = (total == 1 and not alive) or (total > 1 and len(alive) <= 1)
    if not over: return

    winner = alive[0] if alive else None
    if winner:
        _wins[winner.pid] = _wins.get(winner.pid, 0) + 1

    await _broadcast({
        "type":         "round_over",
        "winner_name":  winner.name  if winner else None,
        "winner_color": winner.color if winner else None,
        "leaderboard":  _leaderboard(),
    })
    _round_over_task = asyncio.create_task(_countdown_and_reset())

async def _countdown_and_reset():
    global _round_over_task
    for s in range(4, 0, -1):
        await asyncio.sleep(1)
        await _broadcast({"type": "countdown", "seconds": s})
    await asyncio.sleep(1)

    players.clear()
    spawn_heads = []
    occupied    = set()
    for pid in list(sockets.keys()):
        pos = spawn_pos(occupied, spawn_heads)
        p   = Player(pos, pid=pid, color=_colors.get(pid), name=_names.get(pid))
        p.wins = _wins.get(pid, 0)
        players[pid] = p
        spawn_heads.append(pos)
        for c in p.body: occupied.add(c)

    await _broadcast({"type": "round_start"})
    await _broadcast(build_state())
    _round_over_task = None

# ── Loops ──────────────────────────────────────────────────
async def tick_loop():
    while True:
        await asyncio.sleep(TICK_MS / 1000)
        if players:
            await game_tick()

async def grow_loop():
    while True:
        await asyncio.sleep(GROW_EVERY)
        if players:
            await grow_tick()