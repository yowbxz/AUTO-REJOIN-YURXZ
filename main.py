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
def clear():
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
    """Buang sisa input di buffer dengan delay kecil."""
    try:
        import termios
        termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
    except:
        pass
    time.sleep(0.2)

def inp(prompt, max_chars=2, timeout=60):
    """Input menu."""
    flush_stdin()
    try:
        return input(prompt).strip()
    except EOFError:
        return ""
    except KeyboardInterrupt:
        raise

def inp_text(prompt, timeout=120):
    """Input teks panjang — pakai input() biasa."""
    flush_stdin()
    try:
        return input(prompt).strip()
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
    """Countdown 10 detik sebelum masuk menu."""
    flush_stdin()
    print(f"\n  \033[90m>> \033[97m{label}\033[0m")
    for i in range(detik, 0, -1):
        sys.stdout.write(f"\r  \033[90mMasuk dalam {i}s...\033[0m   ")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r" + " "*40 + "\r\n")
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
    """Cek apakah package Roblox sedang running."""
    ok, out = run_root(f"pidof {pkg}")
    if ok and out.strip():
        return True
    ok, out = run_root(f"ps -A | grep {pkg}")
    return ok and bool(out.strip())

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
    ("12",  "Diagnostic"),
    ("13",  "Lihat Log"),
    ("14",  "Exit"),
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

    # Auto detect lebar terminal — ASCII only, no emoji/unicode box
    try:
        import shutil
        W = shutil.get_terminal_size().columns
    except:
        W = int(os.environ.get("COLUMNS", 44))
    W = max(30, W - 1)

    c1 = int(W * 0.58)
    c2 = W - c1 - 3

    def trunc(s, l):
        s = str(s).replace('\n','').replace('\r','')
        # Hapus semua karakter non-ASCII supaya lebar konsisten
        s = s.encode('ascii', errors='replace').decode('ascii')
        return s[:l-1] + "." if len(s) > l else s

    def sep(ch='-'):
        sys.stdout.write(f"{CY}+{ch*(c1+1)}+{ch*(c2+1)}+{R}\n")

    def row(t1, t2, col=R):
        t1 = t1.encode('ascii', errors='replace').decode('ascii')
        t2 = t2.encode('ascii', errors='replace').decode('ascii')
        sys.stdout.write(
            f"{CY}|{R} {t1:<{c1}} "
            f"{CY}|{col} {t2:<{c2}}{R} {CY}|{R}\n"
        )

    st_txt = (prog + " " if prog else "") + (sys_status or "Idle")
    if nxt_wh: st_txt += f" | {nxt_wh}"

    mode = []
    if ARGS.preventif: mode.append("PREVENTIF")
    if ARGS.low:       mode.append("LOW-PERF")

    mtd_labels = {
        "activity": "[A]",
        "network":  "[N]",
        "cpu":      "[C]",
        "pidof":    "[P]",
    }

    sys.stdout.write(f"\n{MG}  YURXZ Rejoin v9  |  No Cookie  |  by YURXZ{R}\n\n")
    sep('=')
    row("INFO", "STATUS")
    sep('-')
    row("[*] System", st_txt, YE)
    row("[M] Memory", f"Free: {mem} ({mpct}%)", GY)
    if mode: row("[~] Mode", " | ".join(mode), GY)
    sep('-')
    row("PACKAGE", "STATUS")
    sep('-')

    for a in accounts:
        st  = a.get("status", "?")
        mtd = a.get("method", "auto")
        lbl = mtd_labels.get(mtd, "[?]")
        col = GR
        if any(x in st for x in ["Restart","Launch","Wait","Cache","Stop","Loading","Cek","Detect"]):
            col = YE
        elif any(x in st for x in ["Error","Failed","Crash","Freeze","mati","putus"]):
            col = RE
        elif any(x in st for x in ["Idle","Pending"]):
            col = GY
        pkg = a.get('pkg', '?')
        row(f"  {lbl} {pkg}", st, col)

    sep('=')
    sys.stdout.write(f"\n{GY}  [q]=berhenti  [Ctrl+C]=force stop{R}\n")
    sys.stdout.flush()

