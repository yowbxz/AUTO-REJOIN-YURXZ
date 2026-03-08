#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║   🍪 cookie_import.py — Import Cookie dari JSON     ║
║   Roblox Auto Rejoin by YURXZ                       ║
╚══════════════════════════════════════════════════════╝

Format file JSON yang didukung:

Format 1 — Array of accounts:
[
  {
    "name": "NamaAkun",
    "cookie": "_|WARNING:-...",
    "ps_link": "roblox://..."
  }
]

Format 2 — Object dengan key "accounts":
{
  "accounts": [
    {
      "name": "NamaAkun",
      "cookie": "_|WARNING:-...",
      "ps_link": "roblox://..."
    }
  ]
}

Format 3 — Single cookie string per baris (cookies.txt):
  Jalankan: python3 cookie_import.py cookies.txt
"""

import os, sys, json, requests, time

CONFIG_FILE = "config.json"

# ─── WARNA ────────────────────────────────────────────
R  = "\033[0m";  GR = "\033[0;32m"; YL = "\033[0;33m"
RD = "\033[0;31m"; CY = "\033[0;36m"; BL = "\033[1m"

def get_user_info(cookie):
    """Validasi cookie dan ambil info user dari Roblox API."""
    try:
        r = requests.get(
            "https://users.roblox.com/v1/users/authenticated",
            cookies={".ROBLOSECURITY": cookie},
            timeout=8
        )
        if r.status_code == 200:
            d = r.json()
            return d.get("id"), d.get("name")
        elif r.status_code == 401:
            return None, None  # Cookie invalid/expired
    except Exception as e:
        print(f"{YL}  ⚠ Request error: {e}{R}")
    return None, None

def load_existing_config():
    """Load config.json yang sudah ada."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "check_interval": 35,
        "restart_delay": 15,
        "webhook_url": "",
        "floating_window": True,
        "auto_mute": True,
        "auto_low_graphics": True,
        "accounts": [],
    }

def parse_import_file(filepath):
    """
    Parse file import. Dukung:
    - .json dengan format 1 atau 2
    - .txt dengan satu cookie per baris
    """
    cookies_raw = []  # List of dict: {name, cookie, ps_link, package}

    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".txt":
        # Satu cookie per baris
        with open(filepath, "r") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        for i, line in enumerate(lines, 1):
            cookies_raw.append({
                "name":    f"Akun_{i}",
                "cookie":  line,
                "ps_link": "",
                "package": "com.roblox.client",
            })
    else:
        # JSON
        with open(filepath, "r") as f:
            data = json.load(f)

        # Format 2: {"accounts": [...]}
        if isinstance(data, dict) and "accounts" in data:
            data = data["accounts"]

        # Format 1: [...]
        if isinstance(data, list):
            for i, item in enumerate(data, 1):
                cookie = (
                    item.get("cookie") or
                    item.get("roblox_cookie") or
                    item.get(".ROBLOSECURITY") or
                    ""
                )
                cookies_raw.append({
                    "name":    item.get("name") or item.get("username") or f"Akun_{i}",
                    "cookie":  cookie,
                    "ps_link": item.get("ps_link") or item.get("psLink") or "",
                    "package": item.get("package") or "com.roblox.client",
                })
        else:
            print(f"{RD}  ✗ Format JSON tidak dikenali.{R}")
            return []

    return cookies_raw

def main():
    print(f"\n{CY}{BL}══════════════════════════════════════{R}")
    print(f"{CY}{BL}  🍪 Cookie Importer  by YURXZ        {R}")
    print(f"{CY}{BL}══════════════════════════════════════{R}\n")

    # ── Pilih file ────────────────────────────────────
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = input(f"  Path file JSON/TXT: ").strip().strip('"')

    if not os.path.exists(filepath):
        print(f"{RD}  ✗ File tidak ditemukan: {filepath}{R}")
        sys.exit(1)

    print(f"\n{YL}  📂 Membaca: {filepath}{R}")
    try:
        raw_accounts = parse_import_file(filepath)
    except Exception as e:
        print(f"{RD}  ✗ Gagal parse file: {e}{R}")
        sys.exit(1)

    if not raw_accounts:
        print(f"{RD}  ✗ Tidak ada data di file.{R}")
        sys.exit(1)

    print(f"  → Ditemukan {len(raw_accounts)} entri\n")

    # ── Validasi cookie satu per satu ────────────────
    print(f"{YL}  🔍 Validasi cookie via Roblox API...{R}\n")
    valid_accounts = []
    for i, acc in enumerate(raw_accounts, 1):
        cookie = acc.get("cookie", "")
        name   = acc.get("name", f"Akun_{i}")
        print(f"  [{i}/{len(raw_accounts)}] {name}... ", end="", flush=True)

        if not cookie:
            print(f"{RD}✗ Cookie kosong{R}")
            continue

        uid, rblx_name = get_user_info(cookie)
        if uid:
            # Gunakan nama dari Roblox API kalau ada
            final_name = rblx_name or name
            print(f"{GR}✓ {final_name} (ID: {uid}){R}")
            valid_accounts.append({
                "name":          final_name,
                "user_id":       uid,
                "package":       acc.get("package", "com.roblox.client"),
                "roblox_cookie": cookie,
                "ps_link":       acc.get("ps_link", "EDIT_LINK_IN_CONFIG_JSON"),
            })
        else:
            print(f"{RD}✗ Cookie invalid / expired{R}")

        time.sleep(0.5)  # rate limit

    print()
    if not valid_accounts:
        print(f"{RD}  ✗ Tidak ada cookie yang valid.{R}")
        sys.exit(1)

    print(f"{GR}  ✅ {len(valid_accounts)} akun valid dari {len(raw_accounts)} entri{R}\n")

    # ── Tanya PS link kalau belum diisi ──────────────
    need_link = [a for a in valid_accounts if a["ps_link"] == "EDIT_LINK_IN_CONFIG_JSON"]
    if need_link:
        ans = input("  🔗 Ada akun tanpa PS Link. Isi satu link untuk semua? (Y/n): ").lower()
        if ans != 'n':
            gl = input("  Paste PS Link: ").strip()
            if gl:
                for a in valid_accounts:
                    if a["ps_link"] == "EDIT_LINK_IN_CONFIG_JSON":
                        a["ps_link"] = gl
        print()

    # ── Merge ke config.json ──────────────────────────
    config = load_existing_config()
    existing_ids = {str(a.get("user_id")) for a in config.get("accounts", [])}

    added = 0
    updated = 0
    for acc in valid_accounts:
        uid_str = str(acc["user_id"])
        if uid_str in existing_ids:
            # Update cookie yang sudah ada
            for ex in config["accounts"]:
                if str(ex.get("user_id")) == uid_str:
                    ex["roblox_cookie"] = acc["roblox_cookie"]
                    if acc["ps_link"] != "EDIT_LINK_IN_CONFIG_JSON":
                        ex["ps_link"] = acc["ps_link"]
            updated += 1
        else:
            config["accounts"].append(acc)
            existing_ids.add(uid_str)
            added += 1

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    print(f"{CY}{BL}══════════════════════════════════════{R}")
    print(f"{GR}  ✅ Import selesai!{R}")
    print(f"  Ditambah  : {GR}{added}{R} akun baru")
    print(f"  Diupdate  : {YL}{updated}{R} akun (cookie refresh)")
    print(f"  Total     : {len(config['accounts'])} akun di config.json")
    print(f"{CY}{BL}══════════════════════════════════════{R}\n")
    print(f"  Jalankan: {CY}python3 main.py{R}\n")

if __name__ == "__main__":
    main()
