#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║   YURXZ Rejoin Bot  —  bot.py                          ║
║   Discord Bot dengan Button UI                         ║
║   Jalan di Termux bersamaan dengan main.py             ║
╚══════════════════════════════════════════════════════════╝

Setup:
1. Buat bot di https://discord.com/developers/applications
2. Copy TOKEN bot
3. Enable: MESSAGE CONTENT INTENT + SERVER MEMBERS INTENT
4. Invite bot ke server dengan permission: Send Messages,
   Embed Links, Attach Files, Read Message History
5. Isi BOT_TOKEN dan CHANNEL_ID di config.json atau saat setup
"""

import os, sys, json, time, subprocess, threading, re
from pathlib import Path

# ── Path ────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
LOG_FILE    = BASE_DIR / "activity.log"
STATUS_FILE = BASE_DIR / "status.json"
PID_FILE    = BASE_DIR / "rejoin.pid"
BOT_CFG     = BASE_DIR / "bot_config.json"

# ── Warna terminal ─────────────────────────────────────
R  = "\033[0m"; CY = "\033[96m"; GR = "\033[92m"
YE = "\033[93m"; RE = "\033[91m"; MG = "\033[95m"
GY = "\033[90m"; WH = "\033[97m"

# ═══════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════
def load_bot_cfg():
    if BOT_CFG.exists():
        try:
            with open(BOT_CFG) as f:
                return json.load(f)
        except:
            pass
    return {"token": "", "channel_id": "", "owner_ids": []}

def save_bot_cfg(cfg):
    with open(BOT_CFG, "w") as f:
        json.dump(cfg, f, indent=2)

def load_main_cfg():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}

def load_status():
    if STATUS_FILE.exists():
        try:
            with open(STATUS_FILE) as f:
                return json.load(f)
        except:
            pass
    return []

def is_rejoin_running():
    """Cek apakah main.py sedang jalan."""
    try:
        result = subprocess.run(
            ["su", "-c", "pgrep -f main.py"],
            capture_output=True, text=True
        )
        return bool(result.stdout.strip())
    except:
        return False

def get_last_log(n=15):
    """Ambil N baris terakhir dari log."""
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE) as f:
                lines = f.readlines()
            return "".join(lines[-n:]).strip() or "(log kosong)"
        except:
            pass
    return "(log tidak ditemukan)"

def take_screenshot():
    """Ambil screenshot via root."""
    tmp = "/data/local/tmp/yurxz_bot_ss.png"
    local = str(BASE_DIR / "bot_ss.png")
    try:
        r1 = subprocess.run(
            ["su", "-c", f"screencap -p {tmp} && cp {tmp} {local} && chmod 666 {local}"],
            capture_output=True, timeout=10
        )
        if r1.returncode == 0 and os.path.exists(local):
            return local
    except:
        pass
    return None

# PID file untuk tools (start.sh)
TOOLS_PID_FILE = BASE_DIR / "tools.pid"

def run_tools():
    """
    Tombol 1: Jalankan bash start.sh di background.
    Tools jalan sendiri, menu muncul di Termux.
    """
    start_sh = str(BASE_DIR / "start.sh")
    if not os.path.exists(start_sh):
        return False, "start.sh tidak ditemukan!"
    try:
        log_file = open(str(BASE_DIR / "tools.log"), "w")
        proc = subprocess.Popen(
            ["bash", start_sh],
            cwd=str(BASE_DIR),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
        with open(str(TOOLS_PID_FILE), "w") as f:
            f.write(str(proc.pid))
        time.sleep(2)
        return True, f"✅ Tools dijalankan! (PID: {proc.pid})\nMenu rejoin muncul di Termux."
    except Exception as e:
        return False, f"❌ Error: {e}"

def start_rejoin():
    """
    Tombol 2: Tunggu 20 detik lalu kirim input '1' ke tools
    supaya masuk menu Start Auto Rejoin.
    """
    if not is_rejoin_running() and not is_tools_running():
        return False, "Tools belum jalan! Tekan Run Tools dulu."
    if is_rejoin_running():
        return False, "Rejoin sudah jalan!"
    try:
        # Tunggu 20 detik supaya tools siap
        time.sleep(20)
        # Kirim input '1' ke stdin tools via tty
        # Cari tty dari proses tools
        pid = open(str(TOOLS_PID_FILE)).read().strip() if TOOLS_PID_FILE.exists() else ""
        if pid:
            result = subprocess.run(
                ["su", "-c", f"echo '1' > /proc/{pid}/fd/0 2>/dev/null || true"],
                capture_output=True, timeout=5
            )
        # Fallback: tulis ke semua tty yang ada tools
        subprocess.run(
            ["su", "-c", "for tty in $(ls /proc/$(pgrep -f main.py | head -1)/fd/ 2>/dev/null); do echo '1' > /proc/$(pgrep -f main.py | head -1)/fd/$tty 2>/dev/null; done; true"],
            capture_output=True, timeout=5
        )
        time.sleep(3)
        return True, "✅ Input '1' dikirim ke tools!\nRejoin seharusnya dimulai."
    except Exception as e:
        return False, f"❌ Error: {e}"

def is_tools_running():
    """Cek apakah start.sh / main.py sedang jalan."""
    try:
        r = subprocess.run(["su", "-c", "pgrep -f start.sh"], capture_output=True, text=True)
        if r.stdout.strip():
            return True
        r2 = subprocess.run(["su", "-c", "pgrep -f main.py"], capture_output=True, text=True)
        return bool(r2.stdout.strip())
    except:
        return False

def stop_tools():
    """
    Hentikan semua — tools + rejoin sekaligus.
    Kirim SIGINT dulu, lalu force kill kalau masih jalan.
    """
    if not is_tools_running() and not is_rejoin_running():
        return False, "Tools tidak sedang jalan!"
    try:
        # Stop rejoin dulu (SIGINT = Ctrl+C)
        subprocess.run(["su", "-c", "pkill -SIGINT -f main.py"],
                      capture_output=True, timeout=5)
        time.sleep(2)
        subprocess.run(["su", "-c", "pkill -SIGINT -f start.sh"],
                      capture_output=True, timeout=5)
        time.sleep(2)
        subprocess.run(["su", "-c", "pkill -f main.py"],
                      capture_output=True, timeout=5)
        subprocess.run(["su", "-c", "pkill -f start.sh"],
                      capture_output=True, timeout=5)
        time.sleep(1)
        if not is_tools_running() and not is_rejoin_running():
            return True, "✅ Tools + Rejoin dihentikan!"
        else:
            return False, "❌ Gagal stop sepenuhnya."
    except Exception as e:
        return False, f"❌ Error: {e}"

def stop_rejoin():
    """
    Tombol 3: Kirim SIGINT ke main.py — sama seperti Ctrl+C.
    Hanya stop rejoin, tools tetap jalan.
    """
    if not is_rejoin_running():
        return False, "Rejoin tidak sedang jalan!"
    try:
        # SIGINT = Ctrl+C
        subprocess.run(["su", "-c", "pkill -SIGINT -f main.py"],
                      capture_output=True, timeout=5)
        time.sleep(3)
        if is_rejoin_running():
            subprocess.run(["su", "-c", "pkill -f main.py"],
                          capture_output=True, timeout=5)
            time.sleep(2)
        if not is_rejoin_running():
            return True, "✅ Rejoin dihentikan! (Ctrl+C)"
        else:
            return False, "❌ Gagal stop."
    except Exception as e:
        return False, f"❌ Error: {e}"

def run_lua_script(script_text, pkg=None):
    """Inject script Lua ke executor."""
    cfg  = load_main_cfg()
    pkgs = [pkg] if pkg else cfg.get("packages", [])
    if not pkgs:
        return False, "Tidak ada package Roblox!"

    results = []
    for p in pkgs:
        base_data   = f"/data/data/{p}/files"
        base_sdcard = f"/sdcard/Android/data/{p}/files"
        escaped     = script_text.replace("'", "'\\''")

        # Scan folder executor
        injected = 0
        for base in [base_data, base_sdcard]:
            r, out = subprocess.run(
                ["su", "-c", f"ls '{base}' 2>/dev/null"],
                capture_output=True, text=True
            ).returncode, subprocess.run(
                ["su", "-c", f"ls '{base}' 2>/dev/null"],
                capture_output=True, text=True
            ).stdout

            for folder in out.split():
                for subpath in [
                    f"{base}/{folder}/autoexec/autoexec.lua",
                    f"{base}/{folder}/workspace/autoexec.lua",
                ]:
                    folder_path = "/".join(subpath.split("/")[:-1])
                    subprocess.run(
                        ["su", "-c", f"mkdir -p '{folder_path}' && printf '%s' '{escaped}' > '{subpath}' && chmod 666 '{subpath}'"],
                        capture_output=True, timeout=5
                    )
                    injected += 1

        results.append(f"{p}: {injected} path")

    return True, "\n".join(results)

# ═══════════════════════════════════════════════════════
#  DISCORD BOT — pakai requests (tanpa library berat)
# ═══════════════════════════════════════════════════════
try:
    import requests
except ImportError:
    print(f"{RE}Install requests dulu: pip install requests{R}")
    sys.exit(1)

DISCORD_API = "https://discord.com/api/v10"

class DiscordBot:
    def __init__(self, token, channel_id, owner_ids=None):
        self.token      = token
        self.channel_id = str(channel_id)
        self.owner_ids  = [str(x) for x in (owner_ids or [])]
        self.headers    = {
            "Authorization": f"Bot {token}",
            "Content-Type":  "application/json",
        }
        self.last_msg_id = None
        self.panel_msg_id = None  # ID pesan panel utama

    def api(self, method, endpoint, **kwargs):
        url = f"{DISCORD_API}{endpoint}"
        try:
            r = getattr(requests, method)(
                url, headers=self.headers, timeout=15, **kwargs
            )
            return r
        except Exception as e:
            print(f"{RE}API error: {e}{R}")
            return None

    def send_message(self, content="", embeds=None, components=None, file_path=None):
        """Kirim pesan ke channel."""
        payload = {}
        if content:    payload["content"]    = content
        if embeds:     payload["embeds"]     = embeds
        if components: payload["components"] = components

        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as f:
                r = requests.post(
                    f"{DISCORD_API}/channels/{self.channel_id}/messages",
                    headers={"Authorization": f"Bot {self.token}"},
                    data={"payload_json": json.dumps(payload)},
                    files={"file": ("screenshot.png", f, "image/png")},
                    timeout=20
                )
        else:
            r = self.api("post", f"/channels/{self.channel_id}/messages",
                        json=payload)
        if r and r.status_code in (200, 201):
            return r.json().get("id")
        return None

    def edit_message(self, msg_id, content="", embeds=None, components=None):
        """Edit pesan yang sudah ada."""
        payload = {}
        if content:    payload["content"]    = content
        if embeds:     payload["embeds"]     = embeds
        if components: payload["components"] = components
        self.api("patch", f"/channels/{self.channel_id}/messages/{msg_id}",
                json=payload)

    def respond_interaction(self, interaction_id, interaction_token,
                            content="", embeds=None, components=None,
                            ephemeral=False, file_path=None):
        """Respond ke button interaction."""
        flags   = 64 if ephemeral else 0
        payload = {
            "type": 4,
            "data": {"flags": flags}
        }
        if content:    payload["data"]["content"]    = content
        if embeds:     payload["data"]["embeds"]     = embeds
        if components: payload["data"]["components"] = components

        url = f"{DISCORD_API}/interactions/{interaction_id}/{interaction_token}/callback"
        try:
            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    requests.post(
                        url,
                        headers={"Authorization": f"Bot {self.token}"},
                        data={"payload_json": json.dumps(payload)},
                        files={"file": ("screenshot.png", f, "image/png")},
                        timeout=20
                    )
            else:
                requests.post(url, headers=self.headers,
                            json=payload, timeout=15)
        except Exception as e:
            print(f"{RE}Interaction respond error: {e}{R}")

    def get_gateway(self):
        """Ambil gateway URL."""
        r = self.api("get", "/gateway/bot")
        if r and r.status_code == 200:
            return r.json().get("url")
        return None

    def build_panel_embed(self):
        """Build embed panel utama."""
        cfg    = load_main_cfg()
        status = load_status()
        running = is_rejoin_running()

        # Status tiap package
        pkg_lines = []
        if status:
            for s in status:
                icon   = "🟢" if "Running" in s.get("status","") or "In-game" in s.get("status","") else "🔴"
                rejoin = s.get("rejoin", 0)
                pkg_lines.append(f"{icon} `{s.get('pkg','?')}` — {s.get('status','?')} (rejoin: {rejoin}x)")
        else:
            pkgs = cfg.get("packages", [])
            for p in pkgs:
                pkg_lines.append(f"⚪ `{p}` — (belum start)")

        pkg_text = "\n".join(pkg_lines) if pkg_lines else "Tidak ada package"

        color  = 0x2ecc71 if running else 0xe74c3c
        status_text = "🟢 **RUNNING**" if running else "🔴 **STOPPED**"

        embed = {
            "title": "🎮 YURXZ Rejoin v9 — Control Panel",
            "color": color,
            "fields": [
                {"name": "Status", "value": status_text, "inline": True},
                {"name": "PS Link", "value": f"`{cfg.get('global_ps_link','(belum diset)')[:50]}`", "inline": True},
                {"name": "Packages", "value": pkg_text, "inline": False},
            ],
            "footer": {"text": f"YURXZ Bot • {time.strftime('%d/%m/%Y %H:%M:%S')}"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        return embed

    def build_main_buttons(self):
        """Build button panel utama."""
        running = is_rejoin_running()
        tools   = is_tools_running()
        return [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "label": "🔧 Run Tools",
                        "style": 2,
                        "custom_id": "btn_run_tools",
                        "disabled": tools,
                    },
                    {
                        "type": 2,
                        "label": "🔴 Stop Tools",
                        "style": 4,
                        "custom_id": "btn_stop_tools",
                        "disabled": not tools,
                    },
                    {
                        "type": 2,
                        "label": "▶ Start Rejoin",
                        "style": 3,
                        "custom_id": "btn_start",
                        "disabled": running,
                    },
                    {
                        "type": 2,
                        "label": "⏹ Stop Rejoin",
                        "style": 4,
                        "custom_id": "btn_stop",
                        "disabled": not running,
                    },
                ]
            },
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "label": "📊 Status",
                        "style": 1,
                        "custom_id": "btn_status",
                    },
                    {
                        "type": 2,
                        "label": "⚙️ Config",
                        "style": 2,
                        "custom_id": "btn_config",
                    },
                    {
                        "type": 2,
                        "label": "📸 Screenshot",
                        "style": 2,
                        "custom_id": "btn_ss",
                    },
                    {
                        "type": 2,
                        "label": "📜 Log",
                        "style": 2,
                        "custom_id": "btn_log",
                    },
                    {
                        "type": 2,
                        "label": "🔄 Refresh",
                        "style": 2,
                        "custom_id": "btn_refresh",
                    },
                ]
            },
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "label": "💉 Run Script",
                        "style": 1,
                        "custom_id": "btn_script",
                    },
                ]
            }
        ]

    def send_panel(self):
        """Kirim panel kontrol ke channel."""
        embed      = self.build_panel_embed()
        components = self.build_main_buttons()
        msg_id     = self.send_message(embeds=[embed], components=components)
        if msg_id:
            self.panel_msg_id = msg_id
            print(f"{GR}[Bot] Panel dikirim ke channel!{R}")
        return msg_id

    def refresh_panel(self):
        """Update panel yang sudah ada."""
        if not self.panel_msg_id:
            self.send_panel()
            return
        embed      = self.build_panel_embed()
        components = self.build_main_buttons()
        self.edit_message(self.panel_msg_id, embeds=[embed],
                         components=components)

    def handle_interaction(self, data):
        """Handle button press."""
        interaction_id    = data.get("id")
        interaction_token = data.get("token")
        custom_id         = data.get("data", {}).get("custom_id", "")
        user_id           = data.get("member", {}).get("user", {}).get("id", "")

        # Cek owner
        if self.owner_ids and user_id not in self.owner_ids:
            self.respond_interaction(
                interaction_id, interaction_token,
                content="❌ Kamu tidak punya akses!", ephemeral=True
            )
            return

        print(f"{CY}[Bot] Button: {custom_id} dari user {user_id}{R}")

        if custom_id == "btn_run_tools":
            self.respond_interaction(
                interaction_id, interaction_token,
                content="🔧 Menjalankan tools...", ephemeral=True
            )
            ok, msg = run_tools()
            self.send_message(content=f"🔧 {msg}")
            time.sleep(2)
            self.refresh_panel()

        elif custom_id == "btn_stop_tools":
            self.respond_interaction(
                interaction_id, interaction_token,
                content="🔴 Menghentikan tools...", ephemeral=True
            )
            ok, msg = stop_tools()
            self.send_message(content=f"{'🔴' if ok else '❌'} {msg}")
            time.sleep(2)
            self.refresh_panel()

        elif custom_id == "btn_start":
            # Tombol 2: Start rejoin (tunggu 20 detik dulu)
            self.respond_interaction(
                interaction_id, interaction_token,
                content="⏳ Tunggu 20 detik lalu kirim input ke tools...",
                ephemeral=True
            )
            # Jalankan di thread supaya tidak block
            def do_start():
                ok, msg = start_rejoin()
                self.send_message(content=f"{'▶' if ok else '❌'} {msg}")
                time.sleep(2)
                self.refresh_panel()
            threading.Thread(target=do_start, daemon=True).start()

        elif custom_id == "btn_stop":
            ok, msg = stop_rejoin()
            icon = "✅" if ok else "❌"
            self.respond_interaction(
                interaction_id, interaction_token,
                content=f"{icon} {msg}", ephemeral=True
            )
            time.sleep(2)
            self.refresh_panel()

        elif custom_id == "btn_status":
            status = load_status()
            cfg    = load_main_cfg()
            running = is_rejoin_running()

            lines = [f"**Status:** {'🟢 Running' if running else '🔴 Stopped'}"]
            lines.append(f"**PS Link:** `{cfg.get('global_ps_link','(kosong)')[:60]}`")
            lines.append("")
            if status:
                for s in status:
                    icon = "🟢" if "Running" in s.get("status","") or "In-game" in s.get("status","") else "🔴"
                    lines.append(f"{icon} `{s.get('pkg','?')}`")
                    lines.append(f"   Status: {s.get('status','?')}")
                    lines.append(f"   Rejoin: {s.get('rejoin',0)}x")
            else:
                lines.append("Belum ada data status.")

            embed = {
                "title": "📊 Status Sekarang",
                "description": "\n".join(lines),
                "color": 0x3498db,
                "footer": {"text": time.strftime('%d/%m/%Y %H:%M:%S')},
            }
            self.respond_interaction(
                interaction_id, interaction_token,
                embeds=[embed], ephemeral=True
            )

        elif custom_id == "btn_config":
            cfg = load_main_cfg()
            pkgs     = cfg.get("packages", [])
            ps_link  = cfg.get("global_ps_link", "(kosong)")
            interval = cfg.get("check_interval", 35)
            delay    = cfg.get("restart_delay", 10)
            webhook  = cfg.get("webhook_url", "")
            floating = cfg.get("floating_window", True)
            mute     = cfg.get("auto_mute", True)
            lowgfx   = cfg.get("auto_low_graphics", True)
            auto_tap = cfg.get("auto_tap_splash", True)
            ae_delay = cfg.get("autoexec_delay", 30)
            ae_script= cfg.get("autoexec_script", "")

            on  = "✅ ON"
            off = "❌ OFF"

            lines = [
                f"**Packages ({len(pkgs)}):**",
            ]
            for p in pkgs:
                ps = cfg.get("ps_links", {}).get(p, ps_link)
                lines.append(f"  • `{p}`")
                lines.append(f"    PS: `{ps[:50]}`")
            lines += [
                "",
                f"**PS Link Global:** `{ps_link[:60]}`",
                f"**Check Interval:** {interval}s",
                f"**Restart Delay:** {delay}s",
                f"**Webhook:** {'Ada ✅' if webhook else 'Kosong ❌'}",
                "",
                f"**Floating Window:** {on if floating else off}",
                f"**Auto Mute:** {on if mute else off}",
                f"**Low Grafik:** {on if lowgfx else off}",
                f"**Auto Tap Splash:** {on if auto_tap else off}",
                "",
                f"**AutoExec Delay:** {ae_delay}s",
                f"**AutoExec Script:** {'Ada ✅' if ae_script else 'Kosong ❌'}",
            ]
            embed = {
                "title": "⚙️ Config Saat Ini",
                "description": "\n".join(lines),
                "color": 0x9b59b6,
                "footer": {"text": time.strftime('%d/%m/%Y %H:%M:%S')},
            }
            self.respond_interaction(
                interaction_id, interaction_token,
                embeds=[embed], ephemeral=True
            )
            self.respond_interaction(
                interaction_id, interaction_token,
                content="📸 Mengambil screenshot...", ephemeral=True
            )
            ss_path = take_screenshot()
            if ss_path:
                self.send_message(
                    content="📸 Screenshot sekarang:",
                    file_path=ss_path
                )
            else:
                self.send_message(content="❌ Gagal ambil screenshot (butuh root)")

        elif custom_id == "btn_log":
            log_text = get_last_log(20)
            embed = {
                "title": "📜 Log Aktivitas (20 baris terakhir)",
                "description": f"```\n{log_text[:3900]}\n```",
                "color": 0x95a5a6,
                "footer": {"text": time.strftime('%d/%m/%Y %H:%M:%S')},
            }
            self.respond_interaction(
                interaction_id, interaction_token,
                embeds=[embed], ephemeral=True
            )

        elif custom_id == "btn_script":
            self.respond_interaction(
                interaction_id, interaction_token,
                content=(
                    "💉 **Run Script Lua**\n"
                    "Kirim script Lua kamu sebagai pesan berikutnya di channel ini.\n"
                    "Format: `!script <kode lua>`\n"
                    "Contoh: `!script print('hello')`"
                ),
                ephemeral=True
            )

        elif custom_id == "btn_refresh":
            self.respond_interaction(
                interaction_id, interaction_token,
                content="🔄 Refreshing panel...", ephemeral=True
            )
            self.refresh_panel()

    def handle_message(self, data):
        """Handle pesan !script."""
        content   = data.get("content", "")
        author_id = data.get("author", {}).get("id", "")

        if self.owner_ids and author_id not in self.owner_ids:
            return

        if content.startswith("!script "):
            script_text = content[8:].strip()
            if script_text:
                ok, msg = run_lua_script(script_text)
                icon = "✅" if ok else "❌"
                self.send_message(content=f"💉 {icon} Inject script:\n```\n{msg}\n```")

        elif content == "!panel":
            self.send_panel()

        elif content == "!status":
            self.refresh_panel()

    def run_gateway(self):
        """Jalankan bot via Discord Gateway (WebSocket)."""
        try:
            import websocket
        except ImportError:
            print(f"{RE}Install websocket-client: pip install websocket-client{R}")
            sys.exit(1)

        import websocket as ws_lib

        gateway_url = self.get_gateway()
        if not gateway_url:
            print(f"{RE}Gagal ambil gateway URL!{R}")
            return

        gateway_url += "?v=10&encoding=json"
        heartbeat_interval = None
        sequence           = None
        session_id         = None

        def on_open(ws):
            print(f"{GR}[Bot] WebSocket terhubung!{R}")

        def on_message(ws, message):
            nonlocal heartbeat_interval, sequence, session_id
            try:
                data = json.loads(message)
                op   = data.get("op")
                d    = data.get("d", {})
                t    = data.get("t")
                s    = data.get("s")
                if s:
                    sequence = s

                # Op 10: Hello → kirim identify + start heartbeat
                if op == 10:
                    heartbeat_interval = d.get("heartbeat_interval", 41250) / 1000

                    # Identify
                    identify_payload = {
                        "op": 2,
                        "d": {
                            "token":      self.token,
                            "intents":    513,  # GUILDS + GUILD_MESSAGES
                            "properties": {
                                "os":      "android",
                                "browser": "yurxz-bot",
                                "device":  "yurxz-bot",
                            },
                        }
                    }
                    ws.send(json.dumps(identify_payload))

                    # Start heartbeat di thread terpisah
                    def heartbeat_loop():
                        while True:
                            time.sleep(heartbeat_interval)
                            try:
                                ws.send(json.dumps({"op": 1, "d": sequence}))
                            except:
                                break
                    threading.Thread(target=heartbeat_loop, daemon=True).start()

                # Op 0: Event
                elif op == 0:
                    if t == "READY":
                        session_id = d.get("session_id")
                        user = d.get("user", {})
                        print(f"{GR}[Bot] Login sebagai {user.get('username')}#{user.get('discriminator')}{R}")
                        # Kirim panel saat bot ready
                        threading.Thread(
                            target=self.send_panel, daemon=True
                        ).start()

                    elif t == "INTERACTION_CREATE":
                        if d.get("type") == 3:  # Component interaction (button)
                            threading.Thread(
                                target=self.handle_interaction,
                                args=(d,), daemon=True
                            ).start()

                    elif t == "MESSAGE_CREATE":
                        # Hanya proses pesan dari channel yang dikonfigurasi
                        if str(d.get("channel_id")) == self.channel_id:
                            # Abaikan pesan dari bot sendiri
                            if not d.get("author", {}).get("bot"):
                                threading.Thread(
                                    target=self.handle_message,
                                    args=(d,), daemon=True
                                ).start()

                # Op 11: Heartbeat ACK
                elif op == 11:
                    pass

            except Exception as e:
                print(f"{RE}[Bot] Error handle message: {e}{R}")

        def on_error(ws, error):
            print(f"{RE}[Bot] WebSocket error: {error}{R}")

        def on_close(ws, code, msg):
            print(f"{YE}[Bot] WebSocket closed: {code} {msg}{R}")
            print(f"{YE}[Bot] Reconnect dalam 10 detik...{R}")
            time.sleep(10)
            self.run_gateway()  # Reconnect

        ws_app = ws_lib.WebSocketApp(
            gateway_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        # Panel refresh loop di background
        def auto_refresh():
            while True:
                time.sleep(60)  # Refresh panel tiap 1 menit
                try:
                    self.refresh_panel()
                except:
                    pass
        threading.Thread(target=auto_refresh, daemon=True).start()

        ws_app.run_forever(ping_interval=30, ping_timeout=10)

# ═══════════════════════════════════════════════════════
#  SETUP INTERAKTIF
# ═══════════════════════════════════════════════════════
def setup_bot():
    """Setup bot pertama kali."""
    print(f"\n{CY}+{'='*45}+{R}")
    print(f"{MG}  YURXZ Bot Setup{R}")
    print(f"{CY}+{'='*45}+{R}\n")

    cfg = load_bot_cfg()

    print(f"{YE}Cara buat bot Discord:{R}")
    print(f"  1. Buka https://discord.com/developers/applications")
    print(f"  2. New Application -> beri nama")
    print(f"  3. Bot -> Add Bot -> Copy Token")
    print(f"  4. Bot -> Aktifkan MESSAGE CONTENT INTENT")
    print(f"  5. OAuth2 -> URL Generator -> centang bot")
    print(f"     Permissions: Send Messages, Embed Links, Attach Files")
    print(f"  6. Copy Generated URL -> invite bot ke server\n")

    token = input(f"{YE}Masukkan Bot Token: {R}").strip()
    if not token:
        print(f"{RE}Token kosong!{R}"); return

    channel_id = input(f"{YE}Masukkan Channel ID (klik kanan channel -> Copy ID): {R}").strip()
    if not channel_id:
        print(f"{RE}Channel ID kosong!{R}"); return

    owner_raw = input(f"{YE}Masukkan Owner ID kamu (klik kanan profil -> Copy ID): {R}").strip()
    owner_ids = [x.strip() for x in owner_raw.split(",") if x.strip()]

    cfg["token"]      = token
    cfg["channel_id"] = channel_id
    cfg["owner_ids"]  = owner_ids
    save_bot_cfg(cfg)

    print(f"\n{GR}✓ Config bot tersimpan!{R}")
    print(f"{CY}Jalankan bot: python3 bot.py{R}\n")

# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════
def main():
    print(f"\n{CY}+{'='*45}+{R}")
    print(f"{MG}  YURXZ Rejoin Bot  by YURXZ{R}")
    print(f"{CY}+{'='*45}+{R}\n")

    cfg = load_bot_cfg()

    # Cek apakah perlu setup
    if not cfg.get("token") or not cfg.get("channel_id"):
        print(f"{YE}Bot belum dikonfigurasi. Jalankan setup dulu.{R}")
        setup_bot()
        cfg = load_bot_cfg()
        if not cfg.get("token"):
            return

    print(f"{GY}Token   : {cfg['token'][:20]}...{R}")
    print(f"{GY}Channel : {cfg['channel_id']}{R}")
    print(f"{GY}Owners  : {cfg.get('owner_ids', [])}{R}\n")

    # Cek websocket-client
    try:
        import websocket
    except ImportError:
        print(f"{YE}Install websocket-client...{R}")
        os.system("pip install websocket-client -q")

    bot = DiscordBot(
        token      = cfg["token"],
        channel_id = cfg["channel_id"],
        owner_ids  = cfg.get("owner_ids", [])
    )

    print(f"{GR}[Bot] Connecting to Discord...{R}\n")
    try:
        bot.run_gateway()
    except KeyboardInterrupt:
        print(f"\n{YE}[Bot] Dihentikan.{R}\n")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_bot()
    else:
        main()
