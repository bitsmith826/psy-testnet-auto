# 🔮 Psy Protocol — Psychonaut Testnet Automation Bot

Sistem otomatisasi lengkap untuk mengikuti program testnet dan kampanye airdrop **Psy Protocol (Psychonaut Incubation Program)**.

- 🌐 **Portal Kampanye:** [https://psy.xyz/psychonaut](https://psy.xyz/psychonaut)
- 🚰 **Testnet Faucet & Bridge:** [https://app-stg.psy-protocol.xyz/#/faucet](https://app-stg.psy-protocol.xyz/#/faucet)

> [!IMPORTANT]
> **DISCLAIMER:** Proyek ini dibuat murni untuk **tujuan edukasi, riset protokol blockchain, dan pembelajaran open-source**. Dilarang keras menyalahgunakan software ini untuk eksploitasi, kecurangan, atau tindakan yang melanggar *Terms of Service* Psy Protocol. Penggunaan software ini sepenuhnya menjadi tanggung jawab masing-masing individu (*Use at your own risk*).

---

## ✨ Fitur Utama

1. **Multi-Account Support**:
   - Mendukung banyak akun sekaligus melalui file konfigurasi `config/accounts.json`.
   - Mendukung konfigurasi EVM Private Key, JWT Token, dan Proxy (HTTP/SOCKS5) per akun.

2. **Auto Referral Code Binding**:
   - Secara otomatis mengaitkan akun dengan referral code target jika diisi di `config.json` (`PUT /users/me/invite-code`).

3. **Auto Username Generator & Setup**:
   - Jika akun belum memiliki username publik, sistem akan otomatis mendaftarkan handle unik (`psychonaut_xxxxx`).

4. **Daily Check-in Automation**:
   - Otomatis melakukan check-in harian (`POST /tasks/check-in`) untuk menjaga streak poin Psy Points.

5. **Social Missions Auto-Submit**:
   - Otomatis mengirimkan bukti penyelesaian misi sosial di `/tasks/applications` (Follow @PsyProtocol, Like, Retweet, Reply #PsyProtocol, Tweet, dll).

6. **Discord Verification**:
   - Otomatis memverifikasi status membership, kuota pesan (10 pesan), dan reaksi pengumuman di server Discord Psy Protocol.

7. **On-Chain Testnet Faucet Claimer (Sepolia)**:
   - Mengklaim token testnet **10,000 pUSDT** dan **test PSY** langsung dari smart contract `TokenFaucetManager` di Ethereum Sepolia.

8. **Stealth Camoufox Engine (100% Zero-Touch Automation)**:
   - Menggunakan browser stealth **Camoufox** (Firefox C++ fingerprint bypass) yang secara otomatis memecahkan Cloudflare Turnstile captcha di background (headless) tanpa perlu klik manual sama sekali.
   - Mengotomatisasi penandatanganan SIWE (EIP-4361) dan menangkap `jwt_token` langsung ke `config/accounts.json`.

9. **Direct Precision Execution**:
   - Tinggal jalankan `python main.py`, bot otomatis memproses On-Chain Sepolia Faucet (10,000 pUSDT) + Login Headless + Daily Check-In + Referral Binding + Social Quests di seluruh dompet sekaligus dengan tampilan laporan tabel presisi berwarna.

---

## 📁 Struktur Direktori

```
psy-testnet-auto/
├── config/
│   ├── config.json          # Konfigurasi global (invite code, rpc, interval)
│   ├── accounts.json        # Data akun pengguna (private key, jwt, proxy)
│   └── accounts.example.json# Template contoh akun
├── core/
│   ├── api.py               # REST API Client untuk backend member-api.psy.xyz
│   ├── wallet.py            # Modul EVM Wallet & SIWE Message Generator/Signer
│   ├── onchain.py           # Web3 client untuk klaim Faucet pUSDT di Sepolia
│   ├── camoufox_login.py    # Stealth Camoufox Engine (Turnstile auto-solve & JWT capture)
│   └── display.py           # Engine formatting CLI presisi & berwarna (ASCII cards/tables)
├── modules/
│   ├── tasks_runner.py      # Eksekutor misi, check-in, dan profil
│   └── account_manager.py   # Pengelola akun dan batch processing
├── keys.txt                 # Daftar EVM Private Key (1 per baris)
├── main.py                  # CLI eksekutor utama presisi (Direct run & loop)
├── requirements.txt         # Dependensi Python (Camoufox, Web3, Colorama, Rich)
└── README.md                # Dokumentasi panduan
```

---

## 🚀 Panduan Instalasi & Penggunaan

### 1. Prasyarat
- Python 3.9 atau lebih tinggi.
- Google Chrome atau browser Chromium.

### 2. Instal Dependensi
Buka terminal / PowerShell di folder proyek ini dan jalankan:
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Akun (`config/accounts.json`)
Buka file `config/accounts.json` dan masukkan detail akun Anda:
```json
[
  {
    "id": 1,
    "name": "Akun-1",
    "private_key": "0xYOUR_EVM_PRIVATE_KEY",
    "jwt_token": "",
    "proxy": ""
  }
]
```

> **💡 Tips Login & JWT Token:**
> - **Cara 1 (Browser Assistant - Otomatis):** Anda cukup mengisi `private_key`, lalu di menu pilih **Option 4 (Browser Assistant)**. Chrome akan otomatis terbuka, menandatangani pesan SIWE, dan menangkap `jwt_token` langsung ke file `accounts.json`!
> - **Cara 2 (Manual Dari Web Browser):** Buka `https://psy.xyz/psychonaut`, connect wallet Anda di Chrome, tekan `F12` -> `Application` -> `Cookies` / `Local Storage` -> cari key `jwt_token` dan copy nilainya ke `accounts.json`.

---

## 🎮 Menjalankan Bot

### 1. Eksekusi Langsung Semua Akun (Default - Standar D:\Coding)
Cukup ketik:
```bash
python main.py
```
Bot akan langsung:
1. Membaca semua private key dari `keys.txt` / `config/accounts.json`.
2. Mengecek saldo Sepolia ETH dan token testnet.
3. Otomatis mengklaim **10,000 pUSDT** dari smart contract faucet Sepolia.
4. Mengerjakan tugas web campaign (Daily Check-in, Bind Referral jika diisi, Username, Misi Sosial) jika sesi terhubung.
5. Menampilkan tabel ringkasan lengkap untuk seluruh akun.

### 2. Mode Looping Otomatis 24 Jam
```bash
python main.py --loop
```

### 3. Menu / Opsi Tambahan (Opsional)
- Buka Menu Manual: `python main.py --menu`
- Login Browser untuk Akun Tertentu: `python main.py --login 1`

---

## ⚙️ Konfigurasi Lanjutan (`config/config.json`)

Anda dapat menyesuaikan setting di `config/config.json`:
- `invite_code`: Kode rujukan yang akan otomatis di-bind (kosongkan `""` jika tidak menggunakan referral).
- `loop_interval_hours`: Interval check-in otomatis (default: `24` jam).
- `auto_claim_sepolia_faucet`: Jika diset `true`, otomatis mengeksekusi klaim faucet Sepolia saat menjalankan tugas.
- `delay_between_tasks`: Jeda detik antar-tugas untuk keamanan akun.
- `delay_between_accounts`: Jeda detik antar-pergantian akun.

---

## 🔒 Catatan Keamanan
- Gunakan dompet baru (burner / airdrop wallet) untuk aktivitas testnet.
- Jangan pernah membagikan private key Anda kepada orang lain.
- File `config/accounts.json` disimpan secara lokal di komputer Anda.

---

## ⚠️ Disclaimer (Pernyataan Penyangkalan)

1. **Hanya untuk Tujuan Edukasi & Riset (*Educational & Research Purpose Only*)**:
   - Repositori dan kode sumber ini dibuat semata-mata untuk tujuan pembelajaran mengenai interaksi Web3 smart contract (Ethereum Sepolia), otomatisasi browser anti-deteksi (*stealth automation* dengan Camoufox), dan integrasi API kriptografi EIP-191.
2. **Bukan untuk Penyalahgunaan (*No Abuse / Sybil Misuse*)**:
   - Pengembang tidak mendukung, memfasilitasi, atau bertanggung jawab atas segala bentuk penyalahgunaan script ini untuk eksploitasi, serangan Sybil, manipulasi sistem jaringan, atau pelanggaran terhadap *Terms of Service* (Ketentuan Layanan) Psy Protocol.
3. **Resiko Pengguna (*Use at Your Own Risk*)**:
   - Segala tindakan, risiko teknis, potensi penangguhan akun (*ban*), atau kerugian yang timbul akibat penggunaan software ini sepenuhnya menjadi tanggung jawab masing-masing individu pengguna (*Do Your Own Research*). Penulis tidak memberikan jaminan keuntungan finansial atau perolehan airdrop dalam bentuk apa pun.
