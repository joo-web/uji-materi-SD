import streamlit as st
import sqlite3
import random
import time
import pandas as pd
import os
import base64
import requests

# --- SETUP HALAMAN UTAMA ---
st.set_page_config(page_title="Uji Kompetensi SD", page_icon="🎓", layout="centered")

# --- FUNGSI BACKGROUND ---
def set_background():
    folder_script = os.path.dirname(os.path.abspath(__file__))
    image_file = os.path.join(folder_script, 'background2.jpg')
    if os.path.exists(image_file):
        with open(image_file, "rb") as image_file_read:
            encoded_string = base64.b64encode(image_file_read.read()).decode()
        st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url("data:image/jpeg;base64,{encoded_string}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
        )

set_background()

# --- INISIALISASI SESSION STATE ---
# Session state digunakan agar memori aplikasi tidak hilang saat halaman di-refresh
if 'page' not in st.session_state:
    st.session_state.page = 'mulai'
if 'kategori_list' not in st.session_state:
    st.session_state.kategori_list = ["Perhitungan Dasar", "Soal Cerita", "Penalaran"]
if 'idx_kategori' not in st.session_state:
    st.session_state.idx_kategori = 0
if 'level_saat_ini' not in st.session_state:
    st.session_state.level_saat_ini = 1
if 'nyawa' not in st.session_state:
    st.session_state.nyawa = 2
if 'skor_per_kategori' not in st.session_state:
    st.session_state.skor_per_kategori = {"Perhitungan Dasar": 0, "Soal Cerita": 0, "Penalaran": 0}
if 'soal_terpakai' not in st.session_state:
    st.session_state.soal_terpakai = []
if 'soal_aktif' not in st.session_state:
    st.session_state.soal_aktif = None

