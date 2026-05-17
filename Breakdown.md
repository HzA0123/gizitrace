# GiziTrace — Feature Breakdown & Development Scope
**Version:** MVP Hackathon  
**Stack:** Next.js · FastAPI · Supabase · OpenCV · Vercel · HuggingFace Spaces  
**Author:** Project Manager Review

---

## 📐 Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js)                   │
│  ┌──────────────┐  ┌─────────────────┐  ┌────────────┐  │
│  │  QR Scanner  │  │ School Dashboard│  │ Gov Dashboard│ │
│  │  (Siswa)     │  │ (Kepala Sekolah)│  │ (Dinas)    │  │
│  └──────┬───────┘  └────────┬────────┘  └─────┬──────┘  │
└─────────┼───────────────────┼─────────────────┼─────────┘
          │                   │                 │
          ▼                   ▼                 ▼
┌─────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                        │
│   /feedback  /verify  /anomaly  /recommend  /dashboard   │
└────────────┬────────────────────┬────────────────────────┘
             │                    │
     ┌───────▼──────┐    ┌────────▼──────────┐
     │   Supabase   │    │  AI Service        │
     │  PostgreSQL  │    │  (HuggingFace)     │
     │  Auth        │    │  OpenCV · Sklearn  │
     │  Storage     │    │  Weighted Scoring  │
     └──────────────┘    └───────────────────┘
