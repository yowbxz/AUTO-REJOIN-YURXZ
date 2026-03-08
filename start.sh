#!/bin/bash
# ╔══════════════════════════════════════════════╗
# ║   🔧 start.sh — Launcher                    ║
# ║   Roblox Auto Rejoin by YURXZ               ║
# ╚══════════════════════════════════════════════╝

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

RED='\033[0;31m'; YEL='\033[0;33m'; GRE='\033[0;32m'
CYA='\033[0;36m'; RES='\033[0m'

echo -e "\n${CYA}══════════════════════════════════════${RES}"
echo -e "${CYA}  🎮 Roblox Auto Rejoin — Launcher    ${RES}"
echo -e "${CYA}══════════════════════════════════════${RES}\n"

# ── Auto install dependencies ─────────────────────────
echo -e "${YEL}[*] Cek & install dependencies...${RES}"

# Update pkg
pkg update -y -q 2>/dev/null

install_if_missing() {
    if ! command -v "$1" &>/dev/null; then
        echo -e "${YEL}    → Install $2...${RES}"
        pkg install -y "$2" -q 2>/dev/null
    else
        echo -e "${GRE}    ✓ $1 sudah ada${RES}"
    fi
}

install_if_missing python3  python
install_if_missing pip3     python-pip
install_if_missing nano     nano

# Python packages
PY_PKGS=("requests")
for pkg_py in "${PY_PKGS[@]}"; do
    if ! python3 -c "import $pkg_py" 2>/dev/null; then
        echo -e "${YEL}    → pip install $pkg_py...${RES}"
        pip3 install "$pkg_py" -q
    else
        echo -e "${GRE}    ✓ $pkg_py sudah ada${RES}"
    fi
done

echo -e "\n${GRE}[✓] Dependencies OK${RES}\n"

# ── Wakelock ──────────────────────────────────────────
echo -e "${YEL}[*] Aktifkan wakelock...${RES}"
# Termux-wake-lock kalau tersedia
if command -v termux-wake-lock &>/dev/null; then
    termux-wake-lock &
    echo -e "${GRE}    ✓ termux-wake-lock aktif${RES}"
else
    echo -e "${YEL}    ⚠ termux-wake-lock tidak ada (install termux-api jika perlu)${RES}"
fi

# ── Buat stop.sh otomatis ────────────────────────────
cat > "$DIR/stop.sh" << 'STOPEOF'
#!/bin/bash
echo -e "\033[0;33m[!] Menghentikan Roblox Auto Rejoin...\033[0m"
pkill -f "main.py" 2>/dev/null
pkill -f "python3 main" 2>/dev/null
# Lepas wakelock
if command -v termux-wake-unlock &>/dev/null; then
    termux-wake-unlock
fi
echo -e "\033[0;32m[✓] Dihentikan.\033[0m"
STOPEOF
chmod +x "$DIR/stop.sh"
echo -e "${GRE}[✓] stop.sh dibuat${RES}\n"

# ── Proteksi proses (anti-kill termux) ───────────────
# Set niceness rendah supaya termux tidak di-kill sistem
renice -5 $$ 2>/dev/null

# ── Cek root ─────────────────────────────────────────
echo -e "${YEL}[*] Cek root...${RES}"
if su -c "id" &>/dev/null; then
    echo -e "${GRE}    ✓ Root tersedia${RES}\n"
else
    echo -e "${RED}    ✗ Root TIDAK tersedia! Script butuh root.${RES}"
    echo -e "${RED}      Pastikan Termux sudah di-grant su access.${RES}\n"
    exit 1
fi

# ── Parse argumen yang diteruskan ke main.py ─────────
EXTRA_ARGS=""
for arg in "$@"; do
    EXTRA_ARGS="$EXTRA_ARGS $arg"
done

# ── Jalankan main.py dengan watchdog ─────────────────
echo -e "${CYA}[*] Menjalankan main.py...${RES}"
echo -e "${YEL}    (Gunakan stop.sh atau Ctrl+C untuk berhenti)${RES}\n"

# Watchdog: restart main.py kalau crash (bukan Ctrl+C)
while true; do
    python3 "$DIR/main.py" $EXTRA_ARGS
    EXIT_CODE=$?

    # Exit code 0 = user keluar normal (Ctrl+C / menu Exit)
    if [ $EXIT_CODE -eq 0 ] || [ $EXIT_CODE -eq 130 ]; then
        echo -e "\n${GRE}[✓] Keluar normal.${RES}"
        break
    fi

    echo -e "\n${RED}[!] main.py crash (code $EXIT_CODE). Restart dalam 10 detik...${RES}"
    echo -e "${YEL}    Ctrl+C sekarang untuk batal.${RES}"
    sleep 10
done

# Lepas wakelock saat selesai
if command -v termux-wake-unlock &>/dev/null; then
    termux-wake-unlock 2>/dev/null
fi
