#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║     🎮 Roblox Auto Rejoin — main.py                 ║
║     Android Rooted + Termux | by YURXZ              ║
╚══════════════════════════════════════════════════════╝
  - Auto cek status game tiap 35 detik
  - Auto reconnect / rejoin kalau disconnect
  - Freeze detection via CPU usage
  - Clear cache AMAN (tidak hapus login)
  - Cookie expired auto-refresh
  - Discord webhook + screenshot
  - Protect app (anti-kill)
  - Low performance mode (hemat RAM)
  - Auto mute sound Roblox
  - Auto low grafik Roblox
  - Auto floating window Roblox di atas Termux
  - --auto      : langsung mulai tanpa menu
  - --preventif : cek tiap 20 detik
  - --low       : low performance mode
"""

import os, sys, json, sqlite3, subprocess, shutil, requests, time, math, re, argparse
from pathlib import Path

# ─── ARGS ─────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Roblox Auto Rejoin by YURXZ")
parser.add_argument("--auto",      action="store_true", help="Langsung mulai tanpa menu")
parser.add_argument("--preventif", action="store_true", help="Cek tiap 20 detik")
parser.add_argument("--low",       action="store_true", help="Low performance mode")
ARGS = parser.parse_args()

CONFIG_FILE = "config.json"

# ══════════════════════════════════════════════════════
#  HELPERS DASAR
# ══════════════════════════════════════════════════════
def clear_screen():
    print("\033[H\033[2J", end="")
    sys.stdout.flush()

def print_header():
    print("\n" + "="*50)
    print("  🎮 Roblox Auto-Rejoin Tool  by YURXZ")
    print("="*50 + "\n")

def check_root():
    try:
        result = subprocess.run(['su', '-c', 'id'], capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def run_root_cmd(cmd, timeout=15):
    try:
        result = subprocess.run(['su', '-c', cmd],
                                capture_output=True, text=True, timeout=timeout)
        out = (result.stdout or '') + '\n' + (result.stderr or '')
        return result.returncode == 0, out.strip()
    except Exception as e:
        return False, str(e)

def log_activity(msg, lvl="INFO"):
    try:
        with open("activity.log", "a") as f:
            f.write(f"[{time.strftime('%d/%m %H:%M:%S')}] [{lvl}] {msg}\n")
    except:
        pass

def clean_input(prompt):
    print("\033[?25h", end="")
    sys.stdout.flush()
    try:
        return input(prompt).strip()
    except EOFError:
        return ""

# ══════════════════════════════════════════════════════
#  CONFIG — CREATE & EDIT
# ══════════════════════════════════════════════════════
def check_package_installed(package_name):
    success, output = run_root_cmd('pm list packages')
    return success and package_name in output

def find_roblox_packages():
    browsers = {}
    success, output = run_root_cmd('pm list packages')
    if success:
        for line in output.splitlines():
            if 'com.roblox' in line and 'package:' in line:
                pkg = line.replace('package:', '').strip()
                browsers[f"Roblox ({pkg})"] = pkg
    if not browsers:
        browsers['Roblox App'] = 'com.roblox.client'
    installed = {}
    print("🔍 Detecting installed Roblox apps...\n")
    for name, package in browsers.items():
        if check_package_installed(package):
            print(f"   ✓ {name}: Installed")
            installed[name] = package
    return installed

def find_cookie_databases(package_name):
    base_path = f"/data/data/{package_name}"
    found_paths = []
    print(f"   🔎 Searching inside: {base_path}...")
    cmds = [
        f'find {base_path} -type f -name "Cookies" 2>/dev/null',
        f'find {base_path} -type f -name "cookies.sqlite" 2>/dev/null',
        f'find {base_path} -type f -name "*cookie*" 2>/dev/null',
    ]
    for cmd in cmds:
        success, output = run_root_cmd(cmd)
        if success and output:
            for path in output.split('\n'):
                path = path.strip()
                if path and path not in found_paths \
                   and not path.endswith('-journal') \
                   and not path.endswith('.tmp'):
                    print(f"      → Found potential DB: {os.path.basename(path)}")
                    found_paths.append(path)
    if not found_paths:
        print("      ⚠️  No cookie files found.")
    return found_paths

def copy_database(db_path, temp_path):
    success, _ = run_root_cmd(f'cp "{db_path}" "{temp_path}" && chmod 666 "{temp_path}"')
    return success

def extract_cookie_chromium(db_path):
    temp_db = "/sdcard/temp_cookies_chromium.db"
    if not copy_database(db_path, temp_db):
        return None
    try:
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT name, value FROM cookies "
                "WHERE (host_key LIKE '%roblox.com%') AND name = '.ROBLOSECURITY'"
            )
            result = cursor.fetchone()
        except:
            try:
                cursor.execute("SELECT name, value FROM cookies WHERE name = '.ROBLOSECURITY'")
                result = cursor.fetchone()
            except:
                result = None
        conn.close()
        run_root_cmd(f'rm "{temp_db}"')
        return result[1] if result and len(result) > 1 else (result[0] if result else None)
    except:
        run_root_cmd(f'rm "{temp_db}"')
        return None

def extract_cookie_firefox(db_path):
    temp_db = "/sdcard/temp_cookies_firefox.db"
    if not copy_database(db_path, temp_db):
        return None
    try:
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, value FROM moz_cookies "
            "WHERE host LIKE '%roblox.com%' AND name = '.ROBLOSECURITY'"
        )
        result = cursor.fetchone()
        conn.close()
        run_root_cmd(f'rm "{temp_db}"')
        return result[1] if result else None
    except:
        run_root_cmd(f'rm "{temp_db}"')
        return None

def get_user_info(cookie):
    try:
        r = requests.get(
            "https://users.roblox.com/v1/users/authenticated",
            cookies={".ROBLOSECURITY": cookie},
            timeout=5
        )
        if r.status_code == 200:
            d = r.json()
            return d.get('id'), d.get('name')
        elif r.status_code == 401:
            return None, None  # Cookie expired
    except:
        pass
    return None, None

def create_config():
    clear_screen()
    print_header()
    if not check_root():
        print("❌ Root access required!")
        input("\nPress Enter to return...")
        return

    installed_browsers = find_roblox_packages()
    if not installed_browsers:
        print("\n❌ No Roblox apps found!")
        input("\nPress Enter to return...")
        return

    print("\n  🔎 Searching for Roblox cookies...\n")
    found_accounts = []
    for browser_name, package_name in installed_browsers.items():
        print(f"📱 Checking {browser_name}...")
        db_paths = find_cookie_databases(package_name)
        if not db_paths:
            print(f"   ✗ No database found")
            continue
        for db_path in db_paths:
            cookie = extract_cookie_firefox(db_path) \
                if 'firefox' in package_name \
                else extract_cookie_chromium(db_path)
            if cookie:
                print(f"   ✓ Cookie found! Package: {package_name}")
                uid, name = get_user_info(cookie)
                if uid:
                    print(f"   👤 User: {name} | 🆔 ID: {uid}\n")
                    found_accounts.append({
                        "name": name,
                        "user_id": uid,
                        "package": package_name,
                        "roblox_cookie": cookie,
                    })
                else:
                    print("   ⚠️  Could not fetch user (invalid cookie?)\n")
                break

    if not found_accounts:
        print("❌ No cookies found in installed apps.")
        input("\nPress Enter to return...")
        return

    print(f"✅ Found {len(found_accounts)} account(s)!\n")

    current_config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                current_config = json.load(f)
        except:
            pass

    current_webhook = current_config.get("webhook_url", "")
    print(f"Current Webhook: {current_webhook[:40]}..." if current_webhook else "Current Webhook: (kosong)")
    webhook_input = clean_input("Enter Discord Webhook URL (Enter to keep): ")
    final_webhook = webhook_input if webhook_input else current_webhook

    ps_mode = clean_input("🔗 Use same PS Link for all? (Y/n): ").lower()
    if not ps_mode: ps_mode = 'y'
    global_link = "EDIT_LINK_IN_CONFIG_JSON"
    if ps_mode == 'y':
        val = clean_input("Paste PS Link (Enter to skip): ")
        if val: global_link = val

    new_accounts = []
    for acc in found_accounts:
        ps_link = global_link
        if ps_mode != 'y':
            print(f"\n👤 Account: {acc['name']} ({acc['package']})")
            val = clean_input("   Paste PS Link for this account: ")
            if val: ps_link = val
        acc["ps_link"] = ps_link
        new_accounts.append(acc)

    def_interval  = current_config.get("check_interval", 35)
    def_restart   = current_config.get("restart_delay", 15)
    def_float     = current_config.get("floating_window", True)
    def_mute      = current_config.get("auto_mute", True)
    def_lowgfx    = current_config.get("auto_low_graphics", True)

    i_val  = clean_input(f"Check Interval [keep {def_interval}s]: ")
    r_val  = clean_input(f"Restart Delay  [keep {def_restart}s]: ")

    fl_inp = clean_input(f"Floating window? (Y/n) [keep {'Y' if def_float else 'N'}]: ").lower()
    do_float = (fl_inp != 'n') if fl_inp else def_float

    mu_inp = clean_input(f"Auto mute Roblox? (Y/n) [keep {'Y' if def_mute else 'N'}]: ").lower()
    do_mute = (mu_inp != 'n') if mu_inp else def_mute

    gfx_inp = clean_input(f"Auto low grafik? (Y/n) [keep {'Y' if def_lowgfx else 'N'}]: ").lower()
    do_lowgfx = (gfx_inp != 'n') if gfx_inp else def_lowgfx

    final_config = {
        "check_interval":    int(i_val) if i_val.isdigit() else def_interval,
        "restart_delay":     int(r_val) if r_val.isdigit() else def_restart,
        "webhook_url":       final_webhook,
        "floating_window":   do_float,
        "auto_mute":         do_mute,
        "auto_low_graphics": do_lowgfx,
        "accounts":          new_accounts,
    }

    with open(CONFIG_FILE, 'w') as f:
        json.dump(final_config, f, indent=2)
    print("\n✅ Config saved successfully!")
    time.sleep(2)

def edit_config():
    if not os.path.exists(CONFIG_FILE):
        print("No config file found! Please run 'Create Config' first.")
        input("\nPress Enter to return...")
        return
    print("Opening config.json in nano...")
    time.sleep(1)
    os.system(f"nano {CONFIG_FILE}")

# ══════════════════════════════════════════════════════
#  RESOLUTION & GRID
# ══════════════════════════════════════════════════════
def get_current_resolution():
    w, h = 1080, 2400
    success, output = run_root_cmd("dumpsys window displays")
    if success and output:
        m = re.search(r"cur=(\d+)x(\d+)", output)
        if m: return int(m.group(1)), int(m.group(2))
    success, output = run_root_cmd("wm size")
    if success and output:
        m = re.search(r"(\d+)x(\d+)", output)
        if m: return int(m.group(1)), int(m.group(2))
    return w, h

def get_grid_bounds(index, total, screen_w, screen_h):
    cols = math.ceil(math.sqrt(total))
    rows = math.ceil(total / cols)
    if screen_w > screen_h:
        while cols < rows:
            cols += 1
            rows = math.ceil(total / cols)
    cell_w = screen_w // cols
    cell_h = screen_h // rows
    idx = index - 1
    r   = idx // cols
    c   = idx % cols
    return f"{c*cell_w},{r*cell_h},{(c+1)*cell_w},{(r+1)*cell_h}"

# ══════════════════════════════════════════════════════
#  MEMORY INFO
# ══════════════════════════════════════════════════════
def get_memory_info():
    try:
        with open("/proc/meminfo", "r") as f:
            content = f.read()
        m_tot = re.search(r"MemTotal:\s+(\d+)\s+kB", content)
        m_av  = re.search(r"MemAvailable:\s+(\d+)\s+kB", content)
        if not m_av:
            m_av = re.search(r"MemFree:\s+(\d+)\s+kB", content)
        if m_tot and m_av:
            tot = int(m_tot.group(1))
            av  = int(m_av.group(1))
            return f"{av//1024}MB", int((av / tot) * 100)
    except:
        pass
    return "N/A", 0

# ══════════════════════════════════════════════════════
#  FITUR BARU: FREEZE DETECTION
# ══════════════════════════════════════════════════════
def get_cpu_usage(pkg):
    """Ambil CPU% proses Roblox untuk freeze detection."""
    ok, out = run_root_cmd(f"top -bn1 | grep {pkg}", timeout=10)
    if ok and out:
        for line in out.splitlines():
            if pkg in line:
                parts = line.split()
                for p in parts:
                    try:
                        val = float(p.replace('%', ''))
                        if 0 <= val <= 100:
                            return val
                    except:
                        pass
    return -1.0

def is_frozen(pkg):
    """
    Cek freeze: ambil 3 sample CPU tiap 3 detik.
    Kalau rata-rata < 0.5% padahal app running → freeze.
    """
    samples = []
    for _ in range(3):
        cpu = get_cpu_usage(pkg)
        if cpu >= 0:
            samples.append(cpu)
        time.sleep(3)
    if not samples:
        return False
    avg = sum(samples) / len(samples)
    return avg < 0.5

# ══════════════════════════════════════════════════════
#  FITUR BARU: CLEAR CACHE AMAN
# ══════════════════════════════════════════════════════
def clear_cache_safe(pkg):
    """
    Clear cache AMAN — TIDAK hapus login / data akun.
    Hanya hapus folder cache, code_cache, dan user cache.
    """
    cmds = [
        f"rm -rf /data/data/{pkg}/cache/",
        f"rm -rf /data/data/{pkg}/code_cache/",
        f"rm -rf /data/user/0/{pkg}/cache/*",
    ]
    for cmd in cmds:
        run_root_cmd(cmd)
    log_activity(f"Cache {pkg} dibersihkan (aman)", "INFO")

# ══════════════════════════════════════════════════════
#  FITUR BARU: COOKIE AUTO-REFRESH
# ══════════════════════════════════════════════════════
def refresh_cookie(old_cookie):
    """
    Coba refresh cookie Roblox yang expired.
    Return cookie baru kalau berhasil, cookie lama kalau gagal.
    """
    try:
        # Roblox kadang kirim cookie baru di header Set-Cookie saat request apapun
        r = requests.get(
            "https://www.roblox.com/",
            cookies={".ROBLOSECURITY": old_cookie},
            allow_redirects=True,
            timeout=8
        )
        new_cookie = r.cookies.get(".ROBLOSECURITY")
        if new_cookie and new_cookie != old_cookie:
            log_activity("Cookie berhasil di-refresh", "INFO")
            return new_cookie
    except:
        pass
    return old_cookie

def save_refreshed_cookie(user_id, new_cookie):
    """Simpan cookie baru ke config.json."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            cfg = json.load(f)
        for acc in cfg.get("accounts", []):
            if str(acc.get("user_id")) == str(user_id):
                acc["roblox_cookie"] = new_cookie
        with open(CONFIG_FILE, 'w') as f:
            json.dump(cfg, f, indent=2)
    except:
        pass