```

---

## 🗄️ DATABASE SCHEMA (Supabase PostgreSQL)

### Table: `schools`
| Column | Type | Keterangan |
|---|---|---|
| id | UUID PK | |
| name | VARCHAR | Nama sekolah |
| address | TEXT | Alamat |
| district | VARCHAR | Kecamatan |
| city | VARCHAR | Kota/Kabupaten |
| total_students | INTEGER | Jumlah siswa terdaftar |
| qr_token | VARCHAR UNIQUE | Token unik untuk QR sekolah |
| created_at | TIMESTAMP | |

### Table: `classes`
| Column | Type | Keterangan |
|---|---|---|
| id | UUID PK | |
| school_id | UUID FK → schools | |
| name | VARCHAR | e.g. "7A", "8B" |
| grade | INTEGER | e.g. 7, 8, 9 |
| student_count | INTEGER | Jumlah siswa di kelas ini |

### Table: `vendors`
| Column | Type | Keterangan |
|---|---|---|
| id | UUID PK | |
| name | VARCHAR | Nama vendor/SPPG |
| contact | VARCHAR | |
| assigned_schools | UUID[] | Array school_id |
| created_at | TIMESTAMP | |

### Table: `deliveries`
| Column | Type | Keterangan |
|---|---|---|
| id | UUID PK | |
| vendor_id | UUID FK → vendors | |
| school_id | UUID FK → schools | |
| date | DATE | Tanggal distribusi |
| reported_portions | INTEGER | Laporan vendor |
| menu_description | TEXT | Deskripsi menu hari ini |
| delivery_confirmed | BOOLEAN | Default: false |
| confirmed_at | TIMESTAMP | Saat staff sekolah scan |
| confirmed_by | VARCHAR | Staff yang konfirmasi |

### Table: `feedback`
| Column | Type | Keterangan |
|---|---|---|
| id | UUID PK | |
| school_id | UUID FK → schools | |
| class_id | UUID FK → classes | |
| delivery_id | UUID FK → deliveries | |
| date | DATE | |
| response_full | INTEGER | Jumlah "Habis" |
| response_half | INTEGER | Jumlah "Setengah" |
| response_reject | INTEGER | Jumlah "Nggak suka" |
| total_responses | INTEGER | Total scan pada sesi ini |
| created_at | TIMESTAMP | |

### Table: `food_photos`
| Column | Type | Keterangan |
|---|---|---|
| id | UUID PK | |
| delivery_id | UUID FK → deliveries | |
| school_id | UUID FK → schools | |
| photo_url | TEXT | Path di Supabase Storage |
| ai_waste_percent | FLOAT | Output OpenCV (0-100) |
| ai_confidence | FLOAT | Confidence score model |
| processed_at | TIMESTAMP | |
| fallback_manual | BOOLEAN | True jika AI gagal/low confidence |

### Table: `anomalies`
| Column | Type | Keterangan |
|---|---|---|
| id | UUID PK | |
| delivery_id | UUID FK → deliveries | |
| school_id | UUID FK → schools | |
| type | ENUM | `ghost_delivery` · `scan_spike` · `zero_waste` · `low_adoption` |
| description | TEXT | Penjelasan anomali |
| severity | ENUM | `low` · `medium` · `high` |
| is_resolved | BOOLEAN | Default: false |
| created_at | TIMESTAMP | |

### Table: `menu_history`
| Column | Type | Keterangan |
|---|---|---|
| id | UUID PK | |
| school_id | UUID FK → schools | |
| menu_name | VARCHAR | Nama menu |
| date | DATE | |
| acceptance_rate | FLOAT | % yang habis |
| avg_waste_percent | FLOAT | Dari foto AI |
| total_feedback | INTEGER | Jumlah responden |

---

## 🔐 AUTHENTICATION

### Supabase Auth
| Role | Metode Login | Akses |
|---|---|---|
| Staff Sekolah | OTP via email | Dashboard sekolah, konfirmasi delivery |
| Kepala Sekolah | OTP via email | Dashboard sekolah full |
| Admin Dinas | Email + password | Dashboard pemerintah |
| Siswa/Umum | **Tanpa login** | QR feedback page saja |
| Vendor | Email + password | Generate QR delivery, lihat feedback |

> **Catatan:** Siswa tidak perlu akun. QR feedback page adalah public route dengan validasi token sekolah dari URL.

---

## 📱 FRONTEND FEATURES (Next.js + Tailwind)

### 1. QR Feedback Page (Public — No Login)
**Route:** `/feedback?token={qr_token}`

| # | Fitur | Detail |
|---|---|---|
| F-01 | Validasi token sekolah | Cek `qr_token` ke database, tampilkan nama sekolah |
| F-02 | Pilih kelas | Grid tombol kelas (7A, 7B, 8A, dst) |
| F-03 | Tampil menu hari ini | Ambil dari `deliveries` berdasarkan tanggal hari ini |
| F-04 | Tombol feedback 3 opsi | 😋 Habis · 😐 Setengah · 😒 Nggak suka |
| F-05 | Konfirmasi & terima kasih | Setelah tap → layar konfirmasi, tidak bisa submit ulang (session-based) |
| F-06 | Responsive mobile-first | Dioptimalkan untuk HP siswa |
| F-07 | Fallback menu kosong | Jika belum ada delivery hari ini → tampilkan pesan informatif |

---

### 2. Staff Sekolah — Konfirmasi Pengiriman
**Route:** `/school/delivery`

| # | Fitur | Detail |
|---|---|---|
| F-08 | Login staff | Via Supabase Auth OTP email |
| F-09 | Scan QR paket vendor | Gunakan `html5-qrcode` / `jsQR` via kamera |
| F-10 | Tampil detail delivery | Nama vendor, jumlah porsi dilaporkan, menu |
| F-11 | Konfirmasi penerimaan | Tap tombol konfirmasi → update `delivery_confirmed = true` |
| F-12 | Input catatan | Opsional: tambah catatan jika ada masalah |
| F-13 | Upload foto sisa (opsional) | Setelah jam makan, staff foto sisa → kirim ke AI service |

---

### 3. Dashboard Sekolah
**Route:** `/school/dashboard`

| # | Fitur | Detail |
|---|---|---|
| F-14 | Ringkasan hari ini | Porsi terkirim vs total feedback, waste rate hari ini |
| F-15 | Grafik konsumsi mingguan | Line chart: % habis per hari (7 hari terakhir) |
| F-16 | Breakdown per kelas | Tabel: kelas · total responden · % habis · % reject |
| F-17 | Riwayat delivery | List pengiriman 30 hari terakhir + status konfirmasi |
| F-18 | Alert anomali | Badge merah jika ada anomali aktif, klik untuk detail |
| F-19 | Menu terpopuler | Top 3 menu dengan acceptance rate tertinggi |
| F-20 | QR sekolah | Tampilkan + download QR sekolah untuk dicetak |

---

### 4. Dashboard Pemerintah / Dinas
**Route:** `/gov/dashboard`

| # | Fitur | Detail |
|---|---|---|
| F-21 | Peta sebaran sekolah | Map interaktif: warna berdasarkan waste rate (hijau/kuning/merah) |
| F-22 | Agregat kota/kabupaten | Total porsi didistribusikan, total feedback, avg waste rate |
| F-23 | Tabel sekolah | Sortable: nama sekolah · delivery rate · acceptance rate · anomali |
| F-24 | Anomali aktif | List semua anomali belum resolve, filter per severity |
| F-25 | Rekomendasi menu | Top 5 menu rekomendasi berdasarkan data historis seluruh sekolah |
| F-26 | Export laporan | Download CSV / PDF ringkasan mingguan |
| F-27 | Filter periode | Pilih rentang tanggal untuk semua widget |

---

### 5. Vendor Portal
**Route:** `/vendor`

| # | Fitur | Detail |
|---|---|---|
| F-28 | Generate QR delivery | Input: sekolah tujuan, jumlah porsi, deskripsi menu → generate QR unik |
| F-29 | Riwayat pengiriman | List delivery + status konfirmasi dari sekolah |
| F-30 | Feedback summary | Lihat acceptance rate dari sekolah yang dilayani |

---

## ⚙️ BACKEND API (FastAPI — HuggingFace Spaces)

### Endpoint: Feedback & Delivery

| Method | Endpoint | Fungsi |
|---|---|---|
| POST | `/feedback/submit` | Terima data feedback QR dari siswa |
| GET | `/feedback/today/{school_id}` | Ambil rekapitulasi feedback hari ini |
| POST | `/delivery/confirm` | Konfirmasi penerimaan delivery oleh staff sekolah |
| POST | `/delivery/create` | Vendor buat delivery baru + generate QR |
| GET | `/delivery/{school_id}` | List delivery per sekolah |

### Endpoint: AI Service

| Method | Endpoint | Fungsi |
|---|---|---|
| POST | `/ai/analyze-photo` | Terima gambar → output `waste_percent` + `confidence` |
| GET | `/ai/recommend-menu/{school_id}` | Output top N rekomendasi menu |
| GET | `/ai/anomaly-check/{school_id}` | Trigger cek anomali manual |

### Endpoint: Dashboard

| Method | Endpoint | Fungsi |
|---|---|---|
| GET | `/dashboard/school/{school_id}` | Semua data dashboard sekolah |
| GET | `/dashboard/gov` | Agregat data semua sekolah |
| GET | `/dashboard/anomalies` | List anomali aktif |
| GET | `/report/export/{school_id}` | Generate CSV ringkasan |

### Endpoint: Auth & Admin

| Method | Endpoint | Fungsi |
|---|---|---|
| POST | `/school/register` | Onboarding sekolah baru + generate QR token |
| POST | `/vendor/register` | Onboarding vendor baru |
| GET | `/qr/validate/{token}` | Validasi token QR sekolah |

---

## 🤖 AI FEATURES

### AI-01: Food Waste Estimation (OpenCV)
**Library:** OpenCV (Python) + Roboflow API (fallback)  
**Deploy:** FastAPI endpoint `/ai/analyze-photo`

**Cara Kerja:**
```
Input: Foto piring sisa makanan (JPEG/PNG)
    ↓
