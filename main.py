#!/usr/bin/env python3
"""
+==========================================================+
|          YURXZ Rejoin  v9  —  main.py                  |
|          Android Rooted + Termux  |  by YURXZ          |
+==========================================================+
|  Deteksi (tanpa cookie):                               |
|    Level 1 → dumpsys activity  (Activity name)         |
|    Level 2 → network check     (koneksi aktif)         |
|    Level 3 → CPU usage         (app aktif)             |
|    Level 4 → pidof             (fallback universal)    |
+==========================================================+
|  --auto      : langsung mulai tanpa menu               |
|  --preventif : cek tiap 20 detik                       |
|  --low       : hemat RAM/CPU                           |
+==========================================================+
"""

import os, sys, json, subprocess, time, math, re, argparse

# --- ARGS --------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--auto",      action="store_true")
parser.add_argument("--preventif", action="store_true")
parser.add_argument("--low",       action="store_true")
ARGS = parser.parse_args()

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
LOG_FILE    = os.path.join(BASE_DIR, "activity.log")
STATUS_FILE = os.path.join(BASE_DIR, "status.json")
CMD_FILE    = os.path.join(BASE_DIR, ".bot_cmd")   # File perintah dari bot

# --- WARNA -------------------------------------------------
R  = "\033[0m"
CY = "\033[96m"
GR = "\033[92m"
YE = "\033[93m"
RE = "\033[91m"
MG = "\033[95m"
GY = "\033[90m"
WH = "\033[97m"

# ==========================================================
#  HELPERS
# ==========================================================
def reset_terminal():
    """Reset terminal state supaya tidak rusak setelah keluar submenu."""
    try:
        os.system("stty sane 2>/dev/null")
    except:
        pass
    # Reset semua escape sequence
    sys.stdout.write("\033[0m\033[?7h")
    sys.stdout.flush()

def clear():
    reset_terminal()
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

def run_root(cmd, timeout=15):
    try:
        r = subprocess.run(["su", "-c", cmd],
                           capture_output=True, text=True, timeout=timeout)
        out = (r.stdout or "") + "\n" + (r.stderr or "")
        return r.returncode == 0, out.strip()
    except Exception as e:
        return False, str(e)

def log(msg, lvl="INFO"):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{time.strftime('%d/%m %H:%M:%S')}][{lvl}] {msg}\n")
    except:
        pass

def _open_tty():
    return None

def _read_input(tty_file, max_chars=2, timeout=60):
    return ""

def flush_stdin():
    """Buang sisa input di buffer."""
    try:
        import termios
        termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
    except:
        pass
    time.sleep(0.3)

def wait_enter(msg="  Tekan Enter untuk kembali ke menu"):
    """Tunggu Enter."""
    flush_stdin()
    try:
        sys.stdout.write(f"\n{GY}{msg}: {R}")
        sys.stdout.flush()
        sys.stdin.readline()
    except:
        time.sleep(3)

def inp(prompt, max_chars=2, timeout=60):
    """Input menu — flush stdin dulu."""
    flush_stdin()
    try:
        return input(prompt).strip()
    except EOFError:
        return ""
    except KeyboardInterrupt:
        raise
    """Input menu — flush dulu, lalu baca."""
    flush_stdin()
    sys.stdout.write(prompt)
    sys.stdout.flush()
    try:
        line = sys.stdin.readline()
        return line.strip() if line else ""
    except EOFError:
        return ""
    except KeyboardInterrupt:
        raise

def inp_text(prompt, timeout=120):
    """Input teks panjang."""
    flush_stdin()
    sys.stdout.write(prompt)
    sys.stdout.flush()
    try:
        line = sys.stdin.readline()
        return line.strip() if line else ""
    except EOFError:
        return ""
    except KeyboardInterrupt:
        raise

def pause_auto(detik=5):
    """Auto lanjut setelah beberapa detik."""
    for i in range(detik, 0, -1):
        sys.stdout.write(f"\r  \033[90mLanjut dalam {i}s...\033[0m  ")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r" + " "*40 + "\r\n")
    sys.stdout.flush()

def countdown_before_menu(label, detik=10):
    """
    Countdown sebelum masuk menu.
    Tekan Enter → langsung masuk.
    Otomatis masuk setelah 10 detik.
    """
    import select
    flush_stdin()
    print(f"\n  \033[90m>> \033[97m{label}\033[0m")
    print(f"  \033[90m[Enter = langsung masuk | tunggu {detik}s otomatis]\033[0m")
    for i in range(detik, 0, -1):
        sys.stdout.write(f"\r  \033[90mMasuk dalam {i}s...\033[0m   ")
        sys.stdout.flush()
        # Cek input non-blocking
        try:
            ready, _, _ = select.select([sys.stdin], [], [], 1)
            if ready:
                sys.stdin.readline()  # buang input
                break
        except:
            time.sleep(1)
    sys.stdout.write("\r" + " "*50 + "\r\n")
    sys.stdout.flush()
    return True

def get_memory():
    try:
        with open("/proc/meminfo") as f:
            c = f.read()
        mt = re.search(r"MemTotal:\s+(\d+)", c)
        ma = re.search(r"MemAvailable:\s+(\d+)", c) or re.search(r"MemFree:\s+(\d+)", c)
        if mt and ma:
            tot, av = int(mt.group(1)), int(ma.group(1))
            return f"{av//1024}MB", int(av/tot*100)
    except:
        pass
    return "N/A", 0

def check_root():
    try:
        r = subprocess.run(["su", "-c", "id"], capture_output=True, timeout=5)
        return r.returncode == 0
    except:
        return False

# ==========================================================
#  CONFIG
# ==========================================================
def load_cfg():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except:
            pass
    return {
        "packages": [],
        "ps_links": {},
        "check_interval": 35,
        "restart_delay": 10,
        "floating_window": True,
        "auto_mute": True,
        "auto_low_graphics": True,
        "webhook_url": "",
    }

def save_cfg(cfg):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"{RE}Gagal simpan config: {e}{R}")

# ==========================================================
#  ROBLOX PACKAGE DETECTION — PURE DEVICE SCAN
# ==========================================================
def find_installed_pkgs():
    """
    Scan SEMUA package di device secara dinamis.
    Tidak pakai hardcoded list — murni dari pm list packages.
    Filter: nama package mengandung 'roblox'.
    """
    installed = []

    # Cara 1: pm list packages (paling reliable)
    ok, out = run_root("pm list packages -f")
    if ok and out:
        for line in out.splitlines():
            line = line.strip()
            # Format: package:/path/to/apk=com.package.name
            if "=" in line:
                pkg = line.split("=")[-1].strip()
            else:
                pkg = line.replace("package:", "").strip()
            if "roblox" in pkg.lower() and pkg not in installed:
                installed.append(pkg)

    # Cara 2: pm list packages tanpa -f (fallback kalau cara 1 kosong)
    if not installed:
        ok2, out2 = run_root("pm list packages")
        if ok2 and out2:
            for line in out2.splitlines():
                pkg = line.replace("package:", "").strip()
                if "roblox" in pkg.lower() and pkg not in installed:
                    installed.append(pkg)

    # Cara 3: dumpsys package (fallback terakhir)
    if not installed:
        ok3, out3 = run_root("dumpsys package packages | grep 'packageName' | grep roblox")
        if ok3 and out3:
            for line in out3.splitlines():
                m = re.search(r"packageName=(\S+)", line)
                if m:
                    pkg = m.group(1).strip()
                    if "roblox" in pkg.lower() and pkg not in installed:
                        installed.append(pkg)

    return installed

def is_running(pkg):
    """
    Cek apakah package Roblox sedang running.
    Kalau salah satu metode bilang RUNNING → return True.
    Kalau SEMUA metode bilang mati → return False.
    """
    # Metode 1: pidof — paling cepat dan akurat
    ok, out = run_root(f"pidof '{pkg}' 2>/dev/null")
    if ok and out.strip():
        return True

    # Metode 2: ps -ef
    ok, out = run_root(f"ps -ef 2>/dev/null | grep '{pkg}' | grep -v grep")
    if ok and pkg in (out or ""):
        return True

    # Metode 3: dumpsys activity processes — paling reliable Android 10+
    ok, out = run_root(f"dumpsys activity processes 2>/dev/null | grep '{pkg}'")
    if ok and pkg in (out or ""):
        return True

    # Metode 4: cmd activity list-tasks
    ok, out = run_root(f"cmd activity list-tasks 2>/dev/null | grep '{pkg}'")
    if ok and pkg in (out or ""):
        return True

    # Metode 5: /proc scan — paling reliable untuk force close
    ok, out = run_root(f"grep -r '{pkg}' /proc/*/cmdline 2>/dev/null | head -1")
    if ok and pkg in (out or ""):
        return True

    return False

def get_pid(pkg):
    ok, out = run_root(f"pidof {pkg}")
    return out.strip() if ok and out.strip() else None

