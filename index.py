import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Keuangan Cloud", page_icon="☁️")

# --- KONEKSI KE GOOGLE SHEETS ---
@st.cache_resource
def get_worksheet():
    # Mengambil kunci rahasia dari Streamlit Secrets
    secrets = st.secrets["gcp_service_account"]
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds = Credentials.from_service_account_info(secrets, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Buka Google Sheet (Pastikan nama file SAMA PERSIS dengan di Google Sheets)
    sh = client.open_by_key("1u8yYVDA61RKwRoQb4513T94sLmkpQAmPaTRdTooe65M") 
    return sh.sheet1

try:
    ws = get_worksheet()
except Exception as e:
    st.error(f"Gagal koneksi ke Google Sheets: {e}")
    st.stop()

# --- JUDUL ---
st.title("☁️ Catatan Keuangan Online")

# --- FORM INPUT ---
with st.form("form_keuangan", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        tanggal = st.date_input("Tanggal", datetime.today())
        tipe = st.selectbox("Tipe", ["Pengeluaran", "Pemasukan"])
    with col2:
        kategori = st.selectbox("Kategori", ["Makan", "Transport", "Belanja", "Tagihan", "Gaji", "Lainnya"])
        jumlah = st.number_input("Jumlah (Rp)", min_value=0, step=1000)
    
    deskripsi = st.text_input("Deskripsi")
    tombol_simpan = st.form_submit_button("Simpan Data")

# --- LOGIKA SIMPAN ---
if tombol_simpan:
    if jumlah == 0:
        st.warning("Jumlah uang belum diisi.")
    elif not deskripsi:
        st.warning("Deskripsi wajib diisi.")
    else:
        # Ubah tanggal jadi string text biasa saat simpan
        tgl_str = tanggal.strftime("%Y-%m-%d")
        waktu_str = datetime.now().strftime("%H:%M:%S")
        
        data_baru = [tgl_str, tipe, kategori, deskripsi, jumlah, waktu_str]
        
        try:
            ws.append_row(data_baru)
            st.success("✅ Data berhasil disimpan!")
            # Rerun agar tabel di bawah langsung update
            st.rerun()
        except Exception as e:
            st.error(f"Gagal menyimpan: {e}")

# --- TAMPILKAN RIWAYAT (BAGIAN ANTI ERROR) ---
st.divider()
st.subheader("📊 Data di Google Sheets")

try:
    # Ambil semua data
    data_semua = ws.get_all_records()
    
    if data_semua:
        df = pd.DataFrame(data_semua)

        # === SOLUSI PAMUNGKAS ===
        # Ubah SELURUH DataFrame menjadi string (teks)
        # Ini mencegah error "ArrowTypeError" / "Expected bytes"
        df = df.astype(str)
        # ========================

        st.dataframe(df.tail(5)) 
        
        # Hitung Total (Manual Loop karena data sudah jadi string)
        # Kita ambil data mentah lagi untuk perhitungan agar akurat
        total_masuk = 0
        total_keluar = 0
        
        for row in data_semua:
            try:
                # Pastikan nama kolom di Google Sheet kamu: 'Tipe' dan 'Jumlah'
                # Sesuaikan besar kecil hurufnya
                uang = float(str(row['Jumlah']).replace(',', '')) # Hapus koma jika ada
                if row['Tipe'] == 'Pemasukan':
                    total_masuk += uang
                elif row['Tipe'] == 'Pengeluaran':
                    total_keluar += uang
            except:
                continue

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Masuk", f"Rp {total_masuk:,.0f}")
        c2.metric("Total Keluar", f"Rp {total_keluar:,.0f}")
        c3.metric("Sisa Saldo", f"Rp {total_masuk - total_keluar:,.0f}")

    else:
        st.info("Data kosong.")
        
except Exception as e:
    st.warning(f"Sedang memuat data atau data belum siap... ({e})")