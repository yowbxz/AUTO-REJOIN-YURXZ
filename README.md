# 🎮 YURXZ Rejoin v9

> Auto Rejoin Roblox untuk Android Rooted + Termux — **tanpa cookie**, deteksi via package process.

---

## ✨ Fitur

- 🔍 **Auto detect** semua package Roblox di device (murni scan, tidak hardcoded)
- 🔄 **Auto rejoin** kalau disconnect, crash, atau freeze
- 📋 **4 Level deteksi** dengan fallback otomatis (tanpa cookie!)
- 📱 **Multi akun** — support lebih dari 1 akun via multi package
- 🪟 **Floating window** dengan grid layout otomatis
- 🔇 **Auto mute** suara Roblox
- 📉 **Auto low grafik** Roblox
- 🛡️ **Protect app** anti-kill oleh sistem Android
- 🗑️ **Clear cache aman** tidak hapus data login
- 📡 **Discord webhook** notifikasi disconnect/rejoin + screenshot
- 📝 **Activity log** tersimpan otomatis
- 🔁 **Watchdog** — restart otomatis kalau script crash

---

## 🔍 Sistem Deteksi (tanpa cookie)

Script otomatis pilih metode terbaik yang work di HP kamu:

```
📋 Level 1 → dumpsys activity   cek nama Activity (GameActivity?)
🌐 Level 2 → network check      cek koneksi aktif ke server Roblox
💻 Level 3 → CPU usage          cek app masih aktif
🔍 Level 4 → pidof              fallback universal (99% HP rooted)
```

Kalau Level 1 tidak work → otomatis turun ke Level 2, dst.

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
git clone https://github.com/yowbxz/AUTO-REJOIN-YURXZ
cd AUTO-REJOIN-YURXZ

# Setup (install semua dependencies otomatis)
bash setup.sh

# Jalankan
bash start.sh
```

---

## 🚀 Cara Pakai

**Urutan setup pertama kali:**

```
Menu 2 → Detect packages Roblox (otomatis scan device)
Menu 3 → Set PS Link / Game ID
Menu 1 → Start Auto Rejoin
```

**Format input PS Link / Game ID:**

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
| 1 | Start Auto Rejoin | Monitor & auto rejoin |
| 2 | Detect Packages | Scan semua package Roblox di device |
| 3 | Set PS Link / Game ID | Set link sama untuk semua package |
| 4 | Set PS Link per Package | Set link berbeda tiap package |
| 5 | Clear Config | Hapus data config |
| 6 | List Config | Lihat isi config + status |
| 7 | Setup Webhook | Notif Discord |
| 8 | Set Interval | Atur jeda cek (detik) |
| 9 | Toggle Floating Window | On/Off floating |
| 10 | Toggle Auto Mute | On/Off mute |
| 11 | Toggle Low Grafik | On/Off low grafik |
| 12 | Lihat Log | Riwayat aktivitas |
| 13 | Exit | Keluar |

---

## ⚡ Flag CLI

```bash
bash start.sh               # Normal
bash start.sh --auto        # Langsung start tanpa menu
bash start.sh --preventif   # Cek tiap 20 detik
bash start.sh --low         # Mode hemat RAM/CPU
```

---

## 🖥️ Tampilan

**Menu utama:**
```
╔═══════════════════════════════════════════════════════╗
║   YURXZ Rejoin v9  —  No Cookie Edition              ║
║   by YURXZ  |  Detect via Package Process            ║
║   RAM Free: 2048MB (45%) | Packages: 2               ║
╠═══════════════════════════════════════════════════════╣
║  1     Start Auto Rejoin                             ║
║  2     Detect & Set Packages Roblox                  ║
║  ...                                                 ║
╚═══════════════════════════════════════════════════════╝
```

**Monitoring:**
```
  🎮 YURXZ Rejoin v9  |  No Cookie  |  by YURXZ

┌───────────────────────────────────┬──────────────────┐
│ ⚙  System                        │ Monitoring [1/2] │
│ 💾 Memory                        │ Free: 2048MB(45%)│
├───────────────────────────────────┼──────────────────┤
│ 📋 com.roblox.client              │ In-game ✅       │
│ 🌐 com.roblox.clientv             │ In-game ✅       │
└───────────────────────────────────┴──────────────────┘
```

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

## 🔄 Update

```bash
bash update.sh
```

Config & log tidak akan hilang saat update (auto backup).

---

## ⚠️ Disclaimer

Script ini hanya untuk keperluan pribadi. Penggunaan tool otomatis bisa melanggar Terms of Service Roblox. Gunakan dengan bijak.

---

**by YURXZ**