# ==========================================================
#  SISTEM DETEKSI — 4 METODE + FALLBACK OTOMATIS
# ==========================================================
#
#  LEVEL 1 (Utama)  : dumpsys activity → cek Activity name
#  LEVEL 2 (Backup) : network check    → cek koneksi aktif
#  LEVEL 3 (Backup) : CPU/freeze       → cek app nganggur
#  LEVEL 4 (Final)  : pidof only       → cek app hidup/mati
#
#  Kalau level 1 gagal → otomatis turun ke level 2, dst.
# ==========================================================

INGAME_ACTIVITIES = [
    "GameActivity",
    "RobloxGameActivity",
    "NativeGameActivity",
    "RobloxActivity",
    "GameAppActivity",
]

NOTINGAME_ACTIVITIES = [
    "MainActivity",
    "SplashActivity",
    "LoginActivity",
    "LoadingActivity",
    "HomeActivity",
    "LaunchActivity",
    "StartActivity",
]

# Track metode deteksi per package (auto-detect yang work)
_detection_method = {}  # pkg → "activity" | "network" | "cpu" | "pidof"

def get_current_activity(pkg):
    """Ambil nama Activity aktif via dumpsys. Return None kalau gagal."""
    cmds = [
        ("dumpsys activity top 2>/dev/null | grep mResumedActivity", True),
        (f"dumpsys activity activities 2>/dev/null | grep -A2 '{pkg}' | grep 'realActivity'", False),
        (f"dumpsys window windows 2>/dev/null | grep -i 'mCurrentFocus.*{pkg}'", False),
        (f"dumpsys window 2>/dev/null | grep -i 'mCurrentFocus.*{pkg}'", False),
    ]
    for cmd, filter_pkg in cmds:
        ok, out = run_root(cmd, timeout=10)
        if ok and out:
            for line in out.splitlines():
                if filter_pkg and pkg not in line:
                    continue
                m = re.search(r"\.([A-Za-z][A-Za-z0-9_]*Activity[A-Za-z0-9_]*)", line)
                if m:
                    return m.group(1)
    return None

def check_activity(pkg):
    """
    Level 1: Deteksi via dumpsys activity.
    Return: (works: bool, in_game: bool, activity: str)
    """
    activity = get_current_activity(pkg)
    if activity is None:
        return False, False, None  # Method tidak work di HP ini

    # Cek in-game
    for a in INGAME_ACTIVITIES:
        if a.lower() in activity.lower():
            return True, True, activity

    # Cek tidak in-game
    for a in NOTINGAME_ACTIVITIES:
        if a.lower() in activity.lower():
            return True, False, activity

    # Activity tidak dikenal — anggap in-game
    return True, True, activity

def check_network(pkg):
    """
    Level 2: Deteksi via koneksi network aktif.
    Return: (works: bool, connected: bool)
    """
    pid = get_pid(pkg)
    if not pid:
        return True, False  # Method work, tapi app mati

    first_pid = pid.strip().split()[0]

    # Cara 1: ss
    ok, out = run_root(f"ss -tp 2>/dev/null | grep '{first_pid}'", timeout=8)
    if ok and out.strip():
        established = [l for l in out.splitlines() if "ESTAB" in l]
        return True, len(established) > 0

    # Cara 2: netstat
    ok2, out2 = run_root(f"netstat -tp 2>/dev/null | grep {pkg}", timeout=8)
    if ok2 and "ESTABLISHED" in out2:
        return True, True

    # Cara 3: /proc/{pid}/net/tcp6
    ok3, out3 = run_root(
        f"cat /proc/{first_pid}/net/tcp6 2>/dev/null | grep -c '0A'",
        timeout=8
    )
    if ok3 and out3.strip().isdigit():
        return True, int(out3.strip()) > 0

    # Cara 4: /proc/{pid}/net/tcp
    ok4, out4 = run_root(
        f"cat /proc/{first_pid}/net/tcp 2>/dev/null | grep -c '0A'",
        timeout=8
    )
    if ok4 and out4.strip().isdigit():
        return True, int(out4.strip()) > 0

    return False, False  # Method tidak work

def check_cpu_activity(pkg):
    """
    Level 3: Deteksi via CPU usage.
    Return: (works: bool, active: bool)
    App aktif = CPU > 0.5%
    """
    cpu = get_cpu_usage(pkg)
    if cpu < 0:
        return False, False  # Tidak bisa baca CPU
    return True, cpu > 0.5

def is_in_game(pkg):
    """
    Sistem deteksi utama dengan fallback otomatis.
    Otomatis pilih metode terbaik yang work di HP ini.
    Return: (in_game: bool, activity: str, method: str)
    """
    global _detection_method

    # App harus running dulu
    if not is_running(pkg):
        return False, None, "pidof"

    current_method = _detection_method.get(pkg, "auto")

    # -- LEVEL 1: Activity check ------------------------
    if current_method in ("auto", "activity"):
        works, ingame, activity = check_activity(pkg)
        if works:
            _detection_method[pkg] = "activity"
            log(f"{pkg}: Metode=activity | Activity={activity} | InGame={ingame}", "DEBUG")
            return ingame, activity, "activity"
        else:
            if current_method == "activity":
                # Metode ini tiba-tiba tidak work → reset ke auto
                _detection_method[pkg] = "auto"
            log(f"{pkg}: dumpsys activity tidak work → coba network", "WARN")

    # -- LEVEL 2: Network check -------------------------
    if current_method in ("auto", "network"):
        works, connected = check_network(pkg)
        if works:
            _detection_method[pkg] = "network"
            log(f"{pkg}: Metode=network | Connected={connected}", "DEBUG")
            return connected, "network-check", "network"
        else:
            if current_method == "network":
                _detection_method[pkg] = "auto"
            log(f"{pkg}: network check tidak work → coba CPU", "WARN")

    # -- LEVEL 3: CPU activity check --------------------
    if current_method in ("auto", "cpu"):
        works, active = check_cpu_activity(pkg)
        if works:
            _detection_method[pkg] = "cpu"
            log(f"{pkg}: Metode=cpu | Active={active}", "DEBUG")
            return active, "cpu-check", "cpu"
        else:
            log(f"{pkg}: CPU check tidak work → fallback pidof", "WARN")

    # -- LEVEL 4: Fallback — pidof saja -----------------
    _detection_method[pkg] = "pidof"
    running = is_running(pkg)
    log(f"{pkg}: Metode=pidof (fallback) | Running={running}", "DEBUG")
    return running, "pidof-only", "pidof"

# ==========================================================
#  NETWORK CHECK (standalone, dipakai is_in_game)
# ==========================================================
def has_active_connection(pkg):
    """Wrapper untuk backward compat."""
    works, connected = check_network(pkg)
    return connected

# ==========================================================
#  FREEZE DETECTION via CPU
# ==========================================================
def get_cpu_usage(pkg):
    ok, out = run_root(f"top -bn1 | grep {pkg}", timeout=10)
    if ok and out:
        for line in out.splitlines():
            if pkg in line:
                for part in line.split():
                    try:
                        v = float(part.replace('%', ''))
                        if 0 <= v <= 100:
                            return v
                    except:
                        pass
    return -1.0

def is_frozen(pkg):
    """
    Ambil 3 sample CPU tiap 3 detik.
    Rata-rata < 0.5% padahal app running = freeze.
    """
    samples = []
    for _ in range(3):
        v = get_cpu_usage(pkg)
        if v >= 0:
            samples.append(v)
        time.sleep(3)
    return bool(samples) and (sum(samples) / len(samples)) < 0.5

# ==========================================================
#  ROBLOX ACTIONS
# ==========================================================
def force_stop(pkg):
    run_root(f"am force-stop {pkg}")
    time.sleep(1)

def clear_cache_safe(pkg):
    """Clear cache AMAN — tidak hapus data login."""
    run_root(f"rm -rf /data/data/{pkg}/cache/")
    run_root(f"rm -rf /data/data/{pkg}/code_cache/")
    run_root(f"rm -rf /data/user/0/{pkg}/cache/*")

def protect_app(pkg):
    """Set oom_score_adj -1000 supaya sistem tidak kill Roblox."""
    ok, pid = run_root(f"pidof {pkg}")
    if ok and pid.strip():
        for p in pid.strip().split():
            run_root(f"echo -1000 > /proc/{p}/oom_score_adj")
            run_root(f"renice -19 -p {p}")

def mute_roblox():
    run_root("media volume --stream 3 --set 0 2>/dev/null || true")

def set_low_graphics(pkg):
    pref = f"/data/data/{pkg}/shared_prefs"
    ok, files = run_root(f"ls {pref} 2>/dev/null")
    if not ok:
        return
    for fname in files.split():
        if not fname.strip().endswith(".xml"):
            continue
        ok2, content = run_root(f"cat {pref}/{fname.strip()}")
        if ok2 and "GraphicsQualityLevel" in content:
            run_root(
                f"sed -i 's/<int name=\"GraphicsQualityLevel\" value=\"[0-9]*\"/"
                f"<int name=\"GraphicsQualityLevel\" value=\"1\"/g' {pref}/{fname.strip()}"
            )