# ══════════════════════════════════════════════════════
#  FITUR BARU: PROTECT APP (anti-kill)
# ══════════════════════════════════════════════════════
def protect_app(pkg):
    """Set oom_score_adj → -1000 supaya sistem tidak kill proses Roblox."""
    ok, pid_out = run_root_cmd(f"pidof {pkg}")
    if ok and pid_out.strip():
        for pid in pid_out.strip().split():
            run_root_cmd(f"echo -1000 > /proc/{pid}/oom_score_adj")
            run_root_cmd(f"renice -19 -p {pid}")

# ══════════════════════════════════════════════════════
#  FITUR BARU: AUTO MUTE SOUND ROBLOX
# ══════════════════════════════════════════════════════
def mute_roblox(pkg):
    """
    Mute audio Roblox dengan set volume stream MUSIC ke 0.
    Tidak mute sistem / app lain.
    """
    # Cari UID package
    ok, out = run_root_cmd(f"dumpsys package {pkg} | grep userId")
    uid_app = None
    if ok:
        m = re.search(r"userId=(\d+)", out)
        if m:
            uid_app = m.group(1)

    # Turunkan volume via service call audio
    # Stream 3 = STREAM_MUSIC (dipakai game)
    run_root_cmd("media volume --stream 3 --set 0 2>/dev/null || true")
    log_activity(f"Roblox muted (stream music = 0)", "INFO")

