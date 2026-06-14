import streamlit as st
import sqlite3
import random
import time
import pandas as pd
import os

# --- SETUP HALAMAN UTAMA ---
st.set_page_config(page_title="Uji Kompetensi SD", page_icon="🎓", layout="centered")

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
    st.title("🎓 Uji Kemampuan Matematika Adaptif")
    st.write("Silakan lengkapi data diri siswa sebelum memulai ujian.")
    
    with st.form("form_mulai"):
        nama = st.text_input("Nama Lengkap:")
        kelas = st.selectbox("Kelas:", ["Kelas 3", "Kelas 4", "Kelas 5"])
        sekolah = st.text_input("Asal Sekolah:")
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
                st.warning("⚠️ Mohon lengkapi semua data terlebih dahulu!")

# --- HALAMAN 2: KUIS ---
def halaman_kuis():
    kategori_aktif = st.session_state.kategori_list[st.session_state.idx_kategori]
    level_aktif = st.session_state.level_saat_ini
    
    # Header Kuis
    col1, col2 = st.columns(2)
    col1.markdown(f"**Kategori:** {kategori_aktif}")
    col2.markdown(f"**Level:** {level_aktif} dari 5 | **Nyawa:** {'❤️' * st.session_state.nyawa}")
    st.progress(level_aktif / 5)
    st.divider()

    # Ambil soal jika belum ada di state
    if st.session_state.soal_aktif is None:
        soal_baru = ambil_soal_random(st.session_state.kelas, kategori_aktif, level_aktif)
        if soal_baru:
            st.session_state.soal_aktif = soal_baru
            st.session_state.soal_terpakai.append(soal_baru['soal'])
        else:
            st.error("Gagal memuat soal dari database.")
            st.stop()

    soal = st.session_state.soal_aktif
    
    # Tampilkan Soal & Opsi
    st.subheader(soal['soal'])
    pilihan_user = st.radio("Pilih jawaban Anda:", soal['opsi'], index=None)
    
    st.write("")
    if st.button("Jawab & Lanjut", type="primary", use_container_width=True):
        if pilihan_user is None:
            st.warning("Pilih jawaban terlebih dahulu!")
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
        
        st.rerun()

# --- HALAMAN 3: HASIL ---
def halaman_hasil():
    durasi = time.time() - st.session_state.waktu_mulai
    menit, detik = int(durasi // 60), int(durasi % 60)
    
    skor_md = st.session_state.skor_per_kategori["Perhitungan Dasar"]
    skor_ms = st.session_state.skor_per_kategori["Soal Cerita"]
    skor_pp = st.session_state.skor_per_kategori["Penalaran"]
    
    # Hitung bobot
    skor_num = skor_md * 3
    skor_lit = skor_ms * 5
    skor_pen = skor_pp * 8
    total_poin = skor_num + skor_lit + skor_pen
    
    st.success("🎉 Ujian Selesai!")
    st.header("Laporan Performa Siswa")
    st.write(f"**Nama:** {st.session_state.nama.upper()} | **Kelas:** {st.session_state.kelas} | **Sekolah:** {st.session_state.sekolah}")
    st.write(f"**Waktu Pengerjaan:** {menit} menit {detik} detik")
    st.markdown(f"### Total Poin Anda: {total_poin}")
    st.divider()
    
    st.subheader("Detail Penguasaan Materi")
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Numerik", value=f"{(skor_md/5)*100}%")
    col2.metric(label="Literasi", value=f"{(skor_ms/5)*100}%")
    col3.metric(label="Penalaran", value=f"{(skor_pp/5)*100}%")
    
    # Simpan ke DB satu kali
    if 'sudah_disimpan' not in st.session_state:
        simpan_hasil(st.session_state.nama, st.session_state.kelas, st.session_state.sekolah, skor_num, skor_lit, skor_pen, total_poin, durasi)
        st.session_state.sudah_disimpan = True

    st.write("")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Lihat Papan Peringkat (RANK)", use_container_width=True):
            st.session_state.page = 'rank'
            st.rerun()
    with col_btn2:
        if st.button("Kembali ke Beranda", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# --- HALAMAN 4: RANKING ---
def halaman_rank():
    st.title("🏆 Papan Peringkat Global")
    
    db_path = 'bank_soal.db'
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT nama AS Nama, kelas AS Kelas, sekolah AS Sekolah, total_skor AS 'Total Poin', durasi AS 'Waktu (Detik)' FROM hasil_ujian ORDER BY total_skor DESC, durasi ASC", conn)
        conn.close()
        
        # Ubah format detik jadi lebih mudah dibaca
        df['Waktu (Detik)'] = df['Waktu (Detik)'].apply(lambda x: f"{int(x//60)}m {int(x%60)}s")
        df.index = df.index + 1 # Rank mulai dari 1
        
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Gagal memuat ranking: {e}")
        
    if st.button("← Kembali", type="primary"):
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