def get_resolution():
    ok, out = run_root("dumpsys window displays")
    if ok and out:
        m = re.search(r"cur=(\d+)x(\d+)", out)
        if m:
            return int(m.group(1)), int(m.group(2))
    ok, out = run_root("wm size")
    if ok and out:
        m = re.search(r"(\d+)x(\d+)", out)
        if m:
            return int(m.group(1)), int(m.group(2))
    return 1080, 2400

def grid_bounds(idx, total, sw, sh):
    cols = math.ceil(math.sqrt(total))
    rows = math.ceil(total / cols)
    cw, ch = sw // cols, sh // rows
    r = (idx - 1) // cols
    c = (idx - 1) % cols
    return f"{c*cw},{r*ch},{(c+1)*cw},{(r+1)*ch}"

def parse_launch_link(raw):
    """
    Auto konversi input user ke format link yang bisa dilaunching:
    - Angka saja          → roblox://placeId=XXXX
    - roblox://...        → langsung pakai
    - https://roblox.com  → langsung pakai
    - Link private server → langsung pakai
    """
    raw = raw.strip()

    # Kalau angka doang → Game ID → konversi ke roblox URI
    if raw.isdigit():
        return f"roblox://placeId={raw}"

    # Kalau sudah format roblox:// → langsung pakai
    if raw.startswith("roblox://"):
        return raw

    # Kalau link https roblox games → extract place ID dan konversi
    m = re.search(r"roblox\.com/games/(\d+)", raw)
    if m:
        place_id = m.group(1)
        # Kalau ada privateServerLinkCode → pakai link aslinya
        if "privateServerLinkCode" in raw:
            return raw
        return f"roblox://placeId={place_id}"

    # Kalau link private server langsung → pakai apa adanya
    return raw

def launch_game(ps_link, pkg, bounds=None):
    """
    Launch Roblox ke PS Link / Game ID.
    Auto detect format input → konversi → launch.
    Coba 3 cara: ActivityProtocolLaunch → intent VIEW pkg → intent VIEW global.
    """
    link   = parse_launch_link(ps_link)
    extras = f"--windowingMode 5 --bounds {bounds}" if bounds else ""
    cmds   = [
        f'am start {extras} -n {pkg}/com.roblox.client.ActivityProtocolLaunch -a android.intent.action.VIEW -d "{link}"',
        f'am start {extras} -a android.intent.action.VIEW -d "{link}" -p {pkg}',
        f'am start -a android.intent.action.VIEW -d "{link}"',
    ]
    for cmd in cmds:
        ok, out = run_root(cmd)
        if ok and "Error:" not in out and "does not exist" not in out:
            return True
    return False

# ==========================================================
#  BANNER MENU
# ==========================================================
MENU_ITEMS = [
    ("1",  "Start Auto Rejoin"),
    ("2",  "Detect & Set Packages Roblox"),
    ("3",  "Set PS Link / Game ID (Semua Package)"),
    ("4",  "Set PS Link per Package (Berbeda-beda)"),
    ("5",  "Clear Config"),
    ("6",  "List Config"),
    ("7",  "Setup Webhook Discord"),
    ("8",  "Set Interval Cek"),
    ("9",  "Toggle Floating Window"),
    ("10", "Toggle Auto Mute"),
    ("11", "Toggle Low Grafik"),
    ("12", "Diagnostic (Test Deteksi HP ini)"),
    ("13", "Lihat Log Aktivitas"),
    ("14", "Exit"),
]

MENU_ITEMS = [
    ( "1",  "Start Auto Rejoin"),
    ( "2",  "Detect Packages Roblox"),
    ( "3",  "Set PS Link (Semua)"),
    ( "4",  "Set PS Link per Package"),
    ( "5",  "Clear Config"),
    ( "6",  "List Config"),
    ( "7",  "Setup Webhook"),
    ( "8",  "Set Interval"),
    ( "9",  "Toggle Floating Window"),
    ("10",  "Toggle Auto Mute"),
    ("11",  "Toggle Low Grafik"),
    ("12",  "Toggle Auto Tap Splash"),
    ("13",  "Set AutoExec Script"),
    ("14",  "Diagnostic"),
    ("15",  "Lihat Log"),
    ("16",  "Exit"),
]

def get_term_width():
    """Auto detect lebar terminal."""
    try:
        import shutil
        return shutil.get_terminal_size().columns
    except:
        pass
    try:
        cols = int(os.environ.get("COLUMNS", 0))
        if cols > 0:
            return cols
    except:
        pass
    return 44

def print_banner():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()
    mem, mpct = get_memory()
    cfg  = load_cfg()
    pkgs = cfg.get("packages", [])

    W  = max(30, get_term_width() - 1)
    c1 = int(W * 0.18)
    c2 = W - c1 - 3

    def sep(ch='-'):
        sys.stdout.write(f"{CY}+{ch*(c1+1)}+{ch*(c2+1)}+{R}\n")

    def row(t1, t2, c1v=None, c2v=None):
        _c1 = c1v or R
        _c2 = c2v or R
        sys.stdout.write(
            f"{CY}|{_c1} {str(t1):<{c1}} "
            f"{CY}|{_c2} {str(t2):<{c2}}{R} {CY}|{R}\n"
        )

    sys.stdout.write(f"\n{MG}  YURXZ Rejoin v9  |  No Cookie  |  by YURXZ{R}\n")
    sys.stdout.write(f"{GY}  RAM: {mem} ({mpct}%) | Packages: {len(pkgs)}{R}\n\n")

    sep('=')
    row("No", "Menu", YE, WH)
    sep('-')
    for num, label in MENU_ITEMS:
        row(num, label, YE, WH)
    sep('=')
    print()

# ==========================================================
#  DRAW UI MONITORING
# ==========================================================
def draw_ui(accounts, sys_status, prog="", nxt_wh=""):
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()
    mem, mpct = get_memory()

    try:
        import shutil
        W = shutil.get_terminal_size().columns
    except:
        W = int(os.environ.get("COLUMNS", 44))
    W = max(28, W - 1)
    sep  = "=" * W
    sep2 = "-" * W

    def trunc(s, n):
        s = str(s).replace('\n','').replace('\r','')
        s = s.encode('ascii', errors='replace').decode('ascii')
        return s[:n-1] + "." if len(s) > n else s

    st_txt = (prog + " " if prog else "") + (sys_status or "Idle")
    if nxt_wh: st_txt += f" | {nxt_wh}"

    mode = []
    if ARGS.preventif: mode.append("PREV")
    if ARGS.low:       mode.append("LOW")

    mtd_labels = {
        "activity": "[A]",
        "network":  "[N]",
        "cpu":      "[C]",
        "pidof":    "[P]",
    }

    # Header
    sys.stdout.write(f"{CY}{sep}{R}\n")
    sys.stdout.write(f"{MG} YURXZ Rejoin v9  by YURXZ{R}\n")
    sys.stdout.write(f"{CY}{sep2}{R}\n")
    sys.stdout.write(f"{YE} {trunc(st_txt, W-2)}{R}\n")
    sys.stdout.write(f"{GY} RAM: {mem} ({mpct}%){R}\n")
    if mode:
        sys.stdout.write(f"{GY} Mode: {' | '.join(mode)}{R}\n")
    sys.stdout.write(f"{CY}{sep2}{R}\n")

    # Package list — portrait: tiap package 2 baris
    for a in accounts:
        st  = a.get("status", "?")
        mtd = a.get("method", "auto")
        lbl = mtd_labels.get(mtd, "[?]")
        col = GR
        if any(x in st for x in ["Restart","Launch","Wait","Cache","Stop","Loading","Cek","Detect","Tap","Inject"]):
            col = YE
        elif any(x in st for x in ["Error","Failed","Crash","Freeze","mati","putus"]):
            col = RE
        elif any(x in st for x in ["Idle","Pending"]):
            col = GY
        pkg     = a.get('pkg', '?').replace('com.roblox.', 'rb.')
        rejoin  = a.get('rejoin_count', 0)
        sys.stdout.write(f"{CY} {lbl}{R} {WH}{pkg}{GY} ({rejoin}x){R}\n")
        sys.stdout.write(f"    {col}{trunc(st, W-5)}{R}\n")
        sys.stdout.write(f"{GY} {sep2}{R}\n")

    sys.stdout.write(f"{CY}{sep}{R}\n")
    sys.stdout.write(f"{GY} [q]=stop{R}\n")
    sys.stdout.flush()

