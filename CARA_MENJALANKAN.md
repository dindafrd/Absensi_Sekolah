# 📚 PANDUAN LENGKAP: CARA MENJALANKAN APLIKASI DARI AWAL

Dokumen ini menjelaskan langkah-langkah lengkap untuk menjalankan **Face Recognition Attendance System** dari awal, mulai dari setup environment hingga mengakses aplikasi.

---

## 🎯 DAFTAR ISI

1. [Prasyarat](#prasyarat)
2. [Langkah 1: Setup Python Environment](#langkah-1-setup-python-environment)
3. [Langkah 2: Install Dependencies](#langkah-2-install-dependencies)
4. [Langkah 3: Konfigurasi Aplikasi](#langkah-3-konfigurasi-aplikasi)
5. [Langkah 4: Jalankan Aplikasi](#langkah-4-jalankan-aplikasi)
6. [Langkah 5: Akses Aplikasi](#langkah-5-akses-aplikasi)
7. [Troubleshooting](#troubleshooting)

---

## 🔧 PRASYARAT

Sebelum memulai, pastikan Anda sudah memiliki:

### Software yang Diperlukan:

- ✅ **Python 3.10 atau lebih tinggi** - [Download](https://www.python.org/downloads/)
- ✅ **Git** (opsional, untuk clone repository)
- ✅ **Text Editor atau IDE** (VS Code, Notepad++, dll)
- ✅ **Web Browser** (Chrome, Firefox, Edge, Safari)

### Cara Cek Versi Python:

```bash
python --version
# atau
python3 --version
```

Jika belum terinstall, download dari https://www.python.org/downloads/

---

## LANGKAH 1: SETUP PYTHON ENVIRONMENT

### 1.1 Buka Terminal/Command Prompt

- **Windows**: Tekan `Win + R`, ketik `cmd`, tekan Enter
- **Mac/Linux**: Buka Terminal

### 1.2 Navigasi ke Folder Aplikasi

```bash
cd d:\Face_Recognition
# atau sesuaikan dengan lokasi folder Anda
```

### 1.3 Buat Virtual Environment

Virtual environment adalah ruang terisolasi untuk project ini agar tidak mengganggu package global.

```bash
python -m venv .venv
```

**Penjelasan:**

- `python -m venv` = perintah membuat virtual environment
- `.venv` = nama folder virtual environment (bisa diganti)

### 1.4 Aktifkan Virtual Environment

#### **Windows (Command Prompt):**

```bash
.venv\Scripts\activate
```

#### **Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

Jika ada error di PowerShell, jalankan:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### **Mac/Linux:**

```bash
source .venv/bin/activate
```

**Indicator berhasil:**

- Prompt di terminal akan berubah menjadi `(.venv) C:\...`

---

## LANGKAH 2: INSTALL DEPENDENCIES

### 2.1 Update pip (Opsional tapi Disarankan)

```bash
python -m pip install --upgrade pip
```

### 2.2 Install Dependencies Dasar

Jalankan perintah ini untuk menginstall semua package yang diperlukan:

```bash
pip install -r requirements_web.txt
```

**Apa yang akan diinstall:**

- Flask (Web framework)
- OpenCV (Processing gambar)
- NumPy, Pandas (Data processing)
- SQLAlchemy (Database)
- Dan package lainnya...

### 2.3 Jika Ada Error saat Install (Khusus Windows)

Jika mendapat error pada `dlib` atau `face-recognition`, ini adalah masalah kompilasi di Windows. Ada 3 solusi:

#### **Solusi A: Skip face_recognition (Tersingkat)**

Aplikasi bisa tetap berjalan tanpa fitur pengenalan wajah:

```bash
# Install semua tanpa dlib
pip install Flask>=3.0.0 opencv-python>=4.8.0 numpy>=1.24.0 pandas>=2.0.0 Pillow>=10.0.0 openpyxl>=3.1.0 Flask-SQLAlchemy>=3.1.1 Flask-WTF>=1.2.1 python-dotenv>=1.0.0 bcrypt>=4.1.2 Flask-Migrate>=4.0.5
```

Aplikasi akan berfungsi normal, hanya fitur camera/face recognition yang disabled.

#### **Solusi B: Install CMake (Untuk Kompilasi)**

Jika ingin fitur face recognition lengkap:

1. Download CMake dari https://cmake.org/download/
2. Install CMake
3. Jalankan ulang: `pip install -r requirements_web.txt`

#### **Solusi C: Gunakan Pre-built Wheel**

Download dlib wheel yang sudah dikompilasi untuk Windows dari:
https://github.com/ageitgey/face_recognition/issues

---

## LANGKAH 3: KONFIGURASI APLIKASI

### 3.1 Copy File .env

File `.env` berisi konfigurasi aplikasi. Copy dari template:

```bash
cp .env.example .env
```

Atau jika di Windows dan `cp` tidak bekerja:

```bash
copy .env.example .env
```

### 3.2 Edit File .env (Opsional)

Buka file `.env` dengan text editor dan ubah sesuai kebutuhan:

```env
# Aplikasi
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
DEBUG=False

# Database
DATABASE_URI=sqlite:///data/attendance.db

# Server
HOST=127.0.0.1
PORT=5000

# Fitur
ENABLE_CONFIG_ADMIN_LOGIN=0
ADMIN_PASSWORD=
```

**Penjelasan:**

- `SECRET_KEY`: Kunci rahasia untuk enkripsi session (biarkan default jika tidak tahu)
- `PORT`: Port mana yang digunakan (default 5000, bisa ubah jika ada konflik)
- `HOST`: IP yang mendengarkan (127.0.0.1 = localhost saja)

### 3.3 Generate SECRET_KEY (Opsional)

Jika ingin SECRET_KEY yang lebih aman:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy output dan masukkan ke `SECRET_KEY` di file `.env`:

```env
SECRET_KEY=abc123def456... (output dari command di atas)
```

---

## LANGKAH 4: JALANKAN APLIKASI

### 4.1 Pastikan Virtual Environment Aktif

Cek prompt terminal menunjukkan `(.venv)` di depan.

Jika belum, aktifkan dulu:

```bash
# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

### 4.2 Jalankan Server

```bash
python run.py
```

**Output yang diharapkan:**

```
======================================================================
 WEB-BASED FACE RECOGNITION ATTENDANCE SYSTEM v2.0
======================================================================

🔒 Security Features:
  ✓ Password protection
  ✓ CSRF protection enabled
  ✓ Session security
  ✓ Structured logging

💾 Database:
  ✓ SQLite: sqlite:///data/attendance.db

Starting server...
Access the application at: http://127.0.0.1:5000

👤 Login menggunakan akun admin di database.

Press CTRL+C to stop the server
======================================================================
```

### 4.3 Troubleshooting Jalankan Server

#### Error: "Address already in use"

Port 5000 sudah terpakai. Ada 2 cara:

**Cara 1: Ubah PORT di .env**

```env
PORT=5001
```

Lalu jalankan lagi: `python run.py`

**Cara 2: Tutup aplikasi yang pakai port 5000**
Di Windows (PowerShell):

```powershell
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

#### Error: "No module named 'flask'"

Dependencies belum terinstall. Jalankan:

```bash
pip install -r requirements_web.txt
```

#### Error: "Cannot connect to database"

Pastikan folder `data/` ada:

```bash
mkdir data
```

---

## LANGKAH 5: AKSES APLIKASI

### 5.1 Buka Browser

Setelah server berjalan, buka web browser dan akses:

```
http://localhost:5000
```

atau

```
http://127.0.0.1:5000
```

### 5.2 Login ke Aplikasi

**Username/Password Default:**

- Username: `admin`
- Password: Lihat di database atau `.env` (jika dikonfigurasi)

Jika tidak tahu password, Anda bisa:

1. Reset melalui `/reset-password` (jika tersedia)
2. Atau restart aplikasi dengan admin baru di `.env`

### 5.3 Homepage Aplikasi

Setelah login sukses, Anda akan melihat:

- Dashboard dengan statistik absensi
- Menu navigasi di atas/samping
- Opsi untuk tambah siswa, tandai absensi, lihat laporan

---

## 📊 MENU UTAMA APLIKASI

### 1. **Beranda (Dashboard)**

- Menampilkan statistik absensi hari ini
- Total siswa
- Jumlah hadir/tidak hadir

### 2. **Siswa (Students)**

- **Tambah Siswa**: Registrasi siswa baru + upload foto
- **Daftar Siswa**: Lihat semua siswa yang terdaftar
- **Hapus Siswa**: Hapus data siswa

### 3. **Absensi (Attendance)**

- **Mark Attendance**: Tandai kehadiran via camera (jika tersedia)
- **Input Manual**: Tandai kehadiran secara manual
- **Lihat Absensi**: Lihat riwayat absensi

### 4. **Laporan (Reports)**

- **By Date Range**: Lihat absensi per periode
- **Export Excel**: Download laporan ke file Excel

### 5. **Pengaturan (Settings)**

- Ubah jam session (pagi/siang)
- Atur sistem (jika admin)

---

## 🛑 STOP APLIKASI

Untuk menghentikan aplikasi:

**Di Terminal/Command Prompt:**

```bash
Tekan CTRL + C
```

**Output:**

```
^C
Shutting down...
```

Setelah itu, aplikasi akan berhenti dan terminal siap menerima perintah lagi.

---

## 🔄 MENJALANKAN ULANG APLIKASI

Setiap kali ingin menjalankan aplikasi lagi:

### Langkah Singkat:

1. Buka Terminal/Command Prompt
2. Navigasi ke folder: `cd d:\Face_Recognition`
3. Aktifkan virtual environment: `.venv\Scripts\activate` (Windows)
4. Jalankan: `python run.py`
5. Buka browser: `http://localhost:5000`

---

## 📁 STRUKTUR FOLDER APLIKASI

```
Face_Recognition/
├── .venv/                    # Virtual environment (jangan edit)
├── app/
│   ├── __init__.py          # Inisialisasi Flask app
│   ├── config.py            # Konfigurasi
│   ├── models/              # Database models (Student, Attendance, etc)
│   ├── routes/              # URL routes (login, dashboard, etc)
│   ├── services/            # Business logic (face recognition, etc)
│   ├── templates/           # HTML templates
│   └── static/              # CSS, JS, images
├── data/
│   ├── attendance.db        # Database SQLite
│   ├── backups/             # Backup database otomatis
│   └── photos/              # Foto siswa
├── run.py                   # File utama untuk menjalankan app
├── .env                     # Konfigurasi lingkungan
├── .env.example             # Template .env
├── requirements_web.txt     # Daftar dependencies
├── QUICKSTART.md            # Panduan cepat (bahasa Indonesia)
├── README_WEB.md            # README lengkap
└── SETUP_GUIDE.md           # Panduan setup
```

---

## ✅ CHECKLIST SETUP

Gunakan checklist ini untuk memastikan semua setup dengan benar:

- [ ] Python 3.10+ sudah terinstall
- [ ] Virtual environment sudah dibuat (folder `.venv`)
- [ ] Virtual environment sudah diaktifkan (prompt menunjukkan `(.venv)`)
- [ ] Dependencies sudah diinstall (`pip install -r requirements_web.txt`)
- [ ] File `.env` sudah dikopy dari `.env.example`
- [ ] Folder `data/` sudah ada
- [ ] Server berjalan tanpa error (`python run.py`)
- [ ] Bisa akses `http://localhost:5000` di browser
- [ ] Bisa login dengan akun admin

---

## 🆘 TROUBLESHOOTING UMUM

### Q: Virtual environment tidak aktif

**A:** Jalankan:

```bash
# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

### Q: ModuleNotFoundError (missing dependencies)

**A:** Install dependencies:

```bash
pip install -r requirements_web.txt
```

### Q: Port 5000 sudah dipakai

**A:** Ubah PORT di `.env` atau tutup aplikasi lain yang pakai port tersebut

### Q: Lupa password admin

**A:** Reset database atau ubah di `.env`:

```env
AUTO_CREATE_DEFAULT_ADMIN=1
```

### Q: Database error / corruption

**A:** Restore dari backup di folder `data/backups/` atau hapus `data/attendance.db` untuk membuat baru

### Q: Camera tidak terdeteksi

**A:** Ini normal jika face_recognition tidak terinstall. Fitur camera akan disabled

### Q: Halaman blank atau error 500

**A:**

1. Cek console untuk error message
2. Pastikan `.env` sudah dikopy
3. Restart aplikasi
4. Cek folder `data/` ada dan bisa ditulis

---

## 📚 DOKUMENTASI LENGKAP

Untuk informasi lebih detail, baca file dokumentasi lainnya:

- `QUICKSTART.md` - Panduan cepat (Bahasa Indonesia)
- `README_WEB.md` - Dokumentasi lengkap
- `SETUP_GUIDE.md` - Panduan setup dengan detail
- `DEVELOPMENT.md` - Untuk development/coding

---

## 🎉 SELESAI!

Jika semua langkah di atas sudah dilakukan dengan benar, selamat!

Aplikasi **Face Recognition Attendance System** sudah siap digunakan.

### Langkah Berikutnya:

1. ✅ Login dengan akun admin
2. ✅ Tambah beberapa siswa
3. ✅ Coba fitur absensi
4. ✅ Export laporan
5. ✅ Customize pengaturan

**Selamat menggunakan! 🚀**

---

## 📞 BUTUH BANTUAN?

Jika ada pertanyaan atau masalah:

1. Baca troubleshooting di atas
2. Cek console output untuk error message
3. Baca dokumentasi lainnya (README_WEB.md, SETUP_GUIDE.md)
4. Buat issue di repository

---

**Dibuat: 2026-06-12**  
**Aplikasi: Face Recognition Attendance System v2.0**