# ==========================================================
#  MENU 1 — START AUTO REJOIN (tanpa cookie)
# ==========================================================
def menu_start_rejoin():
    if not check_root():
        print(f"{RE}Root access required!{R}")
        pause_auto(); return

    cfg  = load_cfg()
    pkgs = cfg.get("packages", [])

    # Auto detect kalau belum ada
    if not pkgs:
        print(f"{YE}Package belum diset, auto detecting...{R}")
        pkgs = find_installed_pkgs()
        if not pkgs:
            print(f"{RE}Tidak ada package Roblox ditemukan!{R}")
            pause_auto(); return
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
        pause_auto(); return

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

    last_wh = time.time()

    # -- Monitoring loop -----------------------------------
    try:
        while True:
            nxt_wh = ""
            if wh_url:
                diff = int(600 - (time.time() - last_wh))
                if diff <= 0:
                    _send_webhook_nocookie(wh_url, accounts)
                    last_wh = time.time()
                    diff = 600
                nxt_wh = f"WH {diff//60}m"

            for i, a in enumerate(accounts):
                draw_ui(accounts, "Monitoring", f"Check [{i+1}/{tot}]", nxt_wh)
                pkg  = a["pkg"]
                link = a["ps_link"]
                needs_rejoin = False
                reason = ""

                # == CEK 1: App masih running? ============
                if not is_running(pkg):
                    needs_rejoin = True
                    reason = "App mati / crash"
                    a["method"] = "pidof"

                else:
                    # == CEK 2-4: Deteksi dengan fallback =
                    a["status"] = "Detecting..."
                    draw_ui(accounts, "Monitoring", f"Check [{i+1}/{tot}]", nxt_wh)

                    ingame, activity, method = is_in_game(pkg)
                    a["method"] = method  # Tampilkan metode di UI

                    if not ingame:
                        # Toleransi loading / transisi
                        if a.get("loading_count", 0) < 3:
                            a["loading_count"] = a.get("loading_count", 0) + 1
                            a["status"] = f"⏳ Transisi? ({a['loading_count']}/3)"
                            continue
                        else:
                            needs_rejoin = True
                            reason = f"Tidak in-game ({activity or method})"
                            a["loading_count"] = 0
                    else:
                        a["loading_count"] = 0
                        protect_app(pkg)

                        # Status sesuai metode yang dipakai
                        if method == "activity":
                            a["status"] = f"In-game ✅ | {activity}"
                        elif method == "network":
                            a["status"] = "In-game ✅ | koneksi aktif"
                        elif method == "cpu":
                            a["status"] = "Running ✅ | CPU aktif"
                        else:
                            a["status"] = "Running ✅ | pidof"

                # -- Rejoin --------------------------------
                if needs_rejoin:
                    a["rejoin_count"] += 1
                    log(f"{pkg}: {reason} → Rejoin #{a['rejoin_count']}", "WARN")
                    a["status"] = f"⚠️ {reason}"
                    draw_ui(accounts, "Monitoring", f"Rejoin {pkg}", nxt_wh)

                    # Webhook notif
                    if wh_url:
                        _send_webhook_nocookie(wh_url, accounts,
                                               f"⚠️ Disconnect: {pkg}", 15158332)

                    # Stop → clear → launch
                    a["status"] = "Force stop..."
                    draw_ui(accounts, "Monitoring", f"Rejoin {pkg}", nxt_wh)
                    force_stop(pkg)

                    a["status"] = "Clear cache..."
                    draw_ui(accounts, "Monitoring", f"Rejoin {pkg}", nxt_wh)
                    clear_cache_safe(pkg)

                    a["status"] = "Relaunching..."
                    draw_ui(accounts, "Monitoring", f"Rejoin {pkg}", nxt_wh)
                    bounds = grid_bounds(a["index"], tot, sw, sh) if do_float else None
                    launch_game(link, pkg, bounds)

                    time.sleep(5)
                    if do_mute:   mute_roblox()
                    if do_lowgfx: set_low_graphics(pkg)
                    protect_app(pkg)

                    # Countdown wait start
                    for t in range(25, 0, -1):
                        a["status"] = f"Wait start ({t}s)"
                        draw_ui(accounts, "Monitoring", "Wait Launch", nxt_wh)
                        time.sleep(1)

                    a["status"] = f"Running ✅ (rejoin #{a['rejoin_count']})"
                    log(f"{pkg}: Rejoin #{a['rejoin_count']} selesai", "INFO")

                    if wh_url:
                        _send_webhook_nocookie(wh_url, accounts,
                                               f"✅ Rejoin OK: {pkg}", 3066993)

            # Simpan status
            try:
                with open(STATUS_FILE, "w") as f:
                    json.dump([{"pkg": x["pkg"], "status": x["status"],
                                "rejoin": x["rejoin_count"]} for x in accounts], f)
            except:
                pass

            # Countdown idle — cek tombol q untuk berhenti
            step = 2 if ARGS.low else 1
            import signal
            # Pastikan SIGINT tetap work
            signal.signal(signal.SIGINT, signal.default_int_handler)
            for t in range(interval, 0, -step):
                draw_ui(accounts, "Idle", f"Next: {t}s [q=stop]", nxt_wh)
                # Cek input non-blocking selama sleep
                try:
                    import select
                    tty_q = _open_tty()
                    src_q = tty_q if tty_q else sys.stdin
                    ready, _, _ = select.select([src_q], [], [], step)
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
                    time.sleep(step)

    except KeyboardInterrupt:
        print(f"\n{YE}[!] Dihentikan.{R}\n")

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
        pause_auto(); return
    print(f"{GR}Package ditemukan:{R}")
    for p in found:
        ok, out = run_root(f"dumpsys package {p} | grep versionName")
        ver = out.strip().replace("versionName=","").strip() if ok and out.strip() else "?"
        print(f"  {GR}✓{R} {p}  {GY}(v{ver}){R}")
    cfg["packages"] = found
    save_cfg(cfg)
    print(f"\n{GR}✓ {len(found)} package tersimpan ke config!{R}")
    pause_auto()