# ==========================================================
#  MENU 1 — START AUTO REJOIN (tanpa cookie)
# ==========================================================
def watch_package(a, cfg, accounts, sw, sh, tot, wh_url,
                  do_float, do_mute, do_lowgfx, stop_event):
    """
    Worker thread — monitor satu package secara independen.
    Tiap package punya thread sendiri, jadi rejoin/tap paralel.
    """
    import threading

    pkg          = a["pkg"]
    link         = a["ps_link"]
    ae_script    = cfg.get("autoexec_script", "")
    ae_delay     = cfg.get("autoexec_delay", 30)
    auto_tap     = cfg.get("auto_tap_splash", True)
    tap_interval = cfg.get("tap_interval", 3)

    # Hitung posisi tap sesuai grid bounds package ini
    def get_tap_pos():
        if do_float and tot > 1:
            bounds_str = grid_bounds(a["index"], tot, sw, sh)
            try:
                x1, y1, x2, y2 = map(int, bounds_str.split(","))
                return (x1 + x2) // 2, (y1 + y2) // 2
            except:
                pass
        return sw // 2, sh // 2

    def do_rejoin(reason):
        """Rejoin package ini."""
        a["rejoin_count"] = a.get("rejoin_count", 0) + 1
        log(f"{pkg}: {reason} → Rejoin #{a['rejoin_count']}", "WARN")
        a["status"] = f"⚠️ {reason}"

        if wh_url:
            _send_webhook_nocookie(wh_url, accounts,
                                   f"⚠️ Disconnect: {pkg}", 15158332)

        # Force stop → clear cache → launch
        a["status"] = "Force stop..."
        run_root(f"am force-stop {pkg}")
        time.sleep(2)

        a["status"] = "Clear cache..."
        clear_cache_safe(pkg)

        a["status"] = "Relaunching..."
        bounds = grid_bounds(a["index"], tot, sw, sh) if do_float else None
        launch_game(link, pkg, bounds)
        time.sleep(5)

        if do_mute:   mute_roblox()
        if do_lowgfx: set_low_graphics(pkg)
        protect_app(pkg)

        # Auto tap + inject autoexec sampai in-game
        cx, cy      = get_tap_pos()
        injected_ae = False
        game_entered= False
        total_wait  = max(ae_delay + 10, 40)

        for t in range(total_wait, 0, -1):
            if stop_event.is_set():
                return

            # Detect activity
            activity   = get_current_activity(pkg)
            ingame_now = False
            if activity:
                for ga in INGAME_ACTIVITIES:
                    if ga.lower() in activity.lower():
                        ingame_now = True
                        break

            if ingame_now and not game_entered:
                game_entered = True
                a["status"]  = f"In-game! {activity}"
                log(f"{pkg}: Game loaded, activity={activity}", "INFO")
                # Inject autoexec langsung
                if ae_script and not injected_ae:
                    a["status"] = "Inject autoexec..."
                    inject_autoexec(pkg, ae_script)
                    injected_ae = True
                break

            # Auto tap selama loading — tiap detik, semua posisi
            if auto_tap and not game_entered:
                # Bawa ke foreground
                run_root(f"am start -n {pkg}/com.roblox.client.ActivityProtocolLaunch 2>/dev/null; true")
                time.sleep(0.2)
                # Tap banyak posisi
                for tap_y in [cy, int(sh * 0.85), int(sh * 0.7), int(sh * 0.5)]:
                    run_root(f"input tap {cx} {tap_y}")
                    time.sleep(0.05)
                act_str = activity or "loading"
                a["status"] = f"Tapping [{act_str}] {t}s"

            # Fallback inject kalau lewat ae_delay
            if not injected_ae and t <= ae_delay and ae_script:
                a["status"] = "Inject autoexec..."
                inject_autoexec(pkg, ae_script)
                injected_ae = True

            time.sleep(1)

        a["status"] = f"Running ✅ (rejoin #{a['rejoin_count']})"
        if wh_url:
            _send_webhook_nocookie(wh_url, accounts,
                                   f"✅ Rejoin OK: {pkg}", 3066993)

    # ── Main monitoring loop untuk package ini ─────────────
    while not stop_event.is_set():
        try:
            # Cek 1: app running?
            if not is_running(pkg):
                do_rejoin("App mati / crash")
                continue

            # Cek 2: in-game?
            ingame, activity, method = is_in_game(pkg)
            a["method"] = method

            if not ingame:
                a["loading_count"] = a.get("loading_count", 0) + 1

                if auto_tap:
                    cx, cy = get_tap_pos()

                    # Bawa Roblox ke foreground dulu sebelum tap
                    run_root(f"am start -n {pkg}/com.roblox.client.ActivityProtocolLaunch 2>/dev/null; true")
                    time.sleep(0.3)

                    # Tap di beberapa posisi layar (splash bisa di mana saja)
                    for tap_y in [cy, int(sh * 0.7), int(sh * 0.85), int(sh * 0.5)]:
                        run_root(f"input tap {cx} {tap_y}")
                        time.sleep(0.1)

                    # Swipe juga (kadang splash butuh swipe)
                    if a["loading_count"] % 5 == 0:
                        run_root(f"input swipe {cx} {int(sh*0.7)} {cx} {int(sh*0.3)} 300")

                    a["status"] = f"Tapping splash [{activity or 'loading'}] ({a['loading_count']})"
                else:
                    a["status"] = f"Loading [{activity or '?'}] ({a['loading_count']})"

                # Threshold jauh lebih tinggi — Fisch bisa loading 60-90 detik
                # 60 × 2 detik = 120 detik max tunggu
                if a["loading_count"] > 60:
                    do_rejoin(f"Loading timeout ({activity or method})")
                    a["loading_count"] = 0
            else:
                a["loading_count"] = 0
                protect_app(pkg)
                if method == "activity":
                    a["status"] = f"In-game ✅ {activity}"
                elif method == "network":
                    a["status"] = "In-game ✅ net"
                elif method == "cpu":
                    a["status"] = "Running ✅ cpu"
                else:
                    a["status"] = "Running ✅"

        except Exception as e:
            log(f"{pkg}: Error di watch_thread: {e}", "WARN")

        time.sleep(2)  # Cek tiap 2 detik