# --- FUNGSI DATABASE ---
def ambil_soal_random(kelas, kategori, level):
    db_path = 'bank_soal.db'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pertanyaan, opsi_a, opsi_b, opsi_c, opsi_d, kunci 
            FROM tabel_soal WHERE kelas = ? AND kategori = ? AND level = ?
        ''', (kelas, kategori, level))
        soal_soal = cursor.fetchall()
        conn.close()
        
        if soal_soal:
            soal_tersedia = [s for s in soal_soal if s[0] not in st.session_state.soal_terpakai]
            if not soal_tersedia:
                soal_tersedia = soal_soal # Reset jika habis
                
            soal_terpilih = random.choice(soal_tersedia)
            return {
                "soal": soal_terpilih[0],
                "opsi": [str(soal_terpilih[1]), str(soal_terpilih[2]), str(soal_terpilih[3]), str(soal_terpilih[4])],
                "jawaban": int(soal_terpilih[5])
            }
        return None
    except Exception as e:
        st.error(f"Error Database: {e}")
        return None

def simpan_hasil(nama, kelas, sekolah, skor_num, skor_lit, skor_pen, total, durasi):
    db_path = 'bank_soal.db'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hasil_ujian (
                id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, kelas TEXT, sekolah TEXT,
                skor_numerik INTEGER, skor_literasi INTEGER, skor_penalaran INTEGER, 
                total_skor INTEGER, durasi REAL
            )
        ''')
        cursor.execute('''
            INSERT INTO hasil_ujian (nama, kelas, sekolah, skor_numerik, skor_literasi, skor_penalaran, total_skor, durasi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nama, kelas, sekolah, skor_num, skor_lit, skor_pen, total, durasi))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Gagal menyimpan data: {e}")

# --- HALAMAN 1: MULAI ---
def halaman_mulai():
    st.title("Aplikasi Uji Kompetensi SD Adaptif")
    st.markdown("### ISI BIODATA DULU YAAA")
    st.write("Pastikan sudah memiliki alat tulis dan buku")
    
    st.info("""
    **Sistem Penilaian:**
    - **Numerik (Perhitungan Dasar):** 3 Poin per soal
    - **Literasi (Soal Cerita):** 5 Poin per soal
    - **Penalaran:** 8 Poin per soal
    """)
    
    with st.form("form_mulai"):
        nama = st.text_input("Nama Lengkap :")
        kelas = st.selectbox("Kelas :", ["Kelas 3", "Kelas 4", "Kelas 5"])
        sekolah = st.text_input("Asal Sekolah :")
        submit = st.form_submit_button("MULAI UJIAN", type="primary")
        
        if submit:
            if nama and kelas and sekolah:
                st.session_state.nama = nama
                st.session_state.kelas = kelas
                st.session_state.sekolah = sekolah
                st.session_state.waktu_mulai = time.time()
                st.session_state.page = 'kuis'
                st.rerun()
            else:
                st.warning("⚠️ Nama, Kelas, dan Asal Sekolah harus diisi terlebih dahulu!")

# --- HALAMAN 2: KUIS ---
def halaman_kuis():
    kategori_aktif = st.session_state.kategori_list[st.session_state.idx_kategori]
    level_aktif = st.session_state.level_saat_ini
    
    # Header Kuis
    st.progress(level_aktif / 5)
    st.divider()

    # Ambil soal jika belum ada di state
    if st.session_state.soal_aktif is None:
        soal_baru = ambil_soal_random(st.session_state.kelas, kategori_aktif, level_aktif)
        if soal_baru:
            st.session_state.soal_aktif = soal_baru
            st.session_state.soal_terpakai.append(soal_baru['soal'])
        else:
            st.error(f"Soal tidak ditemukan untuk {st.session_state.kelas}, {kategori_aktif}, Level {level_aktif}")
            st.stop()

    soal = st.session_state.soal_aktif
    
    # Tampilkan Soal & Opsi
    st.subheader(soal['soal'])
    pilihan_user = st.radio("Pilih jawaban Anda:", soal['opsi'], index=None)
    
    st.write("")
    btn_text = "Selesaikan Ujian" if st.session_state.idx_kategori == len(st.session_state.kategori_list) - 1 and level_aktif == 5 else "Jawab & Lanjut"
    
    if st.button(btn_text, type="primary", use_container_width=True):
        if pilihan_user is None:
            st.warning("Silakan pilih jawaban terlebih dahulu!")
            return
            
        # Cek Jawaban
        idx_pilihan = soal['opsi'].index(pilihan_user)
        if idx_pilihan == soal['jawaban']:
            # BENAR
            st.session_state.skor_per_kategori[kategori_aktif] += 1
            st.session_state.level_saat_ini += 1
            
            if st.session_state.level_saat_ini > 5:
                st.session_state.idx_kategori += 1
                st.session_state.level_saat_ini = 1
                st.session_state.nyawa = 2
        else:
            # SALAH
            st.session_state.nyawa -= 1
            if st.session_state.nyawa <= 0:
                st.session_state.idx_kategori += 1
                st.session_state.level_saat_ini = 1
                st.session_state.nyawa = 2
        
        # Kosongkan soal aktif untuk mengambil soal baru di rerun berikutnya
        st.session_state.soal_aktif = None
        
        # Cek apakah ujian selesai
        if st.session_state.idx_kategori >= len(st.session_state.kategori_list):
            st.session_state.page = 'hasil'
            st.session_state.waktu_selesai = time.time()
        
        st.rerun()

# --- HALAMAN 3: HASIL ---
def halaman_hasil():
    if 'waktu_selesai' in st.session_state:
        durasi = st.session_state.waktu_selesai - st.session_state.waktu_mulai
    else:
        durasi = 0
        
    menit, detik = int(durasi // 60), int(durasi % 60)
    
    skor_md = st.session_state.skor_per_kategori["Perhitungan Dasar"]
    skor_ms = st.session_state.skor_per_kategori["Soal Cerita"]
    skor_pp = st.session_state.skor_per_kategori["Penalaran"]
    
    # Persentase (sesuai Tkinter)
    pct_md = int((skor_md / 5) * 100)
    pct_ms = int((skor_ms / 5) * 100)
    pct_pp = int((skor_pp / 5) * 100)
    
    # Hitung bobot
    skor_num = skor_md * 3
    skor_lit = skor_ms * 5
    skor_pen = skor_pp * 8
    total_poin = skor_num + skor_lit + skor_pen
    
    st.markdown("<h3 style='text-align: center; font-size: 26px;'>✨ Performa Anda ✨</h3>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='text-align: left; font-size:16px; margin-bottom: 20px; background-color: rgba(255,255,255,0.7); padding: 15px; border-radius: 10px;'>
        Nama : <b>{st.session_state.nama.upper()}</b><br>
        Kelas : <b>{st.session_state.kelas}</b><br>
        Asal Sekolah : <b>{st.session_state.sekolah}</b><br>
        Waktu Pengerjaan : <b>{menit} menit {detik} detik</b><br>
        Total Poin : <b>{total_poin}</b>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("### Numerik")
    st.progress(pct_md / 100, text=f"{pct_md}%")
    
    st.markdown("### Literasi")
    st.progress(pct_ms / 100, text=f"{pct_ms}%")
    
    st.markdown("### Penalaran")
    st.progress(pct_pp / 100, text=f"{pct_pp}%")
    
    # Simpan ke DB satu kali
    if 'sudah_disimpan' not in st.session_state:
        simpan_hasil(st.session_state.nama, st.session_state.kelas, st.session_state.sekolah, skor_num, skor_lit, skor_pen, total_poin, durasi)
        st.session_state.sudah_disimpan = True
        
        # --- FITUR KIRIM OTOMATIS KE GOOGLE DRIVE (GOOGLE SHEETS) ---
        # Ganti teks di bawah dengan URL dari Google Apps Script milikmu
        url_gdrive = "MASUKKAN_URL_WEB_APP_GOOGLE_APPS_SCRIPT_DI_SINI"
        
        if url_gdrive != "MASUKKAN_URL_WEB_APP_GOOGLE_APPS_SCRIPT_DI_SINI":
            data_payload = {
                "nama": st.session_state.nama.upper(),
                "kelas": st.session_state.kelas,
                "sekolah": st.session_state.sekolah,
                "skor": total_poin,
                "waktu": f"{menit}m {detik}s",
                "numerik": f"{pct_md}%",
                "literasi": f"{pct_ms}%",
                "penalaran": f"{pct_pp}%"
            }
            try:
                requests.post(url_gdrive, json=data_payload, timeout=5)
            except Exception as e:
                pass # Jika internet gagal/terputus, biarkan saja agar tidak mengganggu aplikasi

    st.write("")
    
    # Siapkan teks laporan untuk fitur Download
    laporan_teks = f"=== PERFORMA SISWA ===\nNama : {st.session_state.nama.upper()}\nKelas : {st.session_state.kelas}\nSekolah : {st.session_state.sekolah}\nWaktu : {menit} menit {detik} detik\nTotal Poin : {total_poin}\n\n=== PENGUASAAN MATERI ===\n- Numerik : {pct_md}%\n- Literasi : {pct_ms}%\n- Penalaran : {pct_pp}%"
    
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        st.download_button("Download Laporan", data=laporan_teks, file_name=f"Evaluasi_{st.session_state.nama}.txt", use_container_width=True)
    with col_btn2:
        if st.button("Lihat RANK", use_container_width=True, type="primary"):
            st.session_state.page = 'rank'
            st.rerun()
    with col_btn3:
        if st.button("Beranda", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# --- HALAMAN 4: RANKING ---
def halaman_rank():
    kelas_filter = st.session_state.get('kelas', 'Kelas 3')
    st.title(f"Peringkat Siswa - {kelas_filter}")
    st.write(f"Peringkat Siswa {kelas_filter} Berdasarkan Poin dan Waktu Tercepat")
    
    db_path = 'bank_soal.db'
    try:
        conn = sqlite3.connect(db_path)
        query = "SELECT nama AS Nama, kelas AS Kelas, sekolah AS 'Asal Sekolah', total_skor AS 'Total Poin', durasi AS 'Waktu Tercepat' FROM hasil_ujian WHERE kelas = ? ORDER BY total_skor DESC, durasi ASC"
        df = pd.read_sql_query(query, conn, params=(kelas_filter,))
        conn.close()
        
        # Format durasi seperti Tkinter
        df['Waktu Tercepat'] = df['Waktu Tercepat'].apply(lambda x: f"{int(x//60)}m {int(x%60)}s")
        df.index = df.index + 1 # Rank mulai dari 1
        df.index.name = "Peringkat"
        
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Gagal memuat ranking: {e}")
        
    if st.button("Kembali", type="primary"):
        st.session_state.page = 'hasil'
        st.rerun()

# --- ROUTING HALAMAN ---
if st.session_state.page == 'mulai':
    halaman_mulai()
elif st.session_state.page == 'kuis':
    halaman_kuis()
elif st.session_state.page == 'hasil':
    halaman_hasil()
elif st.session_state.page == 'rank':
    halaman_rank()