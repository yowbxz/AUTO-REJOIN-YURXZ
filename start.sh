#!/bin/bash
# YURXZ Rejoin v9 — start.sh

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

RED='\033[0;31m'; YEL='\033[0;33m'; GRE='\033[0;32m'
CYA='\033[0;36m'; RES='\033[0m'; MGA='\033[0;35m'; GRY='\033[0;37m'

# Auto detect lebar terminal
W=$(tput cols 2>/dev/null || echo 44)
[ "$W" -lt 30 ] && W=30
SEP=$(printf '=%.0s' $(seq 1 $W))
SEP2=$(printf '-%.0s' $(seq 1 $W))

pr() { printf "${2:-$RES}  %-$((W-2))s${RES}\n" "$1"; }

clear
echo -e "${CYA}${SEP}${RES}"
pr "YURXZ Rejoin v9  --  Launcher" "$MGA"
pr "by YURXZ" "$GRY"
echo -e "${CYA}${SEP2}${RES}"; echo ""

# Dependencies
pr "[*] Cek & install dependencies..." "$YEL"
pkg update -y -q 2>/dev/null

install_if_missing() {
    if ! command -v "$1" &>/dev/null; then
        pr "  -> Install $2..." "$YEL"
        pkg install -y "$2" -q 2>/dev/null
    else
        pr "  v $1 sudah ada" "$GRE"
    fi
}
install_if_missing python3 python
install_if_missing pip3 python-pip
install_if_missing nano nano

for pkg_py in requests; do
    if ! python3 -c "import $pkg_py" 2>/dev/null; then
        pr "  -> pip install $pkg_py..." "$YEL"
        pip3 install "$pkg_py" -q
    else
        pr "  v $pkg_py sudah ada" "$GRE"
    fi
done
echo ""; pr "[v] Dependencies OK" "$GRE"; echo ""

# Wakelock
pr "[*] Aktifkan wakelock..." "$YEL"
if command -v termux-wake-lock &>/dev/null; then
    termux-wake-lock &
    pr "  v wakelock aktif" "$GRE"
else
    pr "  ! termux-wake-lock tidak ada" "$YEL"
fi

# Buat stop.sh
cat > "$DIR/stop.sh" << 'STOPEOF'
#!/bin/bash
W=$(tput cols 2>/dev/null || echo 44); SEP=$(printf '=%.0s' $(seq 1 $W))
echo -e "\033[0;36m${SEP}\033[0m"
printf "\033[0;35m  %-$((W-2))s\033[0m\n" "YURXZ Rejoin v9 -- Stopper"
echo -e "\033[0;36m${SEP}\033[0m"; echo ""
pkill -f "main.py" 2>/dev/null; pkill -f "python3 main" 2>/dev/null
command -v termux-wake-unlock &>/dev/null && termux-wake-unlock
echo -e "\033[0;32m[v] Dihentikan.\033[0m"
STOPEOF
chmod +x "$DIR/stop.sh"
pr "[v] stop.sh dibuat" "$GRE"; echo ""

renice -5 $$ 2>/dev/null

# Cek root
pr "[*] Cek root..." "$YEL"
if su -c "id" &>/dev/null; then
    pr "  v Root tersedia" "$GRE"; echo ""
else
    pr "  x Root TIDAK tersedia! Grant su ke Termux dulu." "$RED"; echo ""; exit 1
fi

# Fix terminal
export TERM=xterm-256color
stty sane 2>/dev/null || true

EXTRA_ARGS=""
for arg in "$@"; do EXTRA_ARGS="$EXTRA_ARGS $arg"; done

echo -e "${CYA}${SEP}${RES}"
pr "[*] Menjalankan YURXZ Rejoin v9..." "$CYA"
pr "    bash stop.sh atau Ctrl+C untuk berhenti" "$YEL"
echo -e "${CYA}${SEP}${RES}"; echo ""

while true; do
    python3 "$DIR/main.py" $EXTRA_ARGS
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ] || [ $EXIT_CODE -eq 130 ]; then
        echo ""; pr "[v] Keluar normal." "$GRE"; break
    fi
    echo ""; pr "[!] Crash (code $EXIT_CODE). Restart 10 detik..." "$RED"
    pr "    Ctrl+C untuk batal." "$YEL"; sleep 10
done

command -v termux-wake-unlock &>/dev/null && termux-wake-unlock 2>/dev/null