def menu_start_rejoin():
    if not check_root():
        print(f"{RE}Root access required!{R}")
        wait_enter(); return

    cfg  = load_cfg()
    pkgs = cfg.get("packages", [])

    # Auto detect kalau belum ada
    if not pkgs:
        print(f"{YE}Package belum diset, auto detecting...{R}")
        pkgs = find_installed_pkgs()
        if not pkgs:
            print(f"{RE}Tidak ada package Roblox ditemukan!{R}")
            wait_enter(); return
        cfg["packages"] = pkgs
        save_cfg(cfg)

    ps_links    = cfg.get("ps_links", {})
    global_link = cfg.get("global_ps_link", "")

    # Pastikan semua package punya PS link
    missing = [p for p in pkgs if not ps_links.get(p) and not global_link]
    if missing:
        print(f"{RE}PS Link belum diset untuk:{R}")
        for m in missing: print(f"  - {m}")
        print(f"{YE}Gunakan Menu 3 atau 4 untuk set PS Link.{R}")
        wait_enter(); return

    interval      = 20 if ARGS.preventif else cfg.get("check_interval", 35)
    restart_delay = cfg.get("restart_delay", 10)
    do_float      = cfg.get("floating_window", True)
    do_mute       = cfg.get("auto_mute", True)
    do_lowgfx     = cfg.get("auto_low_graphics", True)
    wh_url        = cfg.get("webhook_url", "")

    if ARGS.low:
        interval = max(interval, 50)

    sw, sh = get_resolution()
    tot    = len(pkgs)

    # Build daftar akun monitoring
    accounts = []
    for i, pkg in enumerate(pkgs):
        link = ps_links.get(pkg) or global_link
        accounts.append({
            "index":         i + 1,
            "pkg":           pkg,
            "ps_link":       link,
            "status":        "Pending",
            "freeze_count":  0,
            "rejoin_count":  0,
        })

    run_root("setenforce 0")

    # -- Launch awal semua package -------------------------
    for i, a in enumerate(accounts):
        pkg  = a["pkg"]
        link = a["ps_link"]

        a["status"] = "Force stop..."
        draw_ui(accounts, "Launching", f"[{i+1}/{tot}]")
        force_stop(pkg)

        a["status"] = "Clear cache..."
        draw_ui(accounts, "Launching", f"[{i+1}/{tot}]")
        clear_cache_safe(pkg)

        a["status"] = "Launching..."
        draw_ui(accounts, "Launching", f"[{i+1}/{tot}]")
        bounds = grid_bounds(a["index"], tot, sw, sh) if do_float else None
        ok = launch_game(link, pkg, bounds)

        if ok:
            a["status"] = "Launched ✓"
            if do_mute:
                a["status"] = "Muting..."
                draw_ui(accounts, "Launching", f"[{i+1}/{tot}]")
                mute_roblox()
            if do_lowgfx:
                a["status"] = "Set low grafik..."
                draw_ui(accounts, "Launching", f"[{i+1}/{tot}]")
                set_low_graphics(pkg)
            # Inject AutoExec kalau ada script — dengan delay supaya game loading selesai
            ae_script = cfg.get("autoexec_script", "")
            ae_delay  = cfg.get("autoexec_delay", 30)  # default 30 detik
            if ae_script:
                # Inject file dulu sebelum delay (supaya executor baca saat load)
                a["status"] = "Inject autoexec..."
                draw_ui(accounts, "Launching", f"[{i+1}/{tot}]")
                ok_ae, _ = inject_autoexec(pkg, ae_script)
                log(f"AutoExec pre-inject {'OK' if ok_ae else 'GAGAL'} untuk {pkg}", "INFO")
            time.sleep(3)
            protect_app(pkg)
            log(f"Launch awal {pkg} → OK", "INFO")
        else:
            a["status"] = "Launch Failed ✗"
            log(f"Launch awal {pkg} → GAGAL", "WARN")

        if i < tot - 1:
            for t in range(restart_delay, 0, -1):
                draw_ui(accounts, "Launching", f"Next in {t}s")
                time.sleep(1)

    # Tunggu game load
    for t in range(20, 0, -1):
        draw_ui(accounts, "Initializing", f"Wait {t}s")
        time.sleep(1)

    for a in accounts:
        a["status"] = "Running ✅" if is_running(a["pkg"]) else "Not Running ⚠️"

    last_wh    = time.time()
    stop_event = __import__('threading').Event()

    # ── Jalankan thread per package ────────────────────────
    import threading
    threads = []
    for i_t, a in enumerate(accounts):
        t = threading.Thread(
            target=watch_package,
            args=(a, cfg, accounts, sw, sh, tot, wh_url,
                  do_float, do_mute, do_lowgfx, stop_event),
            daemon=True
        )
        t.start()
        threads.append(t)
        log(f"Thread dimulai untuk {a['pkg']}", "INFO")
        # Delay antar thread supaya tidak bertabrakan
        if i_t < len(accounts) - 1:
            time.sleep(2)

    # ── Main loop — UI + webhook + baca command dari bot ───
    try:
        while True:
            nxt_wh = ""
            if wh_url:
                diff = int(600 - (time.time() - last_wh))
                if diff <= 0:
                    _send_webhook_nocookie(wh_url, accounts)
                    last_wh = time.time()
                    diff    = 600
                nxt_wh = f"WH {diff//60}m"

            draw_ui(accounts, "Monitoring", f"{tot} pkg aktif", nxt_wh)

            # Baca perintah dari bot (file-based command)
            try:
                if os.path.exists(CMD_FILE):
                    with open(CMD_FILE) as f:
                        cmd = f.read().strip()
                    os.remove(CMD_FILE)
                    if cmd == "stop":
                        raise KeyboardInterrupt
                    elif cmd == "start":
                        pass  # sudah jalan, ignore
            except KeyboardInterrupt:
                raise
            except:
                pass

            # Simpan status
            try:
                with open(STATUS_FILE, "w") as f:
                    json.dump([{"pkg": x["pkg"], "status": x["status"],
                                "rejoin": x.get("rejoin_count", 0)} for x in accounts], f)
            except:
                pass

            # Cek tombol q
            try:
                import select
                tty_q = _open_tty()
                src_q = tty_q if tty_q else sys.stdin
                ready, _, _ = select.select([src_q], [], [], 2)
                if ready:
                    ch = src_q.read(1)
                    if isinstance(ch, bytes):
                        try: ch = ch.decode('utf-8', errors='ignore')
                        except: ch = ''
                    if ch.lower() in ('q', '\x03', '\x1b'):
                        if tty_q:
                            try: tty_q.close()
                            except: pass
                        raise KeyboardInterrupt
                if tty_q:
                    try: tty_q.close()
                    except: pass
            except KeyboardInterrupt:
                raise
            except:
                time.sleep(2)

    except KeyboardInterrupt:
        stop_event.set()
        # Hapus cmd file kalau ada
        try:
            if os.path.exists(CMD_FILE): os.remove(CMD_FILE)
        except: pass
        print(f"\n{YE}[!] Menghentikan semua thread...{R}")
        for t in threads:
            t.join(timeout=3)
        print(f"{YE}[!] Dihentikan.{R}\n")

def _send_webhook_nocookie(url, accounts, title="📊 Status Update", color=3447003):
    try:
        import requests as req
    except:
        return
    fields = []
    for a in accounts:
        st = a.get("status","?")
        em = "🟢" if "Running" in st else ("🔴" if any(x in st for x in ["Error","Crash","Failed","mati","freeze"]) else "🟡")
        fields.append({
            "name":   f"{em} {a.get('pkg','?')}",
            "value":  f"**Status:** {st} | Rejoin: {a.get('rejoin_count',0)}x",
            "inline": False,
        })
    payload = {"embeds":[{
        "title": title, "color": color, "fields": fields,
        "footer": {"text": f"YURXZ v9 No-Cookie • {time.strftime('%d/%m/%Y %H:%M:%S')}"},
    }]}
    try:
        req.post(url, json=payload, timeout=10)
    except:
        pass

# ==========================================================
#  MENU 2 — DETECT & SET PACKAGES
# ==========================================================
def menu_detect_packages():
    cfg = load_cfg()
    print(f"\n{CY}[ Detect & Set Packages Roblox ]{R}")
    print(f"{YE}Scanning device...{R}\n")
    found = find_installed_pkgs()
    if not found:
        print(f"{RE}Tidak ada package Roblox ditemukan!{R}")
        pause_auto(10); return
    print(f"{GR}Package ditemukan:{R}")
    for p in found:
        ok, out = run_root(f"dumpsys package {p} | grep versionName")
        ver = out.strip().replace("versionName=","").strip() if ok and out.strip() else "?"
        print(f"  {GR}✓{R} {p}  {GY}(v{ver}){R}")
    cfg["packages"] = found
    save_cfg(cfg)
    print(f"\n{GR}✓ {len(found)} package tersimpan ke config!{R}")
    pause_auto(10)

# ==========================================================
#  MENU 3 — SET PS LINK / GAME ID (SEMUA PACKAGE)
# ==========================================================
def input_ps_link(title="Set PS Link / Game ID"):
    """
    Menu pilihan format PS Link — bisa pilih 1 atau lebih format.
    Return link yang sudah siap dipakai.
    """
    while True:
        print(f"\n{CY}[ {title} ]{R}")
        print(f"{GY}{'-'*get_term_width()}{R}")
        print(f"  {YE}1{R}. Game ID          contoh: {GR}995679412{R}")
        print(f"  {YE}2{R}. Roblox URI       contoh: {GR}roblox://placeId=995679412{R}")
        print(f"  {YE}3{R}. Link game Roblox contoh: {GR}https://www.roblox.com/games/995679412{R}")
        print(f"  {YE}4{R}. Private Server   contoh: {GR}https://www.roblox.com/games/...?privateServerLinkCode=xxx{R}")
        print(f"  {YE}5{R}. Batal")
        print(f"{GY}{'-'*get_term_width()}{R}")
        pilih = inp(f"{YE}Pilih format (1-5): {R}")

        if pilih == "5" or not pilih:
            return None

        if pilih == "1":
            val = inp_text(f"{YE}Masukkan Game ID (angka): {R}")
            if val and val.isdigit():
                link = f"roblox://placeId={val}"
                print(f"{GR}✓ Link: {link}{R}")
                return link
            else:
                print(f"{RE}Game ID harus angka!{R}")

        elif pilih == "2":
            val = inp_text(f"{YE}Masukkan Roblox URI (roblox://...): {R}")
            if val and val.startswith("roblox://"):
                print(f"{GR}✓ Link: {val}{R}")
                return val
            else:
                print(f"{RE}Harus diawali roblox://{R}")

        elif pilih == "3":
            val = inp_text(f"{YE}Masukkan link game Roblox: {R}")
            if val and "roblox.com/games" in val:
                link = parse_launch_link(val)
                print(f"{GR}✓ Link: {link}{R}")
                return link
            else:
                print(f"{RE}Link tidak valid!{R}")

        elif pilih == "4":
            val = inp_text(f"{YE}Paste Private Server link: {R}")
            if val and "privateServerLinkCode" in val:
                print(f"{GR}✓ Link: {val[:60]}...{R}")
                return val
            elif val and "roblox.com" in val:
                print(f"{GR}✓ Link: {val[:60]}{R}")
                return val
            else:
                print(f"{RE}Link tidak valid!{R}")
        else:
            print(f"{RE}Pilihan tidak valid!{R}")

        time.sleep(1)