Preprocessing: Resize → Denoise → Normalize
    ↓
Color Segmentation: Deteksi area makanan vs piring kosong
    (HSV masking untuk pisahkan makanan dari piring putih)
    ↓
Contour Detection: Hitung rasio area makanan / total area piring
    ↓
Output: { waste_percent: 18.5, confidence: 0.82 }
```

**Rules:**
- Confidence < 0.6 → `fallback_manual = true` → minta input manual dari guru
- Foto buram / gelap → reject dengan pesan error spesifik
- Target akurasi: >70% korelasi dengan estimasi manual

---

### AI-02: Anomaly Detection (Rule-Based + Isolation Forest)
**Library:** Scikit-learn (Isolation Forest) + custom threshold rules  
**Trigger:** Otomatis setiap hari setelah jam 14.00, atau manual via endpoint

**Rules yang Diimplementasi:**

| Tipe Anomali | Rule | Severity |
|---|---|---|
| `ghost_delivery` | Vendor lapor N porsi, tapi adoption rate < 30% dari siswa terdaftar | HIGH |
| `zero_waste` | Waste rate tiba-tiba 0% padahal 3 hari sebelumnya >30% | MEDIUM |
| `scan_spike` | Total scan > 120% dari student_count sekolah (ada yang scan berkali-kali) | MEDIUM |
| `low_adoption` | Scan < 20% dari student_count 3 hari berturut-turut | LOW |
| `no_delivery` | Tidak ada delivery confirmed tapi hari sekolah aktif | HIGH |

**Isolation Forest** (untuk pattern yang lebih kompleks):
- Input features: `adoption_rate`, `waste_percent`, `response_reject_ratio`, `scan_duration`
- Dilatih ulang tiap minggu dengan data kumulatif
- Output: anomaly score → jika < threshold → flag sebagai `anomali potensial`

---

### AI-03: Menu Recommendation (Weighted Scoring)
**Library:** Pandas + NumPy (pure Python, no heavy ML)  
**Trigger:** Dipanggil saat dashboard pemerintah/sekolah load section rekomendasi

**Formula Scoring:**
```python
score(menu) = (
    (acceptance_rate × 0.50) +      # % yang habis — bobot terbesar
    (1 - avg_waste_percent × 0.30) + # kebalikan waste rate
    (frequency_served × 0.20)        # seberapa sering pernah disajikan (familiarity)
)
```

**Output:** Top 5 menu dengan skor tertinggi per sekolah / per kecamatan  
**Fallback:** Jika data historis < 7 hari → tampilkan menu populer nasional (hardcoded seed data)

---

## 🔗 QR CODE SYSTEM

| Komponen | Detail |
|---|---|
| Format | URL: `https://gizitrace.app/feedback?token={qr_token}` |
| Generate | Saat onboarding sekolah → UUID unik di-hash jadi token pendek |
| Library frontend | `html5-qrcode` atau `jsQR` (untuk scan delivery QR oleh staff) |
| Library generate | `qrcode` (Python, di backend) |
| Masa berlaku | Permanent — tidak perlu ganti karena date diambil dari `NOW()` saat submit |
| Cetak | 1 QR per sekolah, A5, dicetak oleh admin dinas saat onboarding |