# ══════════════════════════════════════════════════════
#  FITUR BARU: AUTO LOW GRAFIK ROBLOX
# ══════════════════════════════════════════════════════
def set_low_graphics(pkg):
    """
    Set grafik Roblox ke minimum lewat SharedPreferences.
    Cari file pref yang relevan dan patch GraphicsQualityLevel → 1.
    """
    pref_path = f"/data/data/{pkg}/shared_prefs"
    ok, files = run_root_cmd(f"ls {pref_path} 2>/dev/null")
    if not ok:
        return

    patched = 0
    for fname in files.split():
        fname = fname.strip()
        if not fname.endswith(".xml"):
            continue
        # Patch semua file pref yang punya GraphicsQualityLevel
        ok2, content = run_root_cmd(f"cat {pref_path}/{fname}")
        if ok2 and "GraphicsQualityLevel" in content:
            run_root_cmd(
                f"sed -i 's/<int name=\"GraphicsQualityLevel\" value=\"[0-9]*\""
                f"/<int name=\"GraphicsQualityLevel\" value=\"1\"/g' {pref_path}/{fname}"
            )
            patched += 1

    if patched:
        log_activity(f"Low grafik diterapkan ({patched} file pref)", "INFO")
    else:
        log_activity("GraphicsQualityLevel tidak ditemukan di pref (mungkin belum pernah buka settings)", "DEBUG")