def menu_set_global_ps():
    cfg = load_cfg()
    current = cfg.get("global_ps_link","")
    if current:
        print(f"\n{GY}PS Link saat ini: {current[:60]}{R}")

    link = input_ps_link("Set PS Link / Game ID untuk Semua Package")
    if not link:
        print(f"{YE}Dibatalkan.{R}")
        wait_enter()
        return

    cfg["global_ps_link"] = link
    pkgs     = cfg.get("packages", find_installed_pkgs())
    ps_links = cfg.get("ps_links", {})
    for pkg in pkgs:
        ps_links[pkg] = link
        print(f"  {GR}✓{R} {pkg}")
    cfg["ps_links"] = ps_links
    save_cfg(cfg)
    print(f"\n{GR}✓ Tersimpan untuk semua package!{R}")
    wait_enter()

# ==========================================================
#  MENU 4 — SET PS LINK PER PACKAGE
# ==========================================================
def menu_set_per_pkg_ps():
    cfg  = load_cfg()
    pkgs = cfg.get("packages", find_installed_pkgs())
    print(f"\n{CY}[ Set PS Link / Game ID per Package ]{R}")
    ps_links = cfg.get("ps_links", {})
    for pkg in pkgs:
        current = ps_links.get(pkg,"")
        print(f"\n{CY}>> Package: {pkg}{R}")
        if current:
            print(f"  {GY}Saat ini: {current[:55]}{R}")
        print(f"  {GY}(Enter skip = tidak diganti){R}")
        skip = inp(f"  {YE}Ganti PS Link untuk package ini? (y/n): {R}").lower()
        if skip != "y":
            print(f"  {GY}Dilewati.{R}")
            continue
        link = input_ps_link(f"PS Link untuk {pkg}")
        if link:
            parsed = parse_launch_link(link)
            print(f"  {GR}✓ Disimpan: {parsed[:50]}{R}")
            ps_links[pkg] = link
    cfg["ps_links"] = ps_links
    cfg["packages"] = pkgs
    save_cfg(cfg)
    print(f"\n{GR}✓ PS Link per-package tersimpan!{R}")
    wait_enter()

# ==========================================================
#  MENU 5 — CLEAR CONFIG
# ==========================================================
def menu_clear_config():
    cfg = load_cfg()
    print(f"\n{CY}[ Clear Config ]{R}")
    print("  1. Clear PS Links saja")
    print("  2. Clear Packages saja")
    print("  3. Clear semua (reset total)")
    print("  4. Batal")
    c = inp(f"{YE}Pilih: {R}")
    if c == "1":
        cfg["ps_links"] = {}; cfg["global_ps_link"] = ""
        save_cfg(cfg); print(f"{GR}✓ PS Links dihapus.{R}")
    elif c == "2":
        cfg["packages"] = []
        save_cfg(cfg); print(f"{GR}✓ Packages dihapus.{R}")
    elif c == "3":
        save_cfg({"packages":[],"ps_links":{},"check_interval":35,
                  "restart_delay":10,"floating_window":True,
                  "auto_mute":True,"auto_low_graphics":True,"webhook_url":""})
        print(f"{GR}✓ Config direset total.{R}")
    else:
        print(f"{YE}Dibatalkan.{R}")
    wait_enter()

# ==========================================================
#  MENU 6 — LIST CONFIG
# ==========================================================
def menu_list_config():
    cfg = load_cfg()
    W   = min(get_term_width(), 44)  # Max 44 char supaya tidak wrap
    sep = "=" * W
    sep2= "-" * W
    MAX = W - 14  # Max panjang value

    def yn(key, default=True):
        return f"{GR}ON {R}" if cfg.get(key, default) else f"{RE}OFF{R}"

    def trunc(s, n=None):
        n = n or MAX
        s = str(s)
        return s[:n] + ".." if len(s) > n else s

    clear()
    print(f"{CY}{sep}{R}")
    print(f"{CY} LIST CONFIG{R}")
    print(f"{CY}{sep}{R}")

    pkgs = cfg.get("packages", [])
    print(f"{YE} Packages: {len(pkgs)}{R}")
    print(f"{CY}{sep2}{R}")
    for p in pkgs:
        ps   = cfg.get("ps_links", {}).get(p, "(belum diset)")
        st   = f"{GR}Running{R}" if is_running(p) else f"{RE}Mati{R}"
        pname = p.replace("com.roblox.", "rb.")
        print(f" {GR}>{R} {pname}")
        print(f"   St: {st}")
        print(f"   PS: {trunc(ps, MAX)}")
    print(f"{CY}{sep2}{R}")
    gps = cfg.get('global_ps_link','(kosong)')
    print(f" {YE}Global PS  :{R} {trunc(gps)}")
    print(f" {YE}Interval   :{R} {cfg.get('check_interval', 35)}s")
    print(f" {YE}Delay      :{R} {cfg.get('restart_delay', 10)}s")
    print(f" {YE}Floating   :{R} {yn('floating_window')}")
    print(f" {YE}Auto Mute  :{R} {yn('auto_mute')}")
    print(f" {YE}Low Grafik :{R} {yn('auto_low_graphics')}")
    print(f" {YE}Auto Tap   :{R} {yn('auto_tap_splash')}")
    print(f" {YE}AE Delay   :{R} {cfg.get('autoexec_delay', 30)}s")
    ae = cfg.get('autoexec_script', '')
    print(f" {YE}AutoExec   :{R} {'Ada' if ae else '(kosong)'}")
    wh = cfg.get('webhook_url', '')
    print(f" {YE}Webhook    :{R} {'Ada' if wh else '(kosong)'}")
    print(f"{CY}{sep}{R}")
    sys.stdout.flush()
    try:
        sys.stdin.readline()  # Tunggu Enter
    except:
        time.sleep(3)

# ==========================================================
#  MENU 7 — SETUP WEBHOOK
# ==========================================================
def menu_setup_webhook():
    cfg = load_cfg()
    print(f"\n{CY}[ Setup Webhook Discord ]{R}")
    current = cfg.get("webhook_url","")
    print(f"{GY}Webhook saat ini: {current[:60] or '(kosong)'}{R}")
    url = inp_text(f"{YE}Masukkan Discord Webhook URL (Enter hapus): {R}")
    cfg["webhook_url"] = url
    save_cfg(cfg)
    if url:
        print(f"{GR}✓ Webhook disimpan!{R}")
        test = inp(f"{YE}Kirim test? (y/n): {R}").lower()
        if test == "y":
            _send_webhook_nocookie(url, [], "🔔 YURXZ Test", 3447003)
            print(f"{GR}✓ Test terkirim!{R}")
    else:
        print(f"{YE}Webhook dihapus.{R}")
    wait_enter()

# ==========================================================
#  MENU 8 — SET INTERVAL
# ==========================================================
def menu_set_interval():
    cfg = load_cfg()
    print(f"\n{CY}[ Set Interval Cek ]{R}")
    print(f"{GY}Interval saat ini: {cfg.get('check_interval',35)}s{R}")
    print(f"{GY}Restart delay saat ini: {cfg.get('restart_delay',10)}s{R}")
    val = inp_text(f"{YE}Interval cek (detik) [Enter skip]: {R}")
    if val.isdigit(): cfg["check_interval"] = int(val)
    val2 = inp_text(f"{YE}Restart delay (detik) [Enter skip]: {R}")
    if val2.isdigit(): cfg["restart_delay"] = int(val2)
    save_cfg(cfg)
    print(f"{GR}✓ Tersimpan!{R}")
    wait_enter()

# ==========================================================
#  MENU 9, 10, 11 — TOGGLE
# ==========================================================
def menu_toggle(key, label):
    cfg = load_cfg()
    current = cfg.get(key, True)
    status_now = f"{GR}ON{R}" if current else f"{RE}OFF{R}"
    print(f"\n{CY}[ {label} ]{R}")
    print(f"{GY}Status sekarang: {status_now}{R}")
    print(f"\n  1. ON")
    print(f"  2. OFF")
    print(f"  3. Batal")
    c = inp(f"\n{YE}Pilih: {R}")
    if c == "1":
        cfg[key] = True
        save_cfg(cfg)
        print(f"\n{GR}✓ {label}: ON{R}")
    elif c == "2":
        cfg[key] = False
        save_cfg(cfg)
        print(f"\n{RE}✓ {label}: OFF{R}")
    else:
        print(f"\n{YE}Dibatalkan.{R}")
    wait_enter()

