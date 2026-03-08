import os
import sys
import json
import sqlite3
import subprocess
import shutil
import requests
import time
import math
import re
from pathlib import Path

CONFIG_FILE = "config.json"

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

def run_root_cmd(cmd):
    try:
        result = subprocess.run(['su', '-c', cmd], capture_output=True, text=True, timeout=10)
        out = (result.stdout or '') + '\n' + (result.stderr or '')
        return result.returncode == 0, out.strip()
    except Exception as e:
        return False, str(e)

# --- CONFIG CREATION FUNCTIONS ---
def check_package_installed(package_name):
    success, output = run_root_cmd(f'pm list packages')
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
        f'find {base_path} -type f -name "*cookie*" 2>/dev/null'
    ]
    
    for cmd in cmds:
        success, output = run_root_cmd(cmd)
        if success and output:
            for path in output.split('\n'):
                path = path.strip()
                if path and path not in found_paths and not path.endswith('-journal') and not path.endswith('.tmp'):
                    print(f"      → Found potential DB: {os.path.basename(path)}")
                    found_paths.append(path)
    if not found_paths:
        print("      ⚠️ No cookie files found.")
    return found_paths

def copy_database(db_path, temp_path):
    success, _ = run_root_cmd(f'cp "{db_path}" "{temp_path}" && chmod 666 "{temp_path}"')
    return success

def extract_cookie_chromium(db_path):
    temp_db = "/sdcard/temp_cookies_chromium.db"
    if not copy_database(db_path, temp_db): return None
    try:
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name, value FROM cookies WHERE (host_key LIKE '%roblox.com%' OR host_key LIKE '%www.roblox.com%') AND name = '.ROBLOSECURITY'")
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
    if not copy_database(db_path, temp_db): return None
    try:
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, value FROM moz_cookies WHERE host LIKE '%roblox.com%' AND name = '.ROBLOSECURITY'")
        result = cursor.fetchone()
        conn.close()
        run_root_cmd(f'rm "{temp_db}"')
        return result[1] if result else None
    except:
        run_root_cmd(f'rm "{temp_db}"')
        return None