# ══════════════════════════════════════════════════════
#  FITUR BARU: FLOATING WINDOW
# ══════════════════════════════════════════════════════
def set_floating_window(pkg, ps_link, index, total, sw, sh):
    """
    Launch Roblox dalam mode floating (freeform) dengan grid bounds otomatis.
    Layout grid menyesuaikan jumlah akun — mirip Kaeru Tools.
    """
    bounds = get_grid_bounds(index, total, sw, sh)
    flags  = f"--windowingMode 5 --bounds {bounds}"

    # Coba launch dengan freeform mode
    cmd1 = (
        f'am start {flags} '
        f'-n {pkg}/com.roblox.client.ActivityProtocolLaunch '
        f'-a android.intent.action.VIEW -d "{ps_link}"'
    )
    ok1, o1 = run_root_cmd(cmd1)
    if ok1 and "Error:" not in o1 and "does not exist" not in o1:
        log_activity(f"Floating launch akun {index}: bounds={bounds}", "INFO")
        return True, bounds

    # Fallback: launch biasa pakai intent VIEW
    cmd2 = f'am start -a android.intent.action.VIEW -d "{ps_link}" -p {pkg}'
    ok2, _ = run_root_cmd(cmd2)
    log_activity(f"Floating gagal, fallback normal launch akun {index}", "WARN")
    return ok2, bounds

