#!/data/data/com.termux/files/usr/bin/bash
# YURXZ Rejoin v9 — Termux:Boot Script
# Letakkan di: ~/.termux/boot/yurxz.sh

# ── Setup PATH Termux dulu ────────────────────────────
export PATH=/data/data/com.termux/files/usr/bin:$PATH
export LD_LIBRARY_PATH=/data/data/com.termux/files/usr/lib:$LD_LIBRARY_PATH
export PREFIX=/data/data/com.termux/files/usr
export HOME=/data/data/com.termux/files/home
export TERM=xterm-256color

LOGFILE="/data/data/com.termux/files/home/boot.log"

log() {
    echo "[$(date '+%d/%m %H:%M:%S')] $1" >> "$LOGFILE"
}

log "=== Termux:Boot dimulai ==="

# ── Tunggu sistem ready ───────────────────────────────
log "Tunggu sistem ready (30 detik)..."
sleep 30

# ── Tunggu storage mount ──────────────────────────────
log "Cek storage..."
TRIES=0
while [ $TRIES -lt 20 ]; do
    if [ -d "/sdcard/Download" ]; then
        log "Storage OK"
        break
    fi
    log "Storage belum ready, tunggu 5 detik... ($TRIES)"
    sleep 5
    TRIES=$((TRIES + 1))
done

if [ ! -d "/sdcard/Download" ]; then
    log "ERROR: Storage tidak bisa diakses!"
    exit 1
fi

DIR="/sdcard/Download/AUTO-REJOIN-YURXZ"

# ── Cek folder repo ───────────────────────────────────
if [ ! -f "$DIR/main.py" ]; then
    log "ERROR: $DIR/main.py tidak ditemukan!"
    exit 1
fi

# ── Tunggu root ready ─────────────────────────────────
log "Cek root..."
TRIES=0
while [ $TRIES -lt 10 ]; do
    if su -c "id" > /dev/null 2>&1; then
        log "Root OK"
        break
    fi
    log "Root belum ready, tunggu 5 detik... ($TRIES)"
    sleep 5
    TRIES=$((TRIES + 1))
done

# ── Jalankan start.sh di background ──────────────────
log "Menjalankan start.sh..."
cd "$DIR"
nohup bash "$DIR/start.sh" all >> "$DIR/boot_run.log" 2>&1 &
PID=$!
log "start.sh berjalan (PID: $PID)"

echo $PID > "$DIR/boot.pid"
log "=== Boot selesai ==="
