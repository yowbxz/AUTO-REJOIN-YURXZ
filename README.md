# 🎮 YURXZ Rejoin v9

> Auto Rejoin Roblox untuk Android Rooted + Termux — **tanpa cookie**, deteksi via package process.

---

## ✨ Fitur

- 🔍 **Auto detect** semua package Roblox di device (murni scan, tidak hardcoded)
- 🔄 **Auto rejoin** kalau disconnect, crash, atau freeze
- 📋 **4 Level deteksi** dengan fallback otomatis (tanpa cookie!)
- 📱 **Multi akun paralel** — tiap package punya thread sendiri, rejoin independen
- 🪟 **Floating window** dengan grid layout otomatis
- 👆 **Auto tap splash screen** — tap otomatis saat loading/intro game
- 💉 **AutoExec script** — inject Lua ke semua executor saat masuk game
- 🔇 **Auto mute** suara Roblox
- 📉 **Auto low grafik** Roblox
- 🛡️ **Protect app** anti-kill oleh sistem Android
- 🗑️ **Clear cache aman** tidak hapus data login
- 📡 **Discord webhook** notifikasi disconnect/rejoin + screenshot
- 📝 **Activity log** tersimpan otomatis
- 🔁 **Watchdog** — restart otomatis kalau script crash
- ⌨️ **Quick sequence** — ketik `231` = jalankan menu 2,3,1 urut

---

## 🔍 Sistem Deteksi (tanpa cookie)

Script otomatis pilih metode terbaik yang work di HP kamu:

```
[A] Level 1 -> dumpsys activity   cek nama Activity (GameActivity?)
[N] Level 2 -> network check      cek koneksi aktif ke server Roblox
[C] Level 3 -> CPU usage          cek app masih aktif
[P] Level 4 -> pidof              fallback universal (99% HP rooted)
```

---

## 👆 Auto Tap Splash Screen

Deteksi loading screen otomatis dan tap sampai masuk game:

```
Launch Roblox
    |
Detect activity tiap detik
    |
SplashActivity / LoadingActivity -> auto tap di posisi window
    |
GameActivity terdeteksi! -> stop tap + inject autoexec
```

Support floating window — posisi tap otomatis sesuai letak window tiap package.

---

## 💉 AutoExec Script

Inject script Lua ke semua executor saat masuk game:

- Support semua executor: Delta, Fluxus, Cryptic, CodeX, Ronix, Arceus X, Hydrogen, Vega X, Trigon, Krnl, dll
- **Dynamic scan** — tidak hardcoded, otomatis detect executor yang terinstall
- Support lite/clone/modded executor
- Set delay inject sesuai loading time game (default 30 detik)
- Untuk game loading lama seperti Fisch: set delay 35-40 detik

---

## 📱 Multi Akun Paralel

Tiap package punya **thread sendiri** — rejoin independen:

```
Package A -> Thread A -> monitor + tap + rejoin sendiri
Package B -> Thread B -> monitor + tap + rejoin sendiri
Package C -> Thread C -> monitor + tap + rejoin sendiri
```

Kalau package A crash, package B tetap jalan tidak terganggu.

---

## 📋 Requirements

- Android dengan **root** (Magisk / KernelSU / SuperSU)
- **Termux** terinstall
- **Python 3** (auto install via setup.sh)
- `requests` (auto install via setup.sh) — untuk webhook Discord

---

## ⚙️ Instalasi

```bash
# Clone repo
pkg install -y git python
git clone https://github.com/yowbxz/AUTO-REJOIN-YURXZ /sdcard/Download/AUTO-REJOIN-YURXZ
cd /sdcard/Download/AUTO-REJOIN-YURXZ

# Setup
bash setup.sh

# Jalankan
bash start.sh
```

---

## 🚀 Cara Pakai

**Setup pertama kali (quick):**
```
Ketik: 231
= Menu 2 (Detect) -> Menu 3 (Set PS) -> Menu 1 (Start)
```

**Atau manual:**
```
Menu 2  -> Detect packages Roblox
Menu 3  -> Set PS Link / Game ID
Menu 12 -> Toggle Auto Tap Splash (ON)
Menu 13 -> Set AutoExec Script
Menu 1  -> Start Auto Rejoin
```

**Format PS Link yang diterima:**

| Format | Contoh |
|---|---|
| Game ID | `995679412` |
| Roblox URI | `roblox://placeId=995679412` |
| Link game | `https://www.roblox.com/games/995679412/...` |
| Private Server | `https://www.roblox.com/games/...?privateServerLinkCode=xxx` |

---

## 📋 Menu

| No | Menu | Fungsi |
|---|---|---|
| 1 | Start Auto Rejoin | Monitor & auto rejoin (paralel) |
| 2 | Detect Packages | Scan semua package Roblox di device |
| 3 | Set PS Link (Semua) | Set link sama untuk semua package |
| 4 | Set PS Link per Package | Set link berbeda tiap package |
| 5 | Clear Config | Hapus data config |
| 6 | List Config | Lihat isi config + status |
| 7 | Setup Webhook | Notif Discord |
| 8 | Set Interval | Atur jeda cek |
| 9 | Toggle Floating Window | On/Off floating |
| 10 | Toggle Auto Mute | On/Off mute |
| 11 | Toggle Low Grafik | On/Off low grafik |
| 12 | Toggle Auto Tap Splash | On/Off auto tap loading screen |
| 13 | Set AutoExec Script | Set script Lua + delay inject |
| 14 | Diagnostic | Test metode deteksi HP ini |
| 15 | Lihat Log | Riwayat aktivitas |
| 16 | Exit | Keluar |

---

## ⚡ Flag CLI

```bash
bash start.sh               # Normal
bash start.sh --auto        # Langsung start tanpa menu
bash start.sh --preventif   # Cek tiap 20 detik
bash start.sh --low         # Mode hemat RAM/CPU
```

## ⌨️ Quick Sequence

Ketik kombinasi angka untuk jalankan beberapa menu urut:

```
231    -> Detect + Set PS + Start
23     -> Detect + Set PS
21     -> Detect + Start
2,3,1  -> sama (pakai koma)
2 3 1  -> sama (pakai spasi)
```

---

## 🔄 Update

```bash
cd /sdcard/Download/AUTO-REJOIN-YURXZ && bash update.sh
```

Config & log tidak akan hilang saat update (auto backup).

---

## 📁 File

| File | Fungsi |
|---|---|
| `main.py` | Script utama |
| `setup.sh` | Installer dependencies |
| `start.sh` | Launcher + watchdog |
| `update.sh` | Update dari GitHub |
| `config.json` | Config (auto dibuat) |
| `activity.log` | Log aktivitas (auto dibuat) |
| `status.json` | Status akun (auto dibuat) |

---

## ⚠️ Disclaimer

Script ini hanya untuk keperluan pribadi. Penggunaan tool otomatis bisa melanggar Terms of Service Roblox. Gunakan dengan bijak.

---

**by YURXZ**