# ══════════════════════════════════════════════════════
#  DRAW UI
# ══════════════════════════════════════════════════════
def draw_ui(accounts, sys_status, check_prog, next_wh=""):
    sys.stdout.write("\033[2J\033[H\033[?25l")
    C_RES = "\033[0m"; C_CYA = "\033[36m"; C_GRE = "\033[32m"
    C_YEL = "\033[33m"; C_RED = "\033[31m"; C_GRY = "\033[90m"
    C_MGA = "\033[35m"

    mem, m_pct = get_memory_info()
    cols = 68; c1 = 36; c2 = cols - c1 - 5

    def trunc(s, l):
        s = str(s).replace('\n', '').replace('\r', '')
        return s[:l-1] + "." if len(s) > l else s

    def sep(l, m, r, c='─'):
        sys.stdout.write(f"{C_CYA}{l}{c*(c1+1)}{m}{c*(c2+1)}{r}{C_RES}\n")

    def row(t1, t2, col=C_RES):
        sys.stdout.write(
            f"{C_CYA}│{C_RES} {trunc(t1, c1):<{c1}} "
            f"{C_CYA}│{C_RES} {col}{trunc(t2, c2):<{c2}}{C_RES} {C_CYA}│{C_RES}\n"
        )

    # Header
    sys.stdout.write(f"\n{C_MGA}  🎮 ROBLOX AUTO REJOIN  by YURXZ{C_RES}\n\n")
    sep('┌', '┬', '┐')
    row("PACKAGE / NAMA", "STATUS")
    sep('├', '┼', '┤')

    # System rows
    sys_txt = check_prog if check_prog else sys_status
    if next_wh: sys_txt += f" | {next_wh}"
    mode_txt = ("PREVENTIF " if ARGS.preventif else "") + ("LOW-PERF" if ARGS.low else "")
    row("⚙  System", sys_txt or "Idle", C_YEL)
    row("💾 Memory",  f"Free: {mem} ({m_pct}%)", C_GRY)
    if mode_txt:
        row("🔧 Mode", mode_txt.strip(), C_GRY)
    sep('├', '┼', '┤')

    for a in accounts:
        st  = a.get('status', 'Unknown')
        col = C_GRE
        if any(x in st for x in ['Restarting', 'Launching', 'Waiting', 'Init', 'Cache', 'Mute', 'Grafik']):
            col = C_YEL
        elif any(x in st for x in ['Error', 'Failed', 'Crash', 'Freeze']):
            col = C_RED
        elif any(x in st for x in ['Checking', 'Idle']):
            col = C_GRY
        row(f"  {a.get('package','?')} ({a.get('name','?')})", st, col)

    sep('└', '┴', '┘')
    sys.stdout.write(f"\n{C_GRY}  [Ctrl+C untuk berhenti]{C_RES}\n")
    sys.stdout.flush()

# ══════════════════════════════════════════════════════
#  APP RUNNER — CEK APP & PRESENCE
# ══════════════════════════════════════════════════════
def is_roblox_running(pkg):
    ok, out = run_root_cmd(f"pidof {pkg}")
    if ok and out.strip(): return True
    ok, out = run_root_cmd(f"ps -A | grep {pkg}")
    return ok and bool(out.strip())

