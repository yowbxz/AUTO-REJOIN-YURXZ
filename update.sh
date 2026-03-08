#!/bin/bash
# ╔══════════════════════════════════════════════╗
# ║   🔄 update.sh — Update dari GitHub         ║
# ║   Roblox Auto Rejoin by YURXZ               ║
# ╚══════════════════════════════════════════════╝

RED='\033[0;31m'; YEL='\033[0;33m'; GRE='\033[0;32m'
CYA='\033[0;36m'; RES='\033[0m'; BLD='\033[1m'

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# ── EDIT INI: GitHub repo kamu ───────────────────────
GITHUB_USER="yowbxz"
GITHUB_REPO="AUTO-REJOIN-YURXZ"
BRANCH="main"
# ─────────────────────────────────────────────────────

RAW_BASE="https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${BRANCH}"
FILES_TO_UPDATE=("main.py" "start.sh" "setup.sh" "update.sh" "cookie_import.py")

clear
echo -e "${CYA}${BLD}"
echo "╔══════════════════════════════════════════════╗"
echo "║   🔄 Roblox Auto Rejoin — Updater           ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${RES}\n"

# ── Backup data penting ───────────────────────────────
echo -e "${YEL}[1/4] Backup data penting...${RES}"
BACKUP_DIR="$DIR/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup config.json (berisi cookie & webhook)
if [ -f "$DIR/config.json" ]; then
    cp "$DIR/config.json" "$BACKUP_DIR/config.json"
    echo -e "${GRE}  ✓ config.json di-backup${RES}"
fi

# Backup activity.log
if [ -f "$DIR/activity.log" ]; then
    cp "$DIR/activity.log" "$BACKUP_DIR/activity.log"
    echo -e "${GRE}  ✓ activity.log di-backup${RES}"
fi

echo -e "${GRE}  ✓ Backup tersimpan di: $BACKUP_DIR${RES}\n"

# ── Cek koneksi internet ──────────────────────────────
echo -e "${YEL}[2/4] Cek koneksi internet...${RES}"
if ! curl -s --max-time 5 "https://github.com" > /dev/null; then
    echo -e "${RED}  ✗ Tidak ada koneksi internet!${RES}"
    exit 1
fi
echo -e "${GRE}  ✓ Koneksi OK${RES}\n"

# ── Download file terbaru ─────────────────────────────
echo -e "${YEL}[3/4] Download file terbaru dari GitHub...${RES}"
echo -e "  Repo: ${CYA}${GITHUB_USER}/${GITHUB_REPO}@${BRANCH}${RES}\n"

SUCCESS=0
FAIL=0
for file in "${FILES_TO_UPDATE[@]}"; do
    URL="${RAW_BASE}/${file}"
    echo -ne "  → ${file}... "
    
    HTTP_CODE=$(curl -s -o "${DIR}/${file}.new" -w "%{http_code}" "$URL" --max-time 15)
    
    if [ "$HTTP_CODE" = "200" ]; then
        # Validasi file tidak kosong
        if [ -s "${DIR}/${file}.new" ]; then
            mv "${DIR}/${file}.new" "${DIR}/${file}"
            chmod +x "${DIR}/${file}" 2>/dev/null
            echo -e "${GRE}✓ Updated${RES}"
            SUCCESS=$((SUCCESS+1))
        else
            rm -f "${DIR}/${file}.new"
            echo -e "${YEL}⚠ File kosong, skip${RES}"
        fi
    else
        rm -f "${DIR}/${file}.new"
        echo -e "${RED}✗ Gagal (HTTP $HTTP_CODE)${RES}"
        FAIL=$((FAIL+1))
    fi
done

echo ""

# ── Restore config (jangan overwrite!) ───────────────
echo -e "${YEL}[4/4] Restore config...${RES}"
if [ -f "$BACKUP_DIR/config.json" ]; then
    cp "$BACKUP_DIR/config.json" "$DIR/config.json"
    echo -e "${GRE}  ✓ config.json dipulihkan (cookie & webhook aman)${RES}"
fi
echo ""

# ── Summary ───────────────────────────────────────────
echo -e "${CYA}${BLD}══════════════════════════════════════${RES}"
echo -e "${GRE}  ✅ Update selesai!${RES}"
echo -e "  Berhasil : ${GRE}${SUCCESS}${RES} file"
if [ $FAIL -gt 0 ]; then
    echo -e "  Gagal    : ${RED}${FAIL}${RES} file"
fi
echo -e "  Backup   : ${CYA}${BACKUP_DIR}${RES}"
echo ""
echo -e "  Jalankan ulang: ${CYA}bash start.sh${RES}"
echo -e "${CYA}${BLD}══════════════════════════════════════${RES}\n"