---

## 📦 HOSTING & INFRA

| Komponen | Service | Tier |
|---|---|---|
| Frontend | Vercel | Free |
| Backend API | HuggingFace Spaces (FastAPI) | Free |
| Database | Supabase PostgreSQL | Free (500MB) |
| Auth | Supabase Auth | Free |
| Storage (foto) | Supabase Storage | Free (1GB) |
| QR Scanner | html5-qrcode (CDN) | Free |
| **Total Biaya** | | **Rp 0** |

---

## 📋 MVP SCOPE — 24 JAM HACKATHON

### ✅ WAJIB DIBANGUN (Demo live)

| Fitur | Estimasi Waktu |
|---|---|
| Database schema setup (Supabase) | 1 jam |
| QR feedback page (F-01 s/d F-05) | 2 jam |
| Staff konfirmasi delivery (F-08 s/d F-11) | 1.5 jam |
| FastAPI endpoints: feedback submit + delivery confirm | 2 jam |
| AI food waste (OpenCV, basic version) | 2 jam |
| Anomaly detection (rule-based only, skip Isolation Forest) | 1 jam |
| Menu recommendation (weighted scoring) | 1 jam |
| Dashboard sekolah: 3 widget utama (F-14, F-15, F-16) | 2 jam |
| Dashboard pemerintah: agregat + anomali (F-21, F-24, F-25) | 2 jam |
| Vendor QR generate (F-28) | 1 jam |
| **Total** | **~15.5 jam** (ada buffer ~8 jam untuk bug fix + polish) |

### ⏳ POST-MVP (Pitch saja, tidak dibangun)
- Isolation Forest model
- Export CSV/PDF
- Peta interaktif sekolah (bisa pakai static marker dulu)
- Offline mode / PWA
- Integrasi sistem nasional BGN/Kemendikbud

---

## 🎯 DEMO FLOW (Urutan Presentasi ke Juri)

```
1. Vendor generate QR delivery (30 detik)
        ↓
2. Staff sekolah scan QR → konfirmasi terima (30 detik)
        ↓
3. Siswa scan QR sekolah → pilih kelas 7A → tap 😋 Habis (30 detik)
   (demo 5-6 klik dari device berbeda untuk simulasi ramai)
        ↓
4. Staff upload foto piring sisa → AI output "18% waste" (45 detik)
        ↓
5. Dashboard sekolah update real-time (30 detik)
        ↓
6. Dashboard pemerintah: anomali vendor muncul karena adoption rendah (30 detik)
        ↓
7. Rekomendasi menu muncul berdasarkan historis (30 detik)
        ↓
Total: ~4 menit demo + 1 menit elevator pitch
```

---

## ⚠️ RISIKO & MITIGASI

| Risiko | Dampak | Mitigasi |
|---|---|---|
| OpenCV accuracy rendah | AI feature tidak convincing | Siapkan demo dengan foto yang sudah dikalibrasi. Fallback manual selalu aktif |
| Supabase free tier lambat | Dashboard lemot saat demo | Cache query di backend, siapkan seed data lokal |
| QR scan tidak jalan di HP juri | Demo gagal | Siapkan URL langsung sebagai backup (tanpa scan) |
| Isolation Forest overfitting | Anomali salah deteksi | Skip untuk MVP, pakai rule-based saja |
| Tim kecil / solo | Tidak semua fitur selesai | Prioritas: QR flow + 1 dashboard + 1 AI. Yang lain mock UI |

---

*Dokumen ini adalah living document — update seiring progress development.*  
*Last reviewed: GiziTrace MVP — Aceh Hackathon 2026*