def check_user_presence(uid, cookie):
    try:
        r = requests.post(
            "https://presence.roblox.com/v1/presence/users",
            json={'userIds': [uid]},
            cookies={".ROBLOSECURITY": cookie} if cookie else {},
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=5
        )
        if r.status_code == 200 and r.json().get('userPresences'):
            p = r.json()['userPresences'][0]
            return (p.get('userPresenceType') == 2), p.get('gameId')
    except:
        pass
    return True, None

# ══════════════════════════════════════════════════════
#  LAUNCH PS LINK (dengan atau tanpa floating)
# ══════════════════════════════════════════════════════
def open_ps_link(link, pkg, bounds=None):
    def try_launch(extras=""):
        c1 = (
            f'am start {extras} -n {pkg}/com.roblox.client.ActivityProtocolLaunch '
            f'-a android.intent.action.VIEW -d "{link}"'
        )
        ok1, o1 = run_root_cmd(c1)
        if ok1 and "Error:" not in o1 and "does not exist" not in o1:
            return True
        c2 = f'am start {extras} -a android.intent.action.VIEW -d "{link}" -p {pkg}'
        ok2, o2 = run_root_cmd(c2)
        return ok2 and "Error:" not in o2 and "does not exist" not in o2

    if bounds:
        if try_launch(f"--windowingMode 5 --bounds {bounds}"):
            return True
    return try_launch("")