# ==========================================================
#  MENU 12 — LIHAT LOG
# ==========================================================
def inject_autoexec(pkg, script):
    """
    Inject script Lua ke semua executor yang ada di device.
    Cara kerja:
    1. Scan semua subfolder di dalam package files
    2. Cari folder yang ada 'autoexec' di dalamnya
    3. Inject ke sana + path generic fallback
    Jadi support semua executor termasuk lite/clone/modded.
    """
    base_data   = f"/data/data/{pkg}/files"
    base_sdcard = f"/sdcard/Android/data/{pkg}/files"
    escaped     = script.replace("'", "'\\''")
    paths       = []
    injected    = []

    # ── STEP 1: Scan dinamis semua subfolder executor ──────
    for base in [base_data, base_sdcard]:
        # List semua subfolder di base
        ok, out = run_root(f"ls '{base}' 2>/dev/null")
        if ok and out.strip():
            for folder_name in out.split():
                folder_name = folder_name.strip()
                if not folder_name:
                    continue
                sub = f"{base}/{folder_name}"
                # Cek apakah ada folder autoexec di dalamnya
                ok2, out2 = run_root(f"ls '{sub}' 2>/dev/null")
                if ok2 and out2:
                    items = out2.split()
                    if "autoexec" in items:
                        # Ada folder autoexec → inject ke sana
                        paths.append(f"{sub}/autoexec/autoexec.lua")
                    if "workspace" in items:
                        # Ada folder workspace → inject ke sana juga
                        paths.append(f"{sub}/workspace/autoexec.lua")
                    # Cek file autoexec.lua langsung di subfolder
                    if "autoexec.lua" in items:
                        paths.append(f"{sub}/autoexec.lua")

    # ── STEP 2: Path generic / fallback ───────────────────
    for base in [base_data, base_sdcard]:
        paths += [
            f"{base}/autoexec.lua",
            f"{base}/autoexec/autoexec.lua",
            f"{base}/workspace/autoexec.lua",
        ]

    # ── STEP 3: Dedupe ────────────────────────────────────
    paths = list(dict.fromkeys(paths))

    # ── STEP 4: Inject ke semua path ──────────────────────
    for path in paths:
        folder = "/".join(path.split("/")[:-1])
        run_root(f"mkdir -p '{folder}' 2>/dev/null")
        ok, _ = run_root(f"printf '%s' '{escaped}' > '{path}' && chmod 666 '{path}'")
        if ok:
            injected.append(path)
            log(f"AutoExec OK: {path}", "INFO")

    log(f"AutoExec inject {len(injected)}/{len(paths)} path berhasil untuk {pkg}", "INFO")
    return len(injected) > 0, injected

def menu_autoexec():
    cfg = load_cfg()
    current   = cfg.get("autoexec_script", "")
    ae_delay  = cfg.get("autoexec_delay", 30)

    print(f"\n{CY}[ Set AutoExec Script ]{R}")
    print(f"{GY}{'-'*get_term_width()}{R}")

    if current:
        preview = current[:80] + "..." if len(current) > 80 else current
        print(f"{GY}Script: {preview}{R}")
    else:
        print(f"{GY}Script: (belum ada){R}")
    print(f"{GY}Delay inject: {ae_delay} detik setelah launch{R}")
    print()

    print(f"  {YE}1{R}. Input script baru")
    print(f"  {YE}2{R}. Load dari file (/sdcard/Download/autoexec.lua)")
    print(f"  {YE}3{R}. Test inject ke package sekarang")
    print(f"  {YE}4{R}. Set delay inject (detik setelah launch)")
    print(f"  {YE}5{R}. Hapus AutoExec")
    print(f"  {YE}6{R}. Lihat script saat ini")
    print(f"  {YE}7{R}. Batal")
    print(f"{GY}{'-'*get_term_width()}{R}")

    c = inp(f"{YE}Pilih: {R}")

    if c == "1":
        print(f"\n{GY}Paste script Lua kamu.")
        print(f"Ketik END di baris baru untuk selesai:{R}")
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            except EOFError:
                break
        script = "\n".join(lines).strip()
        if script:
            cfg["autoexec_script"] = script
            save_cfg(cfg)
            print(f"\n{GR}✓ Script disimpan! ({len(lines)} baris){R}")
        else:
            print(f"{RE}Script kosong!{R}")

    elif c == "2":
        path = "/sdcard/Download/autoexec.lua"
        ok, out = run_root(f"cat {path} 2>/dev/null")
        if ok and out.strip():
            cfg["autoexec_script"] = out.strip()
            save_cfg(cfg)
            lines = out.strip().split('\n')
            print(f"\n{GR}✓ Script dimuat dari {path}! ({len(lines)} baris){R}")
        else:
            print(f"{RE}File tidak ditemukan atau kosong!{R}")
            print(f"{GY}Buat file: /sdcard/Download/autoexec.lua{R}")

    elif c == "3":
        script = cfg.get("autoexec_script", "")
        if not script:
            print(f"{RE}Belum ada script! Set dulu dengan pilihan 1 atau 2.{R}")
        else:
            pkgs = cfg.get("packages", find_installed_pkgs())
            if not pkgs:
                print(f"{RE}Tidak ada package!{R}")
            else:
                print(f"\n{YE}Inject ke:{R}")
                for pkg in pkgs:
                    ok, injected = inject_autoexec(pkg, script)
                    status = f"{GR}✓ {len(injected)} path{R}" if ok else f"{RE}✗ Gagal{R}"
                    print(f"  {pkg}: {status}")
                    if ok and injected:
                        # Tampilkan beberapa path yang berhasil
                        for p in injected[:3]:
                            executor = p.split("/files/")[-1].split("/")[0] if "/files/" in p else "generic"
                            print(f"    {GY}-> {executor}: {p.split('/')[-1]}{R}")
                        if len(injected) > 3:
                            print(f"    {GY}... dan {len(injected)-3} path lainnya{R}")
                print(f"\n{GR}✓ Inject selesai!{R}")

    elif c == "4":
        print(f"\n{GY}Delay inject saat ini: {ae_delay} detik{R}")
        print(f"{GY}Rekomendasi: 20-40 detik (tunggu loading game selesai){R}")
        print(f"{GY}Untuk Fisch/game loading lama: 30-45 detik{R}")
        val = inp_text(f"{YE}Masukkan delay (detik): {R}")
        if val.isdigit():
            cfg["autoexec_delay"] = int(val)
            save_cfg(cfg)
            print(f"\n{GR}✓ Delay diset ke {val} detik{R}")
        else:
            print(f"{RE}Harus angka!{R}")

    elif c == "5":
        cfg["autoexec_script"] = ""
        save_cfg(cfg)
        print(f"\n{YE}AutoExec dihapus.{R}")

    elif c == "6":
        script = cfg.get("autoexec_script", "")
        if script:
            print(f"\n{GY}Script ({len(script.split(chr(10)))} baris):{R}")
            print(f"{WH}{script}{R}")
        else:
            print(f"{YE}Belum ada script.{R}")

    else:
        print(f"{YE}Dibatalkan.{R}")

    wait_enter()

def menu_lihat_log():
    print(f"\n{CY}[ Log Aktivitas (50 baris terakhir) ]{R}\n")
    log_path = LOG_FILE
    ok, out = run_root(f"tail -50 {log_path} 2>/dev/null")
    if ok and out:
        print(out)
    else:
        print(f"{GY}Log kosong atau belum ada.{R}")
    wait_enter()

