"""
server.py – Einstiegspunkt

Installation: pip install websockets
Start:        python server.py
"""

import asyncio
import json
import socket as _socket
import websockets
import game
import http_server

WS_PORT   = 8765
HTTP_PORT = 8080

async def broadcast(obj: dict):
    if not game.sockets: return
    data = json.dumps(obj, separators=(",",":"))
    dead = []
    for pid, ws in list(game.sockets.items()):
        try:    await ws.send(data)
        except: dead.append(pid)
    for pid in dead:
        game.remove_player(pid)

async def send_to(pid: int, obj: dict):
    ws = game.sockets.get(pid)
    if ws:
        try: await ws.send(json.dumps(obj, separators=(",",":")))
        except: pass

async def ws_handler(ws):
    # Erstes Paket: Name
    try:
        raw  = await asyncio.wait_for(ws.recv(), timeout=10)
        msg  = json.loads(raw)
        name = str(msg.get("name","")).strip()[:15] or None
    except Exception:
        name = None

    p = game.add_player(name=name)
    game.sockets[p.pid] = ws
    print(f"[+] {p.name!r} verbunden  (gesamt: {len(game.sockets)})")

    # Willkommen an neuen Spieler
    await send_to(p.pid, {
        "type": "welcome", "pid": p.pid,
        "name": p.name, "color": p.color, "grid": game.GRID,
    })
    # Vollständiger State an alle (neuer Spieler erscheint auf allen Screens)
    await broadcast(game.build_state())

    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
                if msg.get("type") == "dir":
                    pl = game.players.get(p.pid)
                    if pl: pl.queue_dir(msg["dir"])
            except: pass
    except: pass
    finally:
        print(f"[-] {p.name!r} getrennt  (gesamt: {len(game.sockets)-1})")
        game.remove_player(p.pid)
        await broadcast(game.build_state())

async def main():
    game.set_broadcast(broadcast)

    try:
        s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "localhost"

    http_server.start(HTTP_PORT)

    print("═"*50)
    print("  TRON SNAKE")
    print(f"\n  ► http://{local_ip}:{HTTP_PORT}\n")
    print("  Im Browser öffnen – sofort spielen.")
    print("═"*50)

    async with websockets.serve(ws_handler, "0.0.0.0", WS_PORT):
        await asyncio.gather(game.tick_loop(), game.grow_loop())

if __name__ == "__main__":
    asyncio.run(main())