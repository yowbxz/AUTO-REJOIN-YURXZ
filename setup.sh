#!/bin/bash
# ╔══════════════════════════════════════════════╗
# ║   📦 setup.sh — First Time Installer        ║
# ║   Roblox Auto Rejoin by YURXZ               ║
# ╚══════════════════════════════════════════════╝

RED='\033[0;31m'; YEL='\033[0;33m'; GRE='\033[0;32m'
CYA='\033[0;36m'; RES='\033[0m'; BLD='\033[1m'

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

clear
echo -e "${CYA}${BLD}"
echo "╔══════════════════════════════════════════════╗"
echo "║   📦 Roblox Auto Rejoin — Setup             ║"
echo "║   Android Rooted + Termux   by YURXZ        ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${RES}\n"

# ── Cek root ─────────────────────────────────────────
echo -e "${YEL}[1/5] Cek root access...${RES}"
if ! su -c "id" &>/dev/null; then
    echo -e "${RED}  ✗ Root tidak tersedia!${RES}"
    echo -e "${RED}    Pastikan Termux sudah diberi akses su.${RES}"
    exit 1
fi
echo -e "${GRE}  ✓ Root OK${RES}\n"

# ── Update & install packages ─────────────────────────
echo -e "${YEL}[2/5] Update dan install packages Termux...${RES}"
pkg update -y -q 2>/dev/null
pkg upgrade -y -q 2>/dev/null

PKGS=(python python-pip nano curl wget git)
for p in "${PKGS[@]}"; do
    if dpkg -s "$p" &>/dev/null; then
        echo -e "${GRE}  ✓ $p${RES}"
    else
        echo -e "${YEL}  → Install $p...${RES}"
        pkg install -y "$p" -q 2>/dev/null
        echo -e "${GRE}  ✓ $p terpasang${RES}"
    fi
done
echo ""

# ── Install Python packages ───────────────────────────
echo -e "${YEL}[3/5] Install Python packages...${RES}"
PY_PKGS=(requests)
for pp in "${PY_PKGS[@]}"; do
    echo -e "${YEL}  → pip install $pp...${RES}"
    pip3 install "$pp" -q
    echo -e "${GRE}  ✓ $pp${RES}"
done
echo ""

# ── Buat file config kosong kalau belum ada ───────────
echo -e "${YEL}[4/5] Inisialisasi file...${RES}"
if [ ! -f "$DIR/config.json" ]; then
    cat > "$DIR/config.json" << 'CFEOF'
{
  "check_interval": 35,
  "restart_delay": 15,
  "webhook_url": "",
  "floating_window": true,
  "auto_mute": true,
  "auto_low_graphics": true,
  "accounts": []
}
CFEOF
    echo -e "${GRE}  ✓ config.json dibuat (kosong)${RES}"
else
    echo -e "${GRE}  ✓ config.json sudah ada${RES}"
fi

touch activity.log status.json
chmod +x "$DIR/main.py" "$DIR/start.sh" "$DIR/update.sh" \
         "$DIR/cookie_import.py" 2>/dev/null
echo -e "${GRE}  ✓ Permission file OK${RES}\n"

# ── Selesai ───────────────────────────────────────────
echo -e "${YEL}[5/5] Setup selesai!${RES}\n"
echo -e "${CYA}${BLD}══════════════════════════════════════${RES}"
echo -e "${GRE}  ✅ Instalasi berhasil!${RES}"
echo ""
echo -e "  Langkah selanjutnya:"
echo -e "  ${BLD}1.${RES} Jalankan: ${CYA}python3 main.py${RES}"
echo -e "  ${BLD}2.${RES} Pilih menu ${CYA}'1. Create Config'${RES} untuk scan cookie"
echo -e "  ${BLD}3.${RES} Pilih menu ${CYA}'2. Start Rejoin'${RES} untuk mulai"
echo ""
echo -e "  Atau pakai launcher:"
echo -e "  ${CYA}bash start.sh${RES}"
echo -e "${CYA}${BLD}══════════════════════════════════════${RES}\n"