# ==========================================================
#  MENU 3 — SET PS LINK / GAME ID (SEMUA PACKAGE)
# ==========================================================
def menu_set_global_ps():
    cfg = load_cfg()
    print(f"\n{CY}[ Set PS Link / Game ID untuk Semua Package ]{R}")
    print(f"{GY}{'-'*get_term_width()}{R}")
    print(f"{GY}Format yang bisa diinput:{R}")
    print(f"  {WH}1. Game ID biasa     {GY}→ {GR}995679412{R}")
    print(f"  {WH}2. Roblox URI        {GY}→ {GR}roblox://placeId=995679412{R}")
    print(f"  {WH}3. Link game Roblox  {GY}→ {GR}https://www.roblox.com/games/995679412/...{R}")
    print(f"  {WH}4. Private Server    {GY}→ {GR}https://www.roblox.com/games/...?privateServerLinkCode=xxx{R}")
    print(f"{GY}{'-'*get_term_width()}{R}")
    current = cfg.get("global_ps_link","")
    if current:
        parsed = parse_launch_link(current)
        print(f"{GY}Saat ini : {current[:55]}{R}")
        print(f"{GY}Dikonversi: {parsed[:55]}{R}")
    print()
    link = inp_text(f"{YE}Masukkan PS Link / Game ID: {R}")
    if not link:
        print(f"{RE}Kosong!{R}"); pause_auto(); return
    parsed = parse_launch_link(link)
    print(f"\n{GY}Input    : {link[:55]}{R}")
    print(f"{GR}Dikonversi: {parsed[:55]}{R}")
    cfg["global_ps_link"] = link
    pkgs     = cfg.get("packages", find_installed_pkgs())
    ps_links = cfg.get("ps_links", {})
    for pkg in pkgs:
        ps_links[pkg] = link
        print(f"  {GR}✓{R} {pkg}")
    cfg["ps_links"] = ps_links
    save_cfg(cfg)
    print(f"\n{GR}✓ Tersimpan untuk semua package!{R}")
    pause_auto()