# ==========================================================
#  MENU 12 — DIAGNOSTIC (TEST DETEKSI HP INI)
# ==========================================================
def menu_diagnostic():
    clear()
    print(f"\n{CY}+{'='*get_term_width()}+{R}")
    print(f"{CY}|{MG}   DIAGNOSTIC — Test Kompatibilitas HP Ini       {CY}|{R}")
    print(f"{CY}+{'='*get_term_width()}+{R}\n")

    def ok_str(v): return f"{GR}✅ WORK{R}" if v else f"{RE}❌ TIDAK WORK{R}"

    # -- Test 1: Root -------------------------------------
    print(f"{YE}[1] Root Access...{R}")
    root_ok = check_root()
    print(f"    {ok_str(root_ok)}")
    if not root_ok:
        print(f"{RE}    Root tidak ada! Semua test dibatalkan.{R}")
        wait_enter(); return

    # -- Test 2: pidof ------------------------------------
    print(f"\n{YE}[2] Command pidof...{R}")
    ok, out = run_root("pidof init 2>/dev/null || pidof systemd 2>/dev/null")
    pidof_ok = ok
    print(f"    {ok_str(pidof_ok)}")

    # -- Test 3: pm list packages -------------------------
    print(f"\n{YE}[3] Package scan (pm list packages)...{R}")
    ok, out = run_root("pm list packages 2>/dev/null | head -3")
    pm_ok = ok and bool(out.strip())
    print(f"    {ok_str(pm_ok)}")
    if pm_ok:
        pkgs = find_installed_pkgs()
        if pkgs:
            print(f"    {GR}Roblox packages ditemukan: {len(pkgs)}{R}")
            for p in pkgs: print(f"      - {p}")
        else:
            print(f"    {YE}⚠️  Tidak ada package Roblox (install dulu){R}")

    # -- Test 4: dumpsys activity -------------------------
    print(f"\n{YE}[4] dumpsys activity (deteksi Activity)...{R}")
    ok, out = run_root("dumpsys activity top 2>/dev/null | grep mResumedActivity | head -1")
    dumpsys_ok = ok and bool(out.strip())
    print(f"    {ok_str(dumpsys_ok)}")
    if dumpsys_ok:
        print(f"    {GY}Activity aktif: {out.strip()[:60]}{R}")
        # Cek kalau Roblox running, tampilkan activity-nya
        pkgs = find_installed_pkgs()
        for p in pkgs:
            if is_running(p):
                act = get_current_activity(p)
                print(f"    {GR}Roblox ({p}) Activity: {act or 'tidak terdeteksi'}{R}")

    # -- Test 5: network check ----------------------------
    print(f"\n{YE}[5] Network check (ss/netstat)...{R}")
    ok_ss, _ = run_root("ss -tp 2>/dev/null | head -2")
    ok_ns, _ = run_root("netstat -tp 2>/dev/null | head -2")
    ok_proc, _ = run_root("cat /proc/1/net/tcp 2>/dev/null | head -2")
    net_ok = ok_ss or ok_ns or ok_proc
    print(f"    {ok_str(net_ok)}")
    print(f"    {GY}ss: {ok_str(ok_ss)} | netstat: {ok_str(ok_ns)} | /proc/net: {ok_str(ok_proc)}{R}")

    # -- Test 6: CPU top ----------------------------------
    print(f"\n{YE}[6] CPU monitoring (top)...{R}")
    ok, out = run_root("top -bn1 2>/dev/null | head -3")
    cpu_ok = ok and bool(out.strip())
    print(f"    {ok_str(cpu_ok)}")

    # -- Test 7: am start ---------------------------------
    print(f"\n{YE}[7] Launch intent (am start)...{R}")
    ok, out = run_root("am start --help 2>/dev/null | head -1")
    am_ok = ok
    print(f"    {ok_str(am_ok)}")

    # -- Kesimpulan ---------------------------------------
    print(f"\n{CY}{'='*get_term_width()}{R}")
    print(f"{CY}  KESIMPULAN — Metode Deteksi yang akan dipakai:{R}")
    print(f"{CY}{'='*get_term_width()}{R}")
    if dumpsys_ok:
        print(f"  {GR}✅ UTAMA  : dumpsys activity (paling akurat){R}")
    else:
        print(f"  {RE}❌ UTAMA  : dumpsys activity (tidak work){R}")

    if net_ok:
        print(f"  {GR}✅ BACKUP1: network check{R}")
    else:
        print(f"  {RE}❌ BACKUP1: network check (tidak work){R}")

    if cpu_ok:
        print(f"  {GR}✅ BACKUP2: CPU monitoring{R}")
    else:
        print(f"  {RE}❌ BACKUP2: CPU monitoring (tidak work){R}")

    if pidof_ok:
        print(f"  {GR}✅ BACKUP3: pidof (selalu jadi fallback){R}")

    # Tentukan metode terbaik
    if dumpsys_ok:
        best = f"{GR}dumpsys activity{R}"
    elif net_ok:
        best = f"{YE}network check{R}"
    elif cpu_ok:
        best = f"{YE}CPU monitoring{R}"
    else:
        best = f"{YE}pidof only (basic){R}"

    print(f"\n  {WH}Script akan pakai: {best}")
    print(f"{CY}{'='*get_term_width()}{R}")

    # Simpan hasil ke config
    cfg = load_cfg()
    cfg["diagnostic"] = {
        "dumpsys": dumpsys_ok,
        "network": net_ok,
        "cpu":     cpu_ok,
        "pidof":   pidof_ok,
    }
    save_cfg(cfg)
    print(f"\n{GR}✓ Hasil diagnostic tersimpan ke config.{R}")
    wait_enter()

# ==========================================================
#  MAIN
# ==========================================================
def main():
    if ARGS.auto:
        if not check_root():
            print(f"{RE}Root required!{R}"); sys.exit(1)
        log("Start dengan --auto","INFO")
        menu_start_rejoin()
        return

    MENU_FN = {
        "1":  menu_start_rejoin,
        "2":  menu_detect_packages,
        "3":  menu_set_global_ps,
        "4":  menu_set_per_pkg_ps,
        "5":  menu_clear_config,
        "6":  menu_list_config,
        "7":  menu_setup_webhook,
        "8":  menu_set_interval,
        "9":  lambda: menu_toggle("floating_window", "Floating Window"),
        "10": lambda: menu_toggle("auto_mute", "Auto Mute"),
        "11": lambda: menu_toggle("auto_low_graphics", "Low Grafik"),
        "12": lambda: menu_toggle("auto_tap_splash", "Auto Tap Splash"),
        "13": menu_autoexec,
        "14": menu_diagnostic,
        "15": menu_lihat_log,
    }

def countdown_before_menu(label, detik=10):
    """
    Countdown sebelum masuk menu.
    Tekan Enter → langsung masuk.
    Otomatis masuk setelah 10 detik.
    """
    import select
    flush_stdin()
    print(f"\n  {GY}>> {WH}{label}{R}")
    print(f"  {GY}[Enter = langsung masuk | tunggu {detik}s otomatis]{R}")
    for i in range(detik, 0, -1):
        sys.stdout.write(f"\r  {GY}Masuk dalam {i}s...{R}   ")
        sys.stdout.flush()
        try:
            ready, _, _ = select.select([sys.stdin], [], [], 1)
            if ready:
                sys.stdin.readline()
                break
        except:
            time.sleep(1)
    sys.stdout.write("\r" + " "*50 + "\r\n")
    sys.stdout.flush()
    return True

# ==========================================================
#  MAIN
# ==========================================================
def parse_sequence(c):
    """
    Parse input bebas jadi sequence angka.
    Contoh: "231" → ["2","3","1"]
    Contoh: "10,11,1" → ["10","11","1"]
    Contoh: "2 3 1" → ["2","3","1"]
    Single digit/number juga tetap work.
    """
    # Kalau ada koma atau spasi → split
    if ',' in c:
        parts = [x.strip() for x in c.split(',')]
    elif ' ' in c:
        parts = [x.strip() for x in c.split()]
    elif len(c) > 2:
        # Angka nempel — parse digit per digit
        # Handle 10-14 (2 digit): kalau ada "1" diikuti 0-4 → 2 digit
        parts = []
        i = 0
        while i < len(c):
            if c[i] == '1' and i+1 < len(c) and c[i+1] in '0123456789':
                two = c[i:i+2]
                if two in ['10','11','12','13','14']:
                    parts.append(two); i += 2
                    continue
            parts.append(c[i]); i += 1
    else:
        parts = [c]
    return [p for p in parts if p]

def main():
    if ARGS.auto:
        if not check_root():
            print(f"{RE}Root required!{R}"); sys.exit(1)
        log("Start dengan --auto","INFO")
        menu_start_rejoin()
        return

    MENU_FN = {
        "1":  menu_start_rejoin,
        "2":  menu_detect_packages,
        "3":  menu_set_global_ps,
        "4":  menu_set_per_pkg_ps,
        "5":  menu_clear_config,
        "6":  menu_list_config,
        "7":  menu_setup_webhook,
        "8":  menu_set_interval,
        "9":  lambda: menu_toggle("floating_window", "Floating Window"),
        "10": lambda: menu_toggle("auto_mute", "Auto Mute"),
        "11": lambda: menu_toggle("auto_low_graphics", "Low Grafik"),
        "12": lambda: menu_toggle("auto_tap_splash", "Auto Tap Splash"),
        "13": menu_autoexec,
        "14": menu_diagnostic,
        "15": menu_lihat_log,
    }

    while True:
        # Cek perintah dari bot dulu
        try:
            if os.path.exists(CMD_FILE):
                with open(CMD_FILE) as f:
                    bot_cmd = f.read().strip()
                os.remove(CMD_FILE)
                if bot_cmd == "start":
                    # Bot minta jalankan rejoin (menu 1)
                    log("Bot CMD: start rejoin", "INFO")
                    clear()
                    menu_start_rejoin()
                    continue
                elif bot_cmd == "stop":
                    log("Bot CMD: stop", "INFO")
                    break
        except:
            pass

        reset_terminal()
        print_banner()
        print(f"{GY}  Tip: 231 = urut Menu2,Menu3,Menu1{R}\n")
        c = inp(f"  {YE}Enter choice: {R}")

        if c.strip() == "16":
            clear(); print(f"{CY}Sampai jumpa!{R}\n"); break

        sequence = parse_sequence(c.strip())

        # Filter yang valid
        valid   = [s for s in sequence if s in MENU_FN or s == "14"]
        invalid = [s for s in sequence if s not in MENU_FN and s != "14"]

        if not valid:
            print(f"\n  {RE}Tidak valid: {c}{R}")
            time.sleep(2); continue

        if invalid:
            print(f"\n  {YE}Diabaikan: {', '.join(invalid)}{R}")
            time.sleep(1)

        labels    = [next((l for n, l in MENU_ITEMS if n == s), f"Menu {s}") for s in valid]
        label_str = " -> ".join(labels)
        countdown_before_menu(label_str, 10)

        for s in valid:
            if s == "14":
                clear(); print(f"{CY}Sampai jumpa!{R}\n"); return
            fn = MENU_FN.get(s)
            if fn:
                clear(); fn()

if __name__ == '__main__':
    main()

