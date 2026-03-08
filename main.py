#!/usr/bin/env python3
"""
Roblox Auto Rejoin by YURXZ
Android Rooted + Termux
"""

import os, sys, json, sqlite3, subprocess, requests, time, math, re, argparse, termios, tty
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument("--auto",      action="store_true")
parser.add_argument("--preventif", action="store_true")
parser.add_argument("--low",       action="store_true")
ARGS = parser.parse_args()

CONFIG_FILE = "config.json"

GR = "\033[32m"
YL = "\033[33m"
RD = "\033[31m"
CY = "\033[36m"
GY = "\033[90m"
MG = "\033[35m"
R  = "\033[0m"

# ── safe_input: reset terminal state sebelum baca input ──────────────────────
def safe_input(prompt=""):
    try:
        fd  = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[3] = new[3] | termios.ECHO | termios.ICANON
        termios.tcsetattr(fd, termios.TCSADRAIN, new)
    except Exception:
        pass
    sys.stdout.write(prompt)
    sys.stdout.flush()
    try:
        val = sys.stdin.readline()
        return val.rstrip("\n").strip()
    except EOFError:
        return ""

def clear_screen():
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.flush()

def print_header():
    print("\n" + "="*50)
    print("  Roblox Auto-Rejoin Tool  by YURXZ")
    print("="*50 + "\n")