# ══════════════════════════════════════════════════════
#  WEBHOOK + SCREENSHOT
# ══════════════════════════════════════════════════════
def send_webhook(webhook_url, accounts, title="📊 Status Update", color=3447003):
    if not webhook_url:
        return

    local_img = os.path.join(os.getcwd(), "screen.png")
    temp_img  = "/data/local/tmp/screen.png"
    ok, _     = run_root_cmd(
        f"screencap -p {temp_img} && cp {temp_img} {local_img} && chmod 666 {local_img}"
    )

    embed_fields = []
    for a in accounts:
        st    = a.get('status', '?')
        emoji = "🟢" if "Online" in st else ("🔴" if any(x in st for x in ["Error","Crash","Failed"]) else "🟡")
        embed_fields.append({
            "name":   f"{emoji} {a.get('name','?')} | {a.get('package','?')}",
            "value":  f"**Status:** {st}",
            "inline": False,
        })

    payload = {
        "embeds": [{
            "title":     title,
            "color":     color,
            "fields":    embed_fields,
            "footer":    {"text": f"YURXZ Auto Rejoin • {time.strftime('%d/%m/%Y %H:%M:%S')}"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }]
    }

    files    = {}
    f_handle = None
    if ok and os.path.exists(local_img):
        f_handle = open(local_img, "rb")
        files["file"] = ("screen.png", f_handle, "image/png")
        payload["embeds"][0]["image"] = {"url": "attachment://screen.png"}

    try:
        if files:
            requests.post(
                webhook_url,
                data={"payload_json": json.dumps(payload)},
                files=files, timeout=15
            )
        else:
            requests.post(webhook_url, json=payload, timeout=10)
        log_activity("Webhook terkirim", "INFO")
    except Exception as e:
        log_activity(f"Webhook gagal: {e}", "WARN")
    finally:
        if f_handle:
            f_handle.close()

# ══════════════════════════════════════════════════════
#  MAIN REJOIN LOOP
# ══════════════════════════════════════════════════════
def start_rejoin_app():
    if not os.path.exists(CONFIG_FILE):
        print("Config file not found! Jalankan 'Create Config' dulu.")
        input("\nPress Enter to return...")
        return

    if not check_root():
        print("Root access required!")
        input("\nPress Enter to return...")
        return

    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

    accounts_cfg = config.get("accounts", [])
    if not accounts_cfg:
        print("No accounts configured.")
        time.sleep(2)
        return

    clear_screen()
    run_root_cmd("setenforce 0")   # Matikan SELinux enforce sementara

    # Ambil setting dari config & args
    interval      = 20 if ARGS.preventif else config.get("check_interval", 35)
    restart_delay = config.get("restart_delay", 15)
    wh_url        = config.get("webhook_url", "")
    do_float      = config.get("floating_window", True)
    do_mute       = config.get("auto_mute", True)
    do_lowgfx     = config.get("auto_low_graphics", True)

    if ARGS.low:
        interval = max(interval, 50)  # hemat CPU: tambah jeda

    sw, sh = get_current_resolution()
    tot    = len(accounts_cfg)

    accounts = []
    for i, a in enumerate(accounts_cfg):
        accounts.append({
            'index':          i + 1,
            'name':           a.get('name', f"User {a.get('user_id')}"),
            'user_id':        a.get('user_id'),
            'package':        a.get('package'),
            'cookie':         a.get('roblox_cookie'),
            'ps_link':        a.get('ps_link'),
            'status':         'Pending Start',
            'expected_game':  None,
            'freeze_count':   0,
        })

    draw_ui(accounts, "Starting Up...", "")

    # ── LAUNCH AWAL ─────────────────────────────────────
    for i, acc in enumerate(accounts):
        pkg = acc['package']
        acc['status'] = 'Force stop...'
        draw_ui(accounts, "Launching Accounts", f"[{i+1}/{tot}]")

        run_root_cmd(f"am force-stop {pkg}")
        time.sleep(1)

        # Clear cache AMAN sebelum launch
        acc['status'] = 'Clear cache...'
        draw_ui(accounts, "Launching Accounts", f"[{i+1}/{tot}]")
        clear_cache_safe(pkg)

        # Launch dengan / tanpa floating
        acc['status'] = 'Launching...'
        draw_ui(accounts, "Launching Accounts", f"[{i+1}/{tot}]")

        if do_float:
            bounds = get_grid_bounds(acc['index'], tot, sw, sh)
            success = open_ps_link(acc['ps_link'], pkg, bounds)
        else:
            bounds  = None
            success = open_ps_link(acc['ps_link'], pkg)

        acc['status'] = 'Launched ✓' if success else 'Launch Failed ✗'

        if success:
            # Mute & low grafik langsung setelah launch
            if do_mute:
                acc['status'] = 'Muting...'
                draw_ui(accounts, "Launching Accounts", f"[{i+1}/{tot}]")
                mute_roblox(pkg)

            if do_lowgfx:
                acc['status'] = 'Low grafik...'
                draw_ui(accounts, "Launching Accounts", f"[{i+1}/{tot}]")
                set_low_graphics(pkg)

            # Protect anti-kill
            time.sleep(3)
            protect_app(pkg)

        if i < tot - 1:
            for t in range(restart_delay, 0, -1):
                draw_ui(accounts, "Launching Accounts", f"Next in {t}s")
                time.sleep(1)

    # Tunggu semua load
    for t in range(15, 0, -1):
        draw_ui(accounts, "Initializing", f"Wait {t}s")
        time.sleep(1)

    # Presence awal
    for a in accounts:
        ingame, gid       = check_user_presence(a['user_id'], a['cookie'])
        a['expected_game'] = gid
        a['status']        = "Online ✅" if ingame else "Waiting Game..."

    last_wh = time.time()

    # ── MONITORING LOOP ─────────────────────────────────
    try:
        while True:
            nxt_wh = ""
            if wh_url:
                wh_diff = int(600 - (time.time() - last_wh))
                if wh_diff <= 0:
                    draw_ui(accounts, "Webhook", "Sending Update...")
                    send_webhook(wh_url, accounts)
                    last_wh = time.time()
                    wh_diff = 600
                nxt_wh = f"WH {wh_diff//60}m"

            for i, a in enumerate(accounts):
                draw_ui(accounts, "Monitoring", f"Check [{i+1}/{tot}]", nxt_wh)
                pkg  = a['package']
                uid  = a['user_id']
                cook = a['cookie']

                needs_rejoin = False
                reason       = ""

                # ── 1. Cek app running ─────────────────
                if not is_roblox_running(pkg):
                    needs_rejoin = True
                    reason       = "App closed"

                else:
                    # ── 2. Freeze detection ───────────
                    if not ARGS.low:
                        a['status'] = f"Checking freeze..."
                        draw_ui(accounts, "Monitoring", f"Check [{i+1}/{tot}]", nxt_wh)
                        if is_frozen(pkg):
                            a['freeze_count'] += 1
                            if a['freeze_count'] >= 2:
                                needs_rejoin       = True
                                reason             = "Freeze terdeteksi"
                                a['freeze_count']  = 0
                            else:
                                a['status'] = f"⚠️ Mungkin freeze ({a['freeze_count']}/2)"
                                continue
                        else:
                            a['freeze_count'] = 0

                    # ── 3. Cookie check ───────────────
                    uid_check, _ = get_user_info(cook)
                    if uid_check is None:
                        log_activity(f"{a['name']}: Cookie expired, refresh...", "WARN")
                        a['status'] = "Cookie refresh..."
                        draw_ui(accounts, "Monitoring", f"Cookie [{i+1}/{tot}]", nxt_wh)
                        new_cook = refresh_cookie(cook)
                        uid_check, _ = get_user_info(new_cook)
                        if uid_check:
                            a['cookie'] = new_cook
                            save_refreshed_cookie(uid, new_cook)
                            log_activity(f"{a['name']}: Cookie berhasil di-refresh", "INFO")
                            a['status'] = "Cookie refreshed ✅"
                            continue
                        else:
                            needs_rejoin = True
                            reason       = "Cookie expired (gagal refresh)"
                    else:
                        # ── 4. Presence check ─────────
                        ingame, cg = check_user_presence(uid, cook)
                        if not ingame:
                            needs_rejoin = True
                            reason       = "Not in game"
                        elif a['expected_game'] and cg and str(cg) != str(a['expected_game']):
                            needs_rejoin = True
                            reason       = "Server switch"
                        else:
                            if cg: a['expected_game'] = cg
                            a['status'] = "Online ✅"
                            protect_app(pkg)

                # ── REJOIN ────────────────────────────
                if needs_rejoin:
                    log_activity(f"{a['name']}: {reason} → Rejoin!", "WARN")
                    a['status'] = f"⚠️ {reason}"

                    if wh_url:
                        draw_ui(accounts, "Webhook", f"Crash: {a['name']}")
                        send_webhook(wh_url, accounts,
                                     f"⚠️ Disconnect: {a['name']}", 15158332)

                    # Force stop
                    a['status'] = "Force stop..."
                    draw_ui(accounts, "Monitoring", f"Rejoin {a['name']}", nxt_wh)
                    run_root_cmd(f"am force-stop {pkg}")
                    time.sleep(2)

                    # Clear cache AMAN
                    a['status'] = "Clear cache..."
                    draw_ui(accounts, "Monitoring", f"Rejoin {a['name']}", nxt_wh)
                    clear_cache_safe(pkg)

                    # Relaunch
                    a['status'] = "Relaunching..."
                    draw_ui(accounts, "Monitoring", f"Rejoin {a['name']}", nxt_wh)
                    if do_float:
                        bounds = get_grid_bounds(a['index'], tot, sw, sh)
                        open_ps_link(a['ps_link'], pkg, bounds)
                    else:
                        open_ps_link(a['ps_link'], pkg)

                    # Mute & low grafik ulang setelah rejoin
                    time.sleep(5)
                    if do_mute:   mute_roblox(pkg)
                    if do_lowgfx: set_low_graphics(pkg)
                    protect_app(pkg)

                    for t in range(25, 0, -1):
                        a['status'] = f"Wait Start ({t}s)"
                        draw_ui(accounts, "Monitoring", "Wait Launch", nxt_wh)
                        time.sleep(1)

                    a['status']        = "Online ✅ (rejoined)"
                    a['expected_game'] = None

                    if wh_url:
                        send_webhook(wh_url, accounts,
                                     f"✅ Rejoin berhasil: {a['name']}", 3066993)

            # Simpan status
            try:
                with open("status.json", "w") as f:
                    json.dump([{'name': x['name'], 'status': x['status']}
                               for x in accounts], f)
            except:
                pass

            # Countdown idle
            step = 2 if ARGS.low else 1
            for t in range(interval, 0, -step):
                draw_ui(accounts, "Idle", f"Next Check: {t}s", nxt_wh)
                time.sleep(step)

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h")
        print("\n\033[33m[!] Dihentikan.\033[0m\n")

# ══════════════════════════════════════════════════════
#  MAIN MENU
# ══════════════════════════════════════════════════════
def main():
    # --auto: langsung mulai tanpa menu
    if ARGS.auto:
        if not check_root():
            print("❌ Root required!")
            sys.exit(1)
        log_activity("Mulai dengan flag --auto", "INFO")
        start_rejoin_app()
        return

    while True:
        clear_screen()
        print_header()
        print("  1. Create Config  (scan cookie otomatis)")
        print("  2. Start Rejoin")
        print("  3. Start Rejoin --preventif (cek tiap 20s)")
        print("  4. Start Rejoin --low (hemat RAM/CPU)")
        print("  5. Edit Config (nano)")
        print("  6. Lihat Log")
        print("  7. Exit")
        print("\n" + "="*50)

        c = input("\nSelect an option: ").strip()
        if c == '1':
            create_config()
        elif c == '2':
            start_rejoin_app()
        elif c == '3':
            ARGS.preventif = True
            start_rejoin_app()
        elif c == '4':
            ARGS.low = True
            start_rejoin_app()
        elif c == '5':
            edit_config()
        elif c == '6':
            os.system("tail -60 activity.log")
            input("\nPress Enter...")
        elif c == '7':
            clear_screen()
            break

if __name__ == "__main__":
    main()
