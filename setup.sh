#!/bin/bash
# YURXZ Rejoin v9 — setup.sh

RED='\033[0;31m'; YEL='\033[0;33m'; GRE='\033[0;32m'
CYA='\033[0;36m'; RES='\033[0m'; MGA='\033[0;35m'; GRY='\033[0;37m'

DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$DIR"

W=$(tput cols 2>/dev/null || echo 44)
[ "$W" -lt 30 ] && W=30
SEP=$(printf '=%.0s' $(seq 1 $W))
SEP2=$(printf '-%.0s' $(seq 1 $W))

pr() { printf "${2:-$RES}  %-$((W-2))s${RES}\n" "$1"; }

clear
echo -e "${CYA}${SEP}${RES}"
pr "YURXZ Rejoin v9  --  Setup" "$MGA"
pr "Android Rooted + Termux  by YURXZ" "$GRY"
echo -e "${CYA}${SEP}${RES}"; echo ""

# [1/5] Root
pr "[1/5] Cek root access..." "$YEL"
if ! su -c "id" &>/dev/null; then
    pr "  x Root tidak tersedia! Grant su ke Termux dulu." "$RED"; exit 1
fi
pr "  v Root OK" "$GRE"; echo ""

# [2/5] Install packages
pr "[2/5] Update dan install packages Termux..." "$YEL"
pkg update -y -q 2>/dev/null; pkg upgrade -y -q 2>/dev/null
for p in python python-pip nano curl wget git; do
    if dpkg -s "$p" &>/dev/null; then
        pr "  v $p" "$GRE"
    else
        pr "  -> Install $p..." "$YEL"
        pkg install -y "$p" -q 2>/dev/null
        pr "  v $p terpasang" "$GRE"
    fi
done; echo ""

# [3/5] Python packages
pr "[3/5] Install Python packages..." "$YEL"
for pp in requests websocket-client; do
    pr "  -> pip install $pp..." "$YEL"
    pip3 install "$pp" -q
    pr "  v $pp" "$GRE"
done; echo ""

# [4/5] Init file
pr "[4/5] Inisialisasi file..." "$YEL"
if [ ! -f "$DIR/config.json" ]; then
    cat > "$DIR/config.json" << 'CFEOF'
{
  "packages": [],
  "ps_links": {},
  "global_ps_link": "",
  "check_interval": 35,
  "restart_delay": 10,
  "webhook_url": "",
  "floating_window": true,
  "auto_mute": true,
  "auto_low_graphics": true,
  "auto_tap_splash": true,
  "tap_interval": 3,
  "autoexec_script": "",
  "autoexec_delay": 30
}
CFEOF
    pr "  v config.json dibuat" "$GRE"
else
    pr "  v config.json sudah ada" "$GRE"
    # Tambah field baru kalau belum ada di config lama
    python3 -c "
import json, sys
try:
    with open('$DIR/config.json') as f:
        c = json.load(f)
    changed = False
    defaults = {
        'auto_tap_splash': True,
        'tap_interval': 3,
        'autoexec_script': '',
        'autoexec_delay': 30
    }
    for k, v in defaults.items():
        if k not in c:
            c[k] = v
            changed = True
    if changed:
        with open('$DIR/config.json', 'w') as f:
            json.dump(c, f, indent=2)
        print('  v config.json diperbarui dengan field baru')
except: pass
" 2>/dev/null
fi
touch "$DIR/activity.log" "$DIR/status.json"
chmod +x "$DIR/main.py" "$DIR/start.sh" "$DIR/update.sh" 2>/dev/null
pr "  v Permission OK" "$GRE"; echo ""

# [5/5] Done
pr "[5/5] Setup selesai!" "$YEL"; echo ""
echo -e "${CYA}${SEP}${RES}"
pr "OK Instalasi berhasil!" "$GRE"; echo ""
pr "Langkah selanjutnya:" "$YEL"
pr "  1. bash start.sh" "$CYA"
pr "  2. Menu 2  -> Detect packages Roblox" "$GRY"
pr "  3. Menu 3  -> Set PS Link / Game ID" "$GRY"
pr "  4. Menu 1  -> Start Auto Rejoin" "$GRY"
echo ""
pr "Atau langsung: bash start.sh --auto" "$CYA"
echo -e "${CYA}${SEP}${RES}"; echo ""