# ==========================================================
#  MENU 4 — SET PS LINK PER PACKAGE
# ==========================================================
def menu_set_per_pkg_ps():
    cfg  = load_cfg()
    pkgs = cfg.get("packages", find_installed_pkgs())
    print(f"\n{CY}[ Set PS Link / Game ID per Package ]{R}")
    print(f"{GY}{'-'*get_term_width()}{R}")
    print(f"{GY}Format yang bisa diinput:{R}")
    print(f"  {WH}1. Game ID biasa  {GY}→ {GR}995679412{R}")
    print(f"  {WH}2. Roblox URI     {GY}→ {GR}roblox://placeId=995679412{R}")
    print(f"  {WH}3. Link game      {GY}→ {GR}https://www.roblox.com/games/...{R}")
    print(f"  {WH}4. Private Server {GY}→ {GR}https://www.roblox.com/...?privateServerLinkCode=xxx{R}")
    print(f"{GY}{'-'*get_term_width()}{R}\n")
    ps_links = cfg.get("ps_links", {})
    for pkg in pkgs:
        current = ps_links.get(pkg,"")
        print(f"{CY}▶ {pkg}{R}")
        if current:
            print(f"  {GY}Saat ini: {current[:55]}{R}")
        val = inp_text(f"  {YE}Input baru (Enter skip): {R}")
        if val:
            parsed = parse_launch_link(val)
            print(f"  {GR}✓ Dikonversi → {parsed[:50]}{R}")
            ps_links[pkg] = val
        print()
    cfg["ps_links"] = ps_links
    cfg["packages"] = pkgs
    save_cfg(cfg)
    print(f"{GR}✓ PS Link per-package tersimpan!{R}")
    pause_auto()

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
    pause_auto()

# ==========================================================
#  MENU 6 — LIST CONFIG
# ==========================================================
def menu_list_config():
    cfg = load_cfg()
    print(f"\n{CY}{'='*get_term_width()}{R}")
    print(f"{CY}  LIST CONFIG{R}")
    print(f"{CY}{'='*get_term_width()}{R}")
    print(f"{YE}Packages ({len(cfg.get('packages',[]))}):{R}")
    for p in cfg.get("packages",[]):
        ps = cfg.get("ps_links",{}).get(p,"(belum diset)")
        running = is_running(p)
        status_str = f"{GR}Running{R}" if running else f"{RE}Mati{R}"
        print(f"  {GR}▶{R} {p}")
        print(f"       Status : {status_str}")
        print(f"       PS     : {ps[:60]}")
    print(f"\n{YE}Global PS Link:{R} {cfg.get('global_ps_link','(kosong)')[:60]}")
    print(f"{YE}Interval      :{R} {cfg.get('check_interval',35)}s")
    print(f"{YE}Restart Delay :{R} {cfg.get('restart_delay',10)}s")
    print(f"{YE}Floating      :{R} {'✅' if cfg.get('floating_window') else '❌'}")
    print(f"{YE}Auto Mute     :{R} {'✅' if cfg.get('auto_mute') else '❌'}")
    print(f"{YE}Low Grafik    :{R} {'✅' if cfg.get('auto_low_graphics') else '❌'}")
    print(f"{YE}Webhook       :{R} {cfg.get('webhook_url','(kosong)')[:50]}")
    print(f"{CY}{'='*get_term_width()}{R}")
    pause_auto()

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
    pause_auto()

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
    pause_auto()

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
    pause_auto()

# ==========================================================
#  MENU 12 — LIHAT LOG
# ==========================================================
def menu_lihat_log():
    print(f"\n{CY}[ Log Aktivitas (50 baris terakhir) ]{R}\n")
    log_path = LOG_FILE
    ok, out = run_root(f"tail -50 {log_path} 2>/dev/null")
    if ok and out:
        print(out)
    else:
        print(f"{GY}Log kosong atau belum ada.{R}")
    pause_auto()

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
        pause_auto(); return

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
    pause_auto()

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
        "12": menu_diagnostic,
        "13": menu_lihat_log,
    }

def countdown_before_menu(label, detik=10):
    """Countdown sebelum masuk menu — flush stdin dulu supaya tidak skip."""
    flush_stdin()
    print(f"\n  {GY}>> {WH}{label}{R}")
    for i in range(detik, 0, -1):
        sys.stdout.write(f"\r  {GY}Masuk dalam {i}s...{R}   ")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r" + " "*40 + "\r\n")
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
        "12": menu_diagnostic,
        "13": menu_lihat_log,
    }

    while True:
        print_banner()
        print(f"{GY}  Tip: 231 = urut Menu2,Menu3,Menu1{R}\n")
        c = inp(f"  {YE}Enter choice: {R}")

        if c.strip() == "14":
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

