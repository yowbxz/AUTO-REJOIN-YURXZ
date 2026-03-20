#!/bin/bash
# YURXZ Rejoin v9 — update.sh

RED='\033[0;31m'; YEL='\033[0;33m'; GRE='\033[0;32m'
CYA='\033[0;36m'; RES='\033[0m'; MGA='\033[0;35m'; GRY='\033[0;37m'

DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$DIR"

GITHUB_USER="yowbxz"
GITHUB_REPO="AUTO-REJOIN-YURXZ"
BRANCH="main"
RAW_BASE="https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${BRANCH}"
FILES_TO_UPDATE=("main.py" "start.sh" "setup.sh" "update.sh")

W=$(tput cols 2>/dev/null || echo 44)
[ "$W" -lt 30 ] && W=30
SEP=$(printf '=%.0s' $(seq 1 $W))
SEP2=$(printf '-%.0s' $(seq 1 $W))

pr() { printf "${2:-$RES}  %-$((W-2))s${RES}\n" "$1"; }

clear
echo -e "${CYA}${SEP}${RES}"
pr "YURXZ Rejoin v9  --  Updater" "$MGA"
pr "by YURXZ" "$GRY"
echo -e "${CYA}${SEP}${RES}"; echo ""

# [1/4] Backup
pr "[1/4] Backup data penting..." "$YEL"
BACKUP_DIR="$DIR/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
[ -f "$DIR/config.json" ] && cp "$DIR/config.json" "$BACKUP_DIR/" && pr "  v config.json di-backup" "$GRE"
[ -f "$DIR/activity.log" ] && cp "$DIR/activity.log" "$BACKUP_DIR/" && pr "  v activity.log di-backup" "$GRE"
pr "  v Backup: $BACKUP_DIR" "$GRE"; echo ""

# [2/4] Cek internet
pr "[2/4] Cek koneksi internet..." "$YEL"
if ! curl -s --max-time 5 "https://github.com" > /dev/null; then
    pr "  x Tidak ada koneksi internet!" "$RED"; exit 1
fi
pr "  v Koneksi OK" "$GRE"; echo ""

# [3/4] Download
pr "[3/4] Download file terbaru dari GitHub..." "$YEL"
pr "  Repo: ${GITHUB_USER}/${GITHUB_REPO}@${BRANCH}" "$GRY"; echo ""

SUCCESS=0; FAIL=0
for file in "${FILES_TO_UPDATE[@]}"; do
    URL="${RAW_BASE}/${file}"
    printf "  %-20s " "-> ${file}..."
    HTTP_CODE=$(curl -s -o "${DIR}/${file}.new" -w "%{http_code}" "$URL" --max-time 15)
    if [ "$HTTP_CODE" = "200" ] && [ -s "${DIR}/${file}.new" ]; then
        mv "${DIR}/${file}.new" "${DIR}/${file}"
        chmod +x "${DIR}/${file}" 2>/dev/null
        echo -e "${GRE}v Updated${RES}"
        SUCCESS=$((SUCCESS+1))
    else
        rm -f "${DIR}/${file}.new"
        echo -e "${RED}x Gagal (HTTP $HTTP_CODE)${RES}"
        FAIL=$((FAIL+1))
    fi
done; echo ""

# [4/4] Restore config
pr "[4/4] Restore config..." "$YEL"
[ -f "$BACKUP_DIR/config.json" ] && cp "$BACKUP_DIR/config.json" "$DIR/config.json" && pr "  v config.json dipulihkan (data aman)" "$GRE"
echo ""

echo -e "${CYA}${SEP}${RES}"
pr "OK Update selesai!" "$GRE"
pr "  Berhasil : ${SUCCESS} file" "$GRY"
[ $FAIL -gt 0 ] && pr "  Gagal    : ${FAIL} file" "$RED"
pr "  Backup   : ${BACKUP_DIR}" "$GRY"; echo ""
pr "Jalankan ulang: bash start.sh" "$CYA"
echo -e "${CYA}${SEP}${RES}"; echo ""
