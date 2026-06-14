import pandas as pd
import sqlite3
import os

def konversi_excel_ke_db():
    # 1. Dapatkan lokasi folder tempat script ini berada secara otomatis
    folder_script = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Gabungkan lokasi folder dengan nama file
    nama_txt = os.path.join(folder_script, 'bank-soal-SD.txt')
    nama_db = os.path.join(folder_script, 'bank_soal.db')
    
    print(f"Mencari file di: {nama_txt}...")
    
    if not os.path.exists(nama_txt):
        print("❌ ERROR: File Teks tidak ditemukan!")
        print("Pastikan nama file benar ('bank-soal-SD.txt') dan ada di folder yang sama dengan script ini.")
        return

    try:
        print("Membaca data dari file teks...")
        df = pd.read_csv(nama_txt, delimiter='\t')
        
        print("Membuat/menyambungkan ke database SQLite...")
        conn = sqlite3.connect(nama_db)
        
        print("Memindahkan data ke tabel database...")
        df.to_sql('tabel_soal', conn, if_exists='replace', index=False)
        
        conn.close()
        print(f"✅ SUKSES! File database berhasil dibuat di:\n{nama_db}")
        print(f"Total soal yang berhasil dimasukkan: {len(df)} soal.")
        
    except Exception as e:
        print(f"❌ Terjadi kesalahan saat memproses data: {e}")

if __name__ == "__main__":
    konversi_excel_ke_db()