def check_root():
    try:
        r = subprocess.run(["su", "-c", "id"], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False

def run_root_cmd(cmd, timeout=15):
    try:
        r   = subprocess.run(["su", "-c", cmd], capture_output=True, text=True, timeout=timeout)
        out = (r.stdout or "") + "\n" + (r.stderr or "")
        return r.returncode == 0, out.strip()
    except Exception as e:
        return False, str(e)

def log_activity(msg, lvl="INFO"):
    try:
        ts = datetime.now().strftime("%d/%m %H:%M:%S")
        with open("activity.log", "a") as f:
            f.write(f"[{ts}] [{lvl}] {msg}\n")
    except Exception:
        pass

# ── CONFIG ────────────────────────────────────────────────────────────────────
def check_package_installed(pkg):
    ok, out = run_root_cmd("pm list packages")
    return ok and pkg in out

def find_roblox_packages():
    found = {}
    ok, out = run_root_cmd("pm list packages")
    if ok:
        for line in out.splitlines():
            if "com.roblox" in line and "package:" in line:
                pkg = line.replace("package:", "").strip()
                found[pkg] = pkg
    if not found:
        found["com.roblox.client"] = "com.roblox.client"
    installed = {}
    print("Detecting installed Roblox apps...\n")
    for pkg in found:
        if check_package_installed(pkg):
            print(f"   OK {pkg}")
            installed[pkg] = pkg
    return installed

def find_cookie_databases(pkg):
    base  = f"/data/data/{pkg}"
    paths = []
    print(f"   Searching: {base}...")
    for cmd in [
        f'find {base} -type f -name "Cookies" 2>/dev/null',
        f'find {base} -type f -name "cookies.sqlite" 2>/dev/null',
        f'find {base} -type f -name "*cookie*" 2>/dev/null',
    ]:
        ok, out = run_root_cmd(cmd)
        if ok and out:
            for p in out.split("\n"):
                p = p.strip()
                if p and p not in paths and not p.endswith("-journal") and not p.endswith(".tmp"):
                    print(f"      -> {os.path.basename(p)}")
                    paths.append(p)
    if not paths:
        print("      No cookie files found.")
    return paths

def copy_db(src, dst):
    ok, _ = run_root_cmd(f'cp "{src}" "{dst}" && chmod 666 "{dst}"')
    return ok

def extract_cookie_chromium(db_path):
    tmp = "/sdcard/tmp_cookie_c.db"
    if not copy_db(db_path, tmp):
        return None
    try:
        conn = sqlite3.connect(tmp)
        cur  = conn.cursor()
        try:
            cur.execute("SELECT value FROM cookies WHERE host_key LIKE '%roblox.com%' AND name='.ROBLOSECURITY'")
            row = cur.fetchone()
        except Exception:
            try:
                cur.execute("SELECT value FROM cookies WHERE name='.ROBLOSECURITY'")
                row = cur.fetchone()
            except Exception:
                row = None
        conn.close()
        run_root_cmd(f'rm "{tmp}"')
        return row[0] if row else None
    except Exception:
        run_root_cmd(f'rm "{tmp}"')
        return None

def extract_cookie_firefox(db_path):
    tmp = "/sdcard/tmp_cookie_f.db"
    if not copy_db(db_path, tmp):
        return None
    try:
        conn = sqlite3.connect(tmp)
        cur  = conn.cursor()
        cur.execute("SELECT value FROM moz_cookies WHERE host LIKE '%roblox.com%' AND name='.ROBLOSECURITY'")
        row = cur.fetchone()
        conn.close()
        run_root_cmd(f'rm "{tmp}"')
        return row[0] if row else None
    except Exception:
        run_root_cmd(f'rm "{tmp}"')
        return None

def get_user_info(cookie):
    try:
        r = requests.get(
            "https://users.roblox.com/v1/users/authenticated",
            cookies={".ROBLOSECURITY": cookie},
            timeout=5,
        )
        if r.status_code == 200:
            d = r.json()
            return d.get("id"), d.get("name")
    except Exception:
        pass
    return None, None

def create_config():
    clear_screen()
    print_header()

    if not check_root():
        print("Root access required!")
        safe_input("\nPress Enter...")
        return

    installed = find_roblox_packages()
    if not installed:
        print("\nNo Roblox apps found!")
        safe_input("\nPress Enter...")
        return

    print("\nSearching for Roblox cookies...\n")
    found_accounts = []
    for pkg in installed:
        print(f"Checking {pkg}...")
        db_paths = find_cookie_databases(pkg)
        if not db_paths:
            print("   No database found")
            continue
        for db_path in db_paths:
            cookie = extract_cookie_firefox(db_path) if "firefox" in pkg else extract_cookie_chromium(db_path)
            if cookie:
                print("   Cookie found!")
                uid, name = get_user_info(cookie)
                if uid:
                    print(f"   User: {name} | ID: {uid}\n")
                    found_accounts.append({
                        "name": name, "user_id": uid,
                        "package": pkg, "roblox_cookie": cookie,
                    })
                else:
                    print("   Invalid cookie\n")
                break

    if not found_accounts:
        print("No cookies found.")
        safe_input("\nPress Enter...")
        return

    print(f"Found {len(found_accounts)} account(s)!\n")

    cur_cfg = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                cur_cfg = json.load(f)
        except Exception:
            pass

    cur_wh = cur_cfg.get("webhook_url", "")
    print(f"Current Webhook: {cur_wh[:50] if cur_wh else '(kosong)'}")
    wh       = safe_input("Enter Discord Webhook URL (Enter to keep): ")
    final_wh = wh if wh else cur_wh

    same = safe_input("Same PS Link for all? (Y/n): ").lower()
    if same == "" or same == "y":
        ps          = safe_input("Paste PS Link (Enter to skip): ")
        global_link = ps if ps else "EDIT_LINK_IN_CONFIG_JSON"
    else:
        global_link = None

    new_accounts = []
    for acc in found_accounts:
        if global_link is not None:
            acc["ps_link"] = global_link
        else:
            print(f"\nAccount: {acc['name']} ({acc['package']})")
            ps           = safe_input("   Paste PS Link: ")
            acc["ps_link"] = ps if ps else "EDIT_LINK_IN_CONFIG_JSON"
        new_accounts.append(acc)

    def_i      = cur_cfg.get("check_interval", 35)
    def_r      = cur_cfg.get("restart_delay", 15)
    def_float  = cur_cfg.get("floating_window", True)
    def_mute   = cur_cfg.get("auto_mute", True)
    def_lowgfx = cur_cfg.get("auto_low_graphics", True)

    i_val  = safe_input(f"Check Interval [keep {def_i}s]: ")
    r_val  = safe_input(f"Restart Delay  [keep {def_r}s]: ")
    fl     = safe_input(f"Floating window? (Y/n) [{'Y' if def_float else 'N'}]: ").lower()
    mu     = safe_input(f"Auto mute? (Y/n) [{'Y' if def_mute else 'N'}]: ").lower()
    gfx    = safe_input(f"Auto low grafik? (Y/n) [{'Y' if def_lowgfx else 'N'}]: ").lower()

    config = {
        "check_interval":    int(i_val) if i_val.isdigit() else def_i,
        "restart_delay":     int(r_val) if r_val.isdigit() else def_r,
        "webhook_url":       final_wh,
        "floating_window":   (fl != "n") if fl else def_float,
        "auto_mute":         (mu != "n") if mu else def_mute,
        "auto_low_graphics": (gfx != "n") if gfx else def_lowgfx,
        "accounts":          new_accounts,
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    print("\nConfig saved!\n")
    safe_input("Press Enter to return...")

def edit_config():
    if not os.path.exists(CONFIG_FILE):
        print("Config not found!")
        safe_input("\nPress Enter...")
        return
    os.system(f"nano {CONFIG_FILE}")

# ── RESOLUTION & GRID ─────────────────────────────────────────────────────────
def get_current_resolution():
    ok, out = run_root_cmd("wm size")
    if ok and out:
        m = re.search(r"(\d+)x(\d+)", out)
        if m:
            return int(m.group(1)), int(m.group(2))
    return 1080, 2400

def get_grid_bounds(index, total, sw, sh):
    cols   = math.ceil(math.sqrt(total))
    rows   = math.ceil(total / cols)
    cell_w = sw // cols
    cell_h = sh // rows
    idx    = index - 1
    r      = idx // cols
    c      = idx % cols
    return f"{c*cell_w},{r*cell_h},{(c+1)*cell_w},{(r+1)*cell_h}"

def get_memory_info():
    try:
        with open("/proc/meminfo") as f:
            content = f.read()
        tot = re.search(r"MemTotal:\s+(\d+)", content)
        av  = re.search(r"MemAvailable:\s+(\d+)", content)
        if not av:
            av = re.search(r"MemFree:\s+(\d+)", content)
        if tot and av:
            t = int(tot.group(1))
            a = int(av.group(1))
            return f"{a//1024}MB", int((a / t) * 100)
    except Exception:
        pass
    return "N/A", 0

# ── FITUR ─────────────────────────────────────────────────────────────────────
def clear_cache_safe(pkg):
    for cmd in [
        f"rm -rf /data/data/{pkg}/cache/",
        f"rm -rf /data/data/{pkg}/code_cache/",
        f"rm -rf /data/user/0/{pkg}/cache/*",
    ]:
        run_root_cmd(cmd)
    log_activity(f"Cache cleared: {pkg}")

def protect_app(pkg):
    ok, pids = run_root_cmd(f"pidof {pkg}")
    if ok and pids.strip():
        for pid in pids.strip().split():
            run_root_cmd(f"echo -1000 > /proc/{pid}/oom_score_adj")
            run_root_cmd(f"renice -19 -p {pid}")

def is_frozen(pkg):
    samples = []
    for _ in range(3):
        ok, out = run_root_cmd(f"top -bn1 | grep {pkg}", timeout=10)
        if ok and out:
            for line in out.splitlines():
                if pkg in line:
                    for p in line.split():
                        try:
                            v = float(p.replace("%", ""))
                            if 0 <= v <= 100:
                                samples.append(v)
                                break
                        except Exception:
                            pass
        time.sleep(3)
    if not samples:
        return False
    return (sum(samples) / len(samples)) < 0.5

def refresh_cookie(cookie):
    try:
        r = requests.get("https://www.roblox.com/", cookies={".ROBLOSECURITY": cookie},
                         allow_redirects=True, timeout=8)
        new = r.cookies.get(".ROBLOSECURITY")
        if new and new != cookie:
            return new
    except Exception:
        pass
    return cookie

def save_cookie(uid, new_cookie):
    try:
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        for a in cfg.get("accounts", []):
            if str(a.get("user_id")) == str(uid):
                a["roblox_cookie"] = new_cookie
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

def mute_roblox():
    run_root_cmd("media volume --stream 3 --set 0 2>/dev/null || true")
    log_activity("Roblox muted")

def set_low_graphics(pkg):
    pref = f"/data/data/{pkg}/shared_prefs"
    ok, files = run_root_cmd(f"ls {pref} 2>/dev/null")
    if not ok:
        return
    for fname in files.split():
        if not fname.endswith(".xml"):
            continue
        ok2, content = run_root_cmd(f"cat {pref}/{fname}")
        if ok2 and "GraphicsQualityLevel" in content:
            run_root_cmd(
                f'sed -i \'s/name="GraphicsQualityLevel" value="[0-9]*"/name="GraphicsQualityLevel" value="1"/g\' {pref}/{fname}'
            )
    log_activity(f"Low graphics: {pkg}")

# ── DRAW UI ───────────────────────────────────────────────────────────────────
def draw_ui(accounts, sys_status, check_prog, next_wh=""):
    clear_screen()
    mem, m_pct = get_memory_info()
    c1 = 36; c2 = 26

    def trunc(s, l):
        s = str(s).replace("\n", "").replace("\r", "")
        return s[:l-1] + "." if len(s) > l else s

    def sep(l, m, r, c="─"):
        print(f"{CY}{l}{c*(c1+1)}{m}{c*(c2+1)}{r}{R}")

    def row(t1, t2, col=R):
        print(f"{CY}|{R} {trunc(t1,c1):<{c1}} {CY}|{R} {col}{trunc(t2,c2):<{c2}}{R} {CY}|{R}")

    print(f"\n{MG}  ROBLOX AUTO REJOIN  by YURXZ{R}\n")
    sep("+", "+", "+", "-")
    row("PACKAGE / NAMA", "STATUS")
    sep("+", "+", "+", "-")

    sys_txt = check_prog if check_prog else sys_status
    if next_wh:
        sys_txt += f" | {next_wh}"
    row("System",  sys_txt or "Idle", YL)
    row("Memory",  f"Free: {mem} ({m_pct}%)", GY)

    mode = ("PREVENTIF " if ARGS.preventif else "") + ("LOW-PERF" if ARGS.low else "")
    if mode.strip():
        row("Mode", mode.strip(), GY)
    sep("+", "+", "+", "-")

    for a in accounts:
        st  = a.get("status", "?")
        col = GR
        if any(x in st for x in ["Restart", "Launch", "Wait", "Cache"]):
            col = YL
        elif any(x in st for x in ["Error", "Failed", "Crash", "Freeze"]):
            col = RD
        elif "Check" in st:
            col = GY
        row(f"  {a.get('package','?')} ({a.get('name','?')})", st, col)

    sep("+", "+", "+", "-")
    print(f"\n{GY}  Ctrl+C untuk berhenti{R}")

# ── MONITORING ────────────────────────────────────────────────────────────────
def is_roblox_running(pkg):
    ok, out = run_root_cmd(f"pidof {pkg}")
    if ok and out.strip():
        return True
    ok, out = run_root_cmd(f"ps -A | grep {pkg}")
    return ok and bool(out.strip())

def check_user_presence(uid, cookie):
    try:
        r = requests.post(
            "https://presence.roblox.com/v1/presence/users",
            json={"userIds": [uid]},
            cookies={".ROBLOSECURITY": cookie},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5,
        )
        if r.status_code == 200 and r.json().get("userPresences"):
            p = r.json()["userPresences"][0]
            return (p.get("userPresenceType") == 2), p.get("gameId")
    except Exception:
        pass
    return True, None

def open_ps_link(link, pkg, bounds=None):
    def try_launch(extras=""):
        cmd1 = f'am start {extras} -n {pkg}/com.roblox.client.ActivityProtocolLaunch -a android.intent.action.VIEW -d "{link}"'
        ok1, o1 = run_root_cmd(cmd1)
        if ok1 and "Error:" not in o1 and "does not exist" not in o1:
            return True
        cmd2 = f'am start {extras} -a android.intent.action.VIEW -d "{link}" -p {pkg}'
        ok2, o2 = run_root_cmd(cmd2)
        return ok2 and "Error:" not in o2

    if bounds:
        if try_launch(f"--windowingMode 5 --bounds {bounds}"):
            return True
    return try_launch("")

def send_webhook(url, accounts, title="Status Update", color=3447003):
    if not url:
        return
    local_img = os.path.join(os.getcwd(), "screen.png")
    temp_img  = "/data/local/tmp/screen.png"
    ok, _     = run_root_cmd(f"screencap -p {temp_img} && cp {temp_img} {local_img} && chmod 666 {local_img}")
    fields    = []
    for a in accounts:
        st = a.get("status", "?")
        em = "OK" if "Online" in st else "!!"
        fields.append({"name": f"{em} {a.get('name','?')} | {a.get('package','?')}", "value": f"Status: {st}", "inline": False})
    payload = {
        "embeds": [{
            "title": title, "color": color, "fields": fields,
            "footer": {"text": f"YURXZ Auto Rejoin - {time.strftime('%d/%m/%Y %H:%M:%S')}"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }]
    }
    fh = None
    files = {}
    if ok and os.path.exists(local_img):
        fh = open(local_img, "rb")
        files["file"] = ("screen.png", fh, "image/png")
        payload["embeds"][0]["image"] = {"url": "attachment://screen.png"}
    try:
        if files:
            requests.post(url, data={"payload_json": json.dumps(payload)}, files=files, timeout=15)
        else:
            requests.post(url, json=payload, timeout=10)
        log_activity("Webhook sent")
    except Exception as e:
        log_activity(f"Webhook error: {e}", "WARN")
    finally:
        if fh:
            fh.close()

# ── REJOIN APP ────────────────────────────────────────────────────────────────
def start_rejoin_app():
    if not os.path.exists(CONFIG_FILE):
        print("Config not found! Run Create Config first.")
        safe_input("\nPress Enter...")
        return
    if not check_root():
        print("Root required!")
        safe_input("\nPress Enter...")
        return

    with open(CONFIG_FILE) as f:
        config = json.load(f)

    accounts_cfg = config.get("accounts", [])
    if not accounts_cfg:
        print("No accounts configured.")
        time.sleep(2)
        return

    run_root_cmd("setenforce 0")

    interval      = 20 if ARGS.preventif else config.get("check_interval", 35)
    restart_delay = config.get("restart_delay", 15)
    wh_url        = config.get("webhook_url", "")
    do_float      = config.get("floating_window", True)
    do_mute       = config.get("auto_mute", True)
    do_lowgfx     = config.get("auto_low_graphics", True)
    if ARGS.low:
        interval = max(interval, 50)

    sw, sh = get_current_resolution()
    total  = len(accounts_cfg)

    accounts = []
    for i, a in enumerate(accounts_cfg):
        accounts.append({
            "index": i + 1,
            "name":  a.get("name", f"User{i+1}"),
            "user_id":       a.get("user_id"),
            "package":       a.get("package"),
            "cookie":        a.get("roblox_cookie"),
            "ps_link":       a.get("ps_link"),
            "status":        "Pending",
            "expected_game": None,
            "freeze_count":  0,
        })

    draw_ui(accounts, "Starting...", "")

    for i, acc in enumerate(accounts):
        pkg = acc["package"]
        acc["status"] = "Force stop..."
        draw_ui(accounts, "Launching", f"[{i+1}/{total}]")
        run_root_cmd(f"am force-stop {pkg}")
        time.sleep(1)

        acc["status"] = "Clear cache..."
        draw_ui(accounts, "Launching", f"[{i+1}/{total}]")
        clear_cache_safe(pkg)

        acc["status"] = "Launching..."
        draw_ui(accounts, "Launching", f"[{i+1}/{total}]")
        bounds = get_grid_bounds(acc["index"], total, sw, sh) if do_float else None
        ok     = open_ps_link(acc["ps_link"], pkg, bounds)
        acc["status"] = "Launched OK" if ok else "Launch Failed"

        if ok:
            time.sleep(3)
            if do_mute:   mute_roblox()
            if do_lowgfx: set_low_graphics(pkg)
            protect_app(pkg)

        if i < total - 1:
            for t in range(restart_delay, 0, -1):
                draw_ui(accounts, "Launching", f"Next in {t}s")
                time.sleep(1)

    for t in range(15, 0, -1):
        draw_ui(accounts, "Initializing", f"Wait {t}s")
        time.sleep(1)

    for a in accounts:
        ingame, gid       = check_user_presence(a["user_id"], a["cookie"])
        a["expected_game"] = gid
        a["status"]        = "Online" if ingame else "Waiting Game..."

    last_wh = time.time()

    try:
        while True:
            nxt_wh = ""
            if wh_url:
                diff = int(600 - (time.time() - last_wh))
                if diff <= 0:
                    send_webhook(wh_url, accounts)
                    last_wh = time.time()
                    diff    = 600
                nxt_wh = f"WH {diff//60}m"

            for i, a in enumerate(accounts):
                draw_ui(accounts, "Monitoring", f"Check [{i+1}/{total}]", nxt_wh)
                pkg  = a["package"]
                uid  = a["user_id"]
                cook = a["cookie"]
                needs_rejoin = False
                reason       = ""

                if not is_roblox_running(pkg):
                    needs_rejoin = True
                    reason       = "App closed"
                else:
                    if not ARGS.low and is_frozen(pkg):
                        a["freeze_count"] += 1
                        if a["freeze_count"] >= 2:
                            needs_rejoin      = True
                            reason            = "Freeze"
                            a["freeze_count"] = 0
                        else:
                            a["status"] = f"Mungkin freeze ({a['freeze_count']}/2)"
                            continue
                    else:
                        a["freeze_count"] = 0

                    uid_check, _ = get_user_info(cook)
                    if uid_check is None:
                        new_cook      = refresh_cookie(cook)
                        uid_check, _  = get_user_info(new_cook)
                        if uid_check:
                            a["cookie"] = new_cook
                            save_cookie(uid, new_cook)
                            a["status"] = "Cookie refreshed"
                            continue
                        else:
                            needs_rejoin = True
                            reason       = "Cookie expired"
                    else:
                        ingame, cg = check_user_presence(uid, cook)
                        if not ingame:
                            needs_rejoin = True
                            reason       = "Not in game"
                        elif a["expected_game"] and cg and str(cg) != str(a["expected_game"]):
                            needs_rejoin = True
                            reason       = "Server switch"
                        else:
                            if cg:
                                a["expected_game"] = cg
                            a["status"] = "Online"
                            protect_app(pkg)

                if needs_rejoin:
                    log_activity(f"{a['name']}: {reason}", "WARN")
                    a["status"] = f"Crash: {reason}"
                    if wh_url:
                        send_webhook(wh_url, accounts, f"Disconnect: {a['name']}", 15158332)

                    run_root_cmd(f"am force-stop {pkg}")
                    time.sleep(2)
                    clear_cache_safe(pkg)
                    bounds = get_grid_bounds(a["index"], total, sw, sh) if do_float else None
                    open_ps_link(a["ps_link"], pkg, bounds)
                    time.sleep(5)
                    if do_mute:   mute_roblox()
                    if do_lowgfx: set_low_graphics(pkg)
                    protect_app(pkg)

                    for t in range(25, 0, -1):
                        a["status"] = f"Wait Start ({t}s)"
                        draw_ui(accounts, "Rejoin", a["name"], nxt_wh)
                        time.sleep(1)

                    a["status"]        = "Online (rejoined)"
                    a["expected_game"] = None
                    if wh_url:
                        send_webhook(wh_url, accounts, f"Rejoin OK: {a['name']}", 3066993)

            try:
                with open("status.json", "w") as f:
                    json.dump([{"name": x["name"], "status": x["status"]} for x in accounts], f)
            except Exception:
                pass

            step = 2 if ARGS.low else 1
            for t in range(interval, 0, -step):
                draw_ui(accounts, "Idle", f"Next Check: {t}s", nxt_wh)
                time.sleep(step)

    except KeyboardInterrupt:
        print(f"\n{YL}Dihentikan.{R}\n")

# ── MAIN MENU ─────────────────────────────────────────────────────────────────
def main():
    if ARGS.auto:
        if not check_root():
            print("Root required!")
            sys.exit(1)
        start_rejoin_app()
        return

    while True:
        clear_screen()
        print_header()
        print("  1. Create Config")
        print("  2. Start Rejoin")
        print("  3. Start Rejoin --preventif (cek tiap 20s)")
        print("  4. Start Rejoin --low (hemat RAM)")
        print("  5. Edit Config (nano)")
        print("  6. Lihat Log")
        print("  7. Exit")
        print("\n" + "="*50)

        c = safe_input("\nSelect an option: ")
        if   c == "1": create_config()
        elif c == "2": start_rejoin_app()
        elif c == "3": ARGS.preventif = True; start_rejoin_app()
        elif c == "4": ARGS.low = True; start_rejoin_app()
        elif c == "5": edit_config()
        elif c == "6":
            os.system("tail -60 activity.log")
            safe_input("\nPress Enter...")
        elif c == "7":
            clear_screen()
            break

if __name__ == "__main__":
    main()