def get_user_info(cookie):
    try:
        url = "https://users.roblox.com/v1/users/authenticated"
        response = requests.get(url, cookies={".ROBLOSECURITY": cookie}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('id'), data.get('name')
    except: pass
    return None, None

# --- CREATE CONFIG: tanpa input, langsung scan & simpan ---
def create_config():
    clear_screen()
    print_header()
    if not check_root():
        print("❌ Root access required!")
        print("\nTekan Ctrl+C untuk kembali ke menu.")
        time.sleep(3)
        return
        
    installed_browsers = find_roblox_packages()
    if not installed_browsers:
        print("\n❌ No Roblox apps found!")
        time.sleep(3)
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
            cookie = extract_cookie_firefox(db_path) if 'firefox' in package_name else extract_cookie_chromium(db_path)
            if cookie:
                print(f"   ✓ Cookie found! Package: {package_name}")
                uid, name = get_user_info(cookie)
                if uid:
                    print(f"   👤 User: {name} | 🆔 ID: {uid}\n")
                    found_accounts.append({
                        "name": name,
                        "user_id": uid,
                        "package": package_name,
                        "roblox_cookie": cookie
                    })
                else:
                    print("   ⚠️ Could not fetch user (invalid cookie?)\n")
                break
                
    if not found_accounts:
        # Scan gagal — coba ambil dari config lama atau buat template
        if current_config.get("accounts"):
            found_accounts = current_config["accounts"]
            print(f"📋 Pakai {len(found_accounts)} akun dari config lama.\n")
        else:
            found_accounts = [{
                "name": "EDIT_NAMA_AKUN",
                "user_id": 0,
                "package": "com.roblox.client",
                "roblox_cookie": "EDIT_COOKIE_DI_SINI"
            }]
            print("📋 Template akun kosong dibuat. Edit config.json lalu isi cookie.\n")
    else:
        print(f"✅ Found {len(found_accounts)} account(s)!\n")
    
    # Load config lama kalau ada (jaga webhook & settings)
    current_config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                current_config = json.load(f)
            print("📂 Config lama ditemukan, settings dipertahankan.")
        except: pass

    # Tambah ps_link ke setiap akun (ambil dari config lama kalau ada)
    new_accounts = []
    for acc in found_accounts:
        # Cari ps_link dari config lama berdasarkan user_id
        old_ps = "EDIT_PS_LINK_DI_CONFIG_JSON"
        for old_acc in current_config.get("accounts", []):
            if str(old_acc.get("user_id")) == str(acc["user_id"]):
                old_ps = old_acc.get("ps_link", old_ps)
                break
        acc["ps_link"] = old_ps
        new_accounts.append(acc)

    final_config = {
        "check_interval":    current_config.get("check_interval", 35),
        "restart_delay":     current_config.get("restart_delay", 15),
        "webhook_url":       current_config.get("webhook_url", ""),
        "floating_window":   current_config.get("floating_window", True),
        "auto_mute":         current_config.get("auto_mute", True),
        "auto_low_graphics": current_config.get("auto_low_graphics", True),
        "accounts":          new_accounts
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(final_config, f, indent=2)

    print("✅ Config saved!\n")
    print("=" * 50)
    print("📝 LANGKAH SELANJUTNYA:")
    print(f"   nano {CONFIG_FILE}")
    print("")
    print("   Ganti EDIT_PS_LINK_DI_CONFIG_JSON")
    print("   dengan PS Link game kamu.")
    print("")
    print("   Opsional: isi webhook_url untuk notif Discord.")
    print("=" * 50)
    print("\nTekan Ctrl+C untuk kembali ke menu.")
    time.sleep(5)

def edit_config():
    if not os.path.exists(CONFIG_FILE):
        print("No config file found! Please run 'Create Config' first.")
        time.sleep(2)
        return
    os.system(f"nano {CONFIG_FILE}")

# --- APP RUNNER FUNCTIONS ---
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
    r = idx // cols
    c = idx % cols
    return f"{c*cell_w},{r*cell_h},{(c+1)*cell_w},{(r+1)*cell_h}"

def get_memory_info():
    try:
        with open("/proc/meminfo", "r") as f:
            content = f.read()
            m_tot = re.search(r"MemTotal:\s+(\d+)\s+kB", content)
            m_av = re.search(r"MemAvailable:\s+(\d+)\s+kB", content)
            if not m_av: m_av = re.search(r"MemFree:\s+(\d+)\s+kB", content)
            if m_tot and m_av:
                tot = int(m_tot.group(1))
                av = int(m_av.group(1))
                return f"{av//1024}MB", int((av/tot)*100)
    except: pass
    return "N/A", 0

def draw_ui(accounts, sys_status, check_prog, next_wh=""):
    sys.stdout.write("\033[2J\033[H")
    C_RES, C_CYA, C_GRE, C_YEL, C_RED, C_GRY = "\033[0m", "\033[36m", "\033[32m", "\033[33m", "\033[31m", "\033[90m"
    
    mem, m_pct = get_memory_info()
    cols = 65
    c1 = 34
    c2 = cols - 4 - c1
    
    def trunc(s, l):
        s = str(s).replace('\n', '').replace('\r', '')
        return s[:l-1] + "." if len(s) > l else s
    def sep(l, m, r, c='─'):
        sys.stdout.write(f"{C_CYA}{l}{c*(c1+1)}{m}{c*(c2+1)}{r}{C_RES}\n")
    def row(t1, t2, col=C_RES):
        sys.stdout.write(f"{C_CYA}│{C_RES} {trunc(t1, c1):<{c1}}{C_CYA}│{C_RES} {col}{trunc(t2, c2):<{c2}}{C_RES}{C_CYA}│{C_RES}\n")
        
    sep('┌', '┬', '┐')
    row("PACKAGE", "STATUS")
    sep('├', '┼', '┤')
    
    sys_txt = check_prog if check_prog else sys_status
    if next_wh: sys_txt += f" | {next_wh}"
    row("System", sys_txt or "Idle", C_YEL)
    row("Memory", f"Free: {mem} ({m_pct}%)", C_GRY)
    sep('├', '┼', '┤')
    
    for a in accounts:
        st = a.get('status', 'Unknown')
        c = C_GRE
        if any(x in st for x in ['Restarting','Initializing','Waiting','Starting','Cache','Mute','Grafik']): c = C_YEL
        elif any(x in st for x in ['Error','Stopped','Failed','Crash','Freeze']): c = C_RED
        elif 'Checking' in st: c = C_GRY
        row(f"{a['package']} ({a.get('name', '?')})", st, c)
        
    sep('└', '┴', '┘')
    sys.stdout.write("\n\033[90m  Ctrl+C untuk berhenti\033[0m\n")
    sys.stdout.flush()

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
    except: pass
    return True, None

def open_ps_link(link, pkg, bounds=None):
    def try_launch(extras=""):
        c1 = f'am start {extras} -n {pkg}/com.roblox.client.ActivityProtocolLaunch -a android.intent.action.VIEW -d "{link}"'
        ok1, o1 = run_root_cmd(c1)
        if ok1 and "Error:" not in o1 and "does not exist" not in o1: return True
        
        c2 = f'am start {extras} -a android.intent.action.VIEW -d "{link}" -p {pkg}'
        ok2, o2 = run_root_cmd(c2)
        if ok2 and "Error:" not in o2 and "does not exist" not in o2: return True
        
        return False

    if bounds:
        flags = f"--windowingMode 5 --bounds {bounds}"
        if try_launch(flags):
            return True
    if try_launch(""):
        return True
    return False

def log_activity(msg, lvl="INFO"):
    try:
        with open("activity.log", "a") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] [{lvl}] {msg}\n")
    except: pass

# --- FITUR BARU ---
def clear_cache_safe(pkg):
    for cmd in [
        f"rm -rf /data/data/{pkg}/cache/",
        f"rm -rf /data/data/{pkg}/code_cache/",
        f"rm -rf /data/user/0/{pkg}/cache/*",
    ]:
        run_root_cmd(cmd)
    log_activity(f"Cache cleared (safe): {pkg}")

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
                            v = float(p.replace('%', ''))
                            if 0 <= v <= 100:
                                samples.append(v); break
                        except: pass
        time.sleep(3)
    if not samples: return False
    return (sum(samples) / len(samples)) < 0.5

def refresh_cookie(cookie):
    try:
        r = requests.get("https://www.roblox.com/",
                         cookies={".ROBLOSECURITY": cookie},
                         allow_redirects=True, timeout=8)
        new = r.cookies.get(".ROBLOSECURITY")
        if new and new != cookie:
            return new
    except: pass
    return cookie

def save_refreshed_cookie(uid, new_cookie):
    try:
        with open(CONFIG_FILE, 'r') as f: cfg = json.load(f)
        for acc in cfg.get("accounts", []):
            if str(acc.get("user_id")) == str(uid):
                acc["roblox_cookie"] = new_cookie
        with open(CONFIG_FILE, 'w') as f: json.dump(cfg, f, indent=2)
    except: pass

def mute_roblox():
    # Cara 1: media volume command
    run_root_cmd("media volume --stream 3 --set 0 2>/dev/null || true")
    # Cara 2: service call audio (lebih kompatibel)
    run_root_cmd("service call audio 3 i32 3 i32 0 i32 1 2>/dev/null || true")
    # Cara 3: set via settings
    run_root_cmd("settings put system volume_music 0 2>/dev/null || true")
    log_activity("Roblox muted")

def set_low_graphics(pkg):
    pref = f"/data/data/{pkg}/shared_prefs"
    ok, files = run_root_cmd(f"ls {pref} 2>/dev/null")
    if not ok: return
    for fname in files.split():
        if not fname.endswith(".xml"): continue
        ok2, content = run_root_cmd(f"cat {pref}/{fname}")
        if ok2 and "GraphicsQualityLevel" in content:
            run_root_cmd(
                f'sed -i \'s/name="GraphicsQualityLevel" value="[0-9]*"/name="GraphicsQualityLevel" value="1"/g\' {pref}/{fname}'
            )

def send_webhook(webhook_url, accounts):
    if not webhook_url: return
    
    local_img = os.path.join(os.getcwd(), "screen.png")
    temp_img = "/data/local/tmp/screen.png"
    ok, _ = run_root_cmd(f"screencap -p {temp_img} && cp {temp_img} {local_img} && chmod 666 {local_img}")
    
    embed_fields = []
    for a in accounts:
        embed_fields.append({
            "name": f"{a.get('name', '?')} | {a.get('package', '?')}",
            "value": f"**Status:** {a.get('status', '?')}",
            "inline": False
        })
        
    payload = {
        "embeds": [{
            "title": "Roblox Account Status",
            "color": 3447003,
            "fields": embed_fields,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }]
    }
    
    files = {}
    if ok and os.path.exists(local_img):
        f = open(local_img, "rb")
        files["file"] = ("screen.png", f, "image/png")
        payload["embeds"][0]["image"] = {"url": "attachment://screen.png"}
        
    try:
        if files:
            requests.post(webhook_url, data={"payload_json": json.dumps(payload)}, files=files, timeout=15)
        else:
            requests.post(webhook_url, json=payload, timeout=10)
    except: pass
    finally:
        if "file" in files: files["file"][1].close()

def start_rejoin_app():
    if not os.path.exists(CONFIG_FILE):
        print("Config file not found! Please run 'Create Config' first.")
        time.sleep(3)
        return
        
    if not check_root():
        print("Root access required!")
        time.sleep(3)
        return
        
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        
    accounts_cfg = config.get("accounts", [])
    if not accounts_cfg:
        print("No accounts configured.")
        time.sleep(2)
        return

    # Cek PS link belum diisi
    missing = [a for a in accounts_cfg if not a.get("ps_link") or a.get("ps_link") == "EDIT_PS_LINK_DI_CONFIG_JSON"]
    if missing:
        print(f"⚠️  PS Link belum diisi untuk {len(missing)} akun!")
        print(f"Edit dulu: nano {CONFIG_FILE}")
        print(f"Ganti EDIT_PS_LINK_DI_CONFIG_JSON dengan PS Link game.")
        time.sleep(5)
        return
        
    clear_screen()
    run_root_cmd("setenforce 0")
    
    interval      = config.get("check_interval", 35)
    restart_delay = config.get("restart_delay", 15)
    wh_url        = config.get("webhook_url", "")
    do_float      = config.get("floating_window", True)
    do_mute       = config.get("auto_mute", True)
    do_lowgfx     = config.get("auto_low_graphics", True)
    
    sw, sh = get_current_resolution()
    tot = len(accounts_cfg)
    
    accounts = []
    for i, a in enumerate(accounts_cfg):
        accounts.append({
            'index': i+1,
            'name': a.get('name', f"User {a.get('user_id')}"),
            'user_id': a.get('user_id'),
            'package': a.get('package'),
            'cookie': a.get('roblox_cookie'),
            'ps_link': a.get('ps_link'),
            'status': 'Pending Start',
            'expected_game': None,
            'freeze_count': 0
        })
        
    draw_ui(accounts, "Starting Up...", "")
    
    for i, acc in enumerate(accounts):
        pkg = acc['package']
        acc['status'] = 'Force stop...'
        draw_ui(accounts, "Launching Accounts", f"[{i+1}/{tot}]")
        run_root_cmd(f"am force-stop {pkg}")
        time.sleep(1)

        acc['status'] = 'Clear cache...'
        draw_ui(accounts, "Launching Accounts", f"[{i+1}/{tot}]")
        clear_cache_safe(pkg)

        acc['status'] = 'Launching...'
        draw_ui(accounts, "Launching Accounts", f"[{i+1}/{tot}]")
        bounds = get_grid_bounds(acc['index'], tot, sw, sh) if do_float else None
        if open_ps_link(acc['ps_link'], pkg, bounds):
            acc['status'] = 'Launched (Wait)'
        else:
            acc['status'] = 'Launch Failed'

        if acc['status'] == 'Launched (Wait)':
            time.sleep(3)
            if do_mute:   mute_roblox()
            if do_lowgfx:
                set_low_graphics(pkg)
                set_low_resolution()
            protect_app(pkg)
            
        if i < tot - 1:
            for t in range(restart_delay, 0, -1):
                draw_ui(accounts, "Launching Accounts", f"Next in {t}s")
                time.sleep(1)
                
    for t in range(10, 0, -1):
        draw_ui(accounts, "Initializing", f"Wait {t}s")
        time.sleep(1)
        
    for a in accounts:
        ingame, gid = check_user_presence(a['user_id'], a['cookie'])
        a['expected_game'] = gid
        a['status'] = "Online" if gid else "Waiting Game"
        
    last_wh = time.time()
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
                nxt_wh = f"WH in {wh_diff//60}m"
                
            for i, a in enumerate(accounts):
                draw_ui(accounts, "Monitoring", f"Check [{i+1}/{tot}]", nxt_wh)
                pkg  = a['package']
                uid  = a['user_id']
                cook = a['cookie']

                if not is_roblox_running(pkg):
                    needs_rejoin, reason = True, "App closed"
                else:
                    # Freeze detection
                    if is_frozen(pkg):
                        a['freeze_count'] += 1
                        if a['freeze_count'] >= 2:
                            needs_rejoin, reason = True, "Freeze"
                            a['freeze_count'] = 0
                        else:
                            a['status'] = f"Mungkin freeze ({a['freeze_count']}/2)"
                            continue
                    else:
                        a['freeze_count'] = 0

                    # Cookie check
                    uid_check, _ = get_user_info(cook)
                    if uid_check is None:
                        new_cook     = refresh_cookie(cook)
                        uid_check, _ = get_user_info(new_cook)
                        if uid_check:
                            a['cookie'] = new_cook
                            save_refreshed_cookie(uid, new_cook)
                            a['status'] = "Cookie refreshed"
                            log_activity(f"{a['name']}: cookie refreshed")
                            continue
                        else:
                            needs_rejoin, reason = True, "Cookie expired"
                    else:
                        ingame, cg = check_user_presence(uid, cook)
                        if not ingame:
                            needs_rejoin, reason = True, "Not in game"
                        elif a['expected_game'] and cg and str(cg) != str(a['expected_game']):
                            needs_rejoin, reason = True, "Server switch"
                        else:
                            needs_rejoin, reason = False, ""
                            if cg: a['expected_game'] = cg
                            a['status'] = "Online"
                            protect_app(pkg)
                        
                if needs_rejoin:
                    log_activity(f"{a['name']}: {reason}", "WARN")
                    a['status'] = f"Crash: {reason}"
                    
                    if wh_url:
                        draw_ui(accounts, "Webhook", "Sending Crash Status...")
                        send_webhook(wh_url, accounts)
                        
                    a['status'] = "Restarting..."
                    draw_ui(accounts, "Monitoring", f"Fix {a['name']}", nxt_wh)
                    
                    run_root_cmd(f"am force-stop {pkg}")
                    time.sleep(2)
                    clear_cache_safe(pkg)
                    open_ps_link(a['ps_link'], pkg, get_grid_bounds(a['index'], tot, sw, sh) if do_float else None)
                    time.sleep(5)
                    if do_mute:   mute_roblox()
                    if do_lowgfx:
                        set_low_graphics(pkg)
                        set_low_resolution()
                    protect_app(pkg)
                    
                    for t in range(25, 0, -1):
                        a['status'] = f"Wait Start ({t}s)"
                        draw_ui(accounts, "Monitoring", "Wait Launch", nxt_wh)
                        time.sleep(1)
                        
                    a['status'] = "Online"
                    a['expected_game'] = None
                    if wh_url:
                        send_webhook(wh_url, accounts)
                else:
                    a['status'] = "Online"
                    
            with open("status.json", "w") as f:
                json.dump([{'name': x['name'], 'status': x['status']} for x in accounts], f)
                
            for t in range(interval, 0, -1):
                draw_ui(accounts, "Idle", f"Next Check: {t}s", nxt_wh)
                time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h")
        restore_resolution()

def main():
    while True:
        clear_screen()
        print_header()
        print("  1. Create Config  (scan cookie otomatis)")
        print("  2. Start Rejoin App")
        print("  3. Edit Config (nano)")
        print("  4. Exit")
        print("\n" + "="*50)
        
        c = input("\nSelect an option: ").strip()
        if c == '1': create_config()
        elif c == '2': start_rejoin_app()
        elif c == '3': edit_config()
        elif c == '4':
            clear_screen()
            break

if __name__ == "__main__":
    main()
