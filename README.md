# 🎮 YURXZ Rejoin v9

> Auto Rejoin Roblox untuk Android Rooted + Termux — **tanpa cookie**, deteksi via package process.

---

## ✨ Fitur

- 🔍 **Auto detect** semua package Roblox di device
- 🔄 **Auto rejoin** paralel — tiap package thread sendiri
- 📋 **4 Level deteksi** dengan fallback otomatis
- 👆 **Auto tap splash screen** — tap otomatis saat loading
- 💉 **AutoExec** — inject Lua ke semua executor saat masuk game
- 🤖 **Discord Bot** — kontrol dari Discord pakai tombol
- 🪟 **Floating window** grid layout otomatis
- 🔇 **Auto mute** + 📉 **Low grafik**
- 🛡️ **Protect app** anti-kill
- 📡 **Discord webhook** notifikasi + screenshot
- 🔁 **Auto boot** via Termux:Boot

---

## ⚙️ Install (Baru)

```bash
pkg update -y && pkg install -y git python
git clone https://github.com/yowbxz/AUTO-REJOIN-YURXZ /sdcard/Download/AUTO-REJOIN-YURXZ
cd /sdcard/Download/AUTO-REJOIN-YURXZ
bash setup.sh
bash start.sh
```

---

## 🔄 Update

```bash
cd /sdcard/Download/AUTO-REJOIN-YURXZ && bash update.sh
```

---

## 🚀 Command

```bash
# Jalankan menu + bot background
bash start.sh

# Jalankan rejoin otomatis + bot background
bash start.sh all

# Hanya bot saja
bash start.sh bot

# Stop semua
bash start.sh stop
# atau
bash stop.sh
```

---

## 🧪 Test / Debug

```bash
# Test main.py langsung
cd /sdcard/Download/AUTO-REJOIN-YURXZ && python3 main.py

# Test bot
python3 bot.py

# Lihat log rejoin
tail -f /sdcard/Download/AUTO-REJOIN-YURXZ/activity.log

# Lihat log bot
tail -f /sdcard/Download/AUTO-REJOIN-YURXZ/bot.log

# Cek apakah rejoin jalan
pgrep -f main.py && echo "RUNNING" || echo "STOPPED"

# Cek status
cat /sdcard/Download/AUTO-REJOIN-YURXZ/status.json
```

---

## 🤖 Discord Bot

### Setup Bot

```bash
# Setup bot (sekali aja)
cd /sdcard/Download/AUTO-REJOIN-YURXZ
python3 bot.py setup
```

### Cara buat bot Discord

1. Buka https://discord.com/developers/applications
2. New Application → beri nama
3. Bot → Add Bot → Copy Token
4. Aktifkan **MESSAGE CONTENT INTENT**
5. OAuth2 → URL Generator → `bot` + permissions:
   Send Messages, Embed Links, Attach Files
6. Copy URL → invite ke server

### Munculin Panel di Discord

```
Ketik: !panel
```

### Tombol Panel

```
[🔧 Run Tools] [🔴 Stop Tools] [▶ Start Rejoin] [⏹ Stop Rejoin]
[📊 Status] [⚙️ Config] [📸 Screenshot] [📜 Log] [🔄 Refresh]
[💉 Run Script]
```

| Tombol | Fungsi |
|---|---|
| 🔧 Run Tools | Jalankan tools (menu muncul di Termux) |
| 🔴 Stop Tools | Hentikan tools + rejoin |
| ▶ Start Rejoin | Tunggu 20 detik lalu auto start rejoin |
| ⏹ Stop Rejoin | Kirim Ctrl+C ke rejoin |
| 📊 Status | Status tiap package |
| ⚙️ Config | Lihat config saat ini |
| 📸 Screenshot | Ambil screenshot layar |
| 📜 Log | 20 baris log terakhir |
| 💉 Run Script | Inject Lua via `!script <kode>` |
| 🔄 Refresh | Update panel |

---

## 📲 Auto Boot (Termux:Boot)

```bash
# Install Termux:Boot dari F-Droid
# Buka Termux:Boot sekali
# Lalu:
mkdir -p ~/.termux/boot
cp /sdcard/Download/AUTO-REJOIN-YURXZ/yurxz_boot.sh ~/.termux/boot/yurxz.sh
chmod +x ~/.termux/boot/yurxz.sh
# Restart HP — otomatis jalan!
```

---

## 📋 Menu Tools

| No | Menu |
|---|---|
| 1 | Start Auto Rejoin |
| 2 | Detect Packages Roblox |
| 3 | Set PS Link (Semua) |
| 4 | Set PS Link per Package |
| 5 | Clear Config |
| 6 | List Config |
| 7 | Setup Webhook |
| 8 | Set Interval |
| 9 | Toggle Floating Window |
| 10 | Toggle Auto Mute |
| 11 | Toggle Low Grafik |
| 12 | Toggle Auto Tap Splash |
| 13 | Set AutoExec Script |
| 14 | Diagnostic |
| 15 | Lihat Log |
| 16 | Exit |

**Quick sequence:** ketik `231` = Menu2 + Menu3 + Menu1 urut

---

## 📁 File

| File | Fungsi |
|---|---|
| `main.py` | Script utama rejoin |
| `bot.py` | Discord bot |
| `start.sh` | Launcher |
| `setup.sh` | Installer |
| `update.sh` | Updater dari GitHub |
| `yurxz_boot.sh` | Auto boot script |

---

## ⚠️ Disclaimer

Script ini hanya untuk keperluan pribadi. Gunakan dengan bijak.

---

**by YURXZ**
