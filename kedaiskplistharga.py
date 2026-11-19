import streamlit as st
import sqlite3
import pandas as pd
import html

# Konfigurasi halaman
st.set_page_config(page_title="Daftar Harga Kedai SKP", page_icon="✨", layout="centered")

# --- AMBIL PIN ADMIN ---
# Jika sudah diatur di Streamlit Secrets akan pakai itu, jika belum pakai default "1234"
try:
    ADMIN_PIN = str(st.secrets["ADMIN_PIN"])
except Exception:
    ADMIN_PIN = "1234"

# Inisialisasi status login admin
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .hero-box {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 24px 20px;
        border-radius: 16px;
        color: #FFFFFF;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
    }
    .hero-title {
        font-size: 24px;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero-sub {
        font-size: 13px;
        color: #94A3B8;
        margin-top: 6px;
        margin-bottom: 0;
    }
    .cat-header {
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #D97706;
        margin-top: 22px;
        margin-bottom: 10px;
        padding-bottom: 6px;
        border-bottom: 1px solid rgba(148, 163, 184, 0.25);
    }
    .product-card {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 18px;
        margin-bottom: 10px;
        border-radius: 12px;
        background-color: rgba(148, 163, 184, 0.08);
        border: 1px solid rgba(148, 163, 184, 0.2);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .product-card:hover {
        transform: translateY(-2px);
        border-color: #D97706;
    }
    .product-name {
        font-size: 15px;
        font-weight: 600;
    }
    .product-price {
        font-size: 15px;
        font-weight: 700;
        color: #10B981;
        white-space: nowrap;
        margin-left: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("toko.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS produk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            kategori TEXT NOT NULL,
            harga INTEGER NOT NULL
        )
    """)
    c.execute("SELECT COUNT(*) FROM produk")
    if c.fetchone()[0] == 0:
        sample_data = [
            ("Nasi Goreng Spesial", "Makanan", 15000),
            ("Mie Ayam Bakso", "Makanan", 12000),
            ("Keripik Kentang", "Snack", 8000),
            ("Kacang Atom", "Snack", 5000),
            ("Es Teh Manis", "Minuman", 4000),
            ("Kopi Susu Gula Aren", "Minuman", 15000),
        ]
        c.executemany("INSERT INTO produk (nama, kategori, harga) VALUES (?, ?, ?)", sample_data)
    conn.commit()
    conn.close()

def get_data():
    conn = sqlite3.connect("toko.db")
    df = pd.read_sql_query("SELECT * FROM produk ORDER BY kategori, nama", conn)
    conn.close()
    return df

def tambah_produk(nama, kategori, harga):
    conn = sqlite3.connect("toko.db")
    c = conn.cursor()
    c.execute("INSERT INTO produk (nama, kategori, harga) VALUES (?, ?, ?)", (nama, kategori, harga))
    conn.commit()
    conn.close()

def update_harga(id_produk, nama_baru, kategori_baru, harga_baru):
    conn = sqlite3.connect("toko.db")
    c = conn.cursor()
    c.execute(
        "UPDATE produk SET nama = ?, kategori = ?, harga = ? WHERE id = ?",
        (nama_baru, kategori_baru, harga_baru, id_produk)
    )
    conn.commit()
    conn.close()

def hapus_produk(id_produk):
    conn = sqlite3.connect("toko.db")
    c = conn.cursor()
    c.execute("DELETE FROM produk WHERE id = ?", (id_produk,))
    conn.commit()
    conn.close()

def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

def tampilkan_daftar_harga():
    df = get_data()

    keyword = st.text_input("", placeholder="🔍 Cari nama makanan, snack, atau minuman...", label_visibility="collapsed")
    filter_kat = st.radio("Kategori", ["Semua"] + KATEGORI_LIST, horizontal=True, label_visibility="collapsed")

    hasil = df.copy()
    if keyword:
        hasil = hasil[hasil["nama"].str.contains(keyword, case=False, na=False)]
    if filter_kat != "Semua":
        hasil = hasil[hasil["kategori"] == filter_kat]

    if hasil.empty:
        st.info("Produk yang dicari tidak ditemukan.")
    else:
        kategori_tampil = KATEGORI_LIST if filter_kat == "Semua" else [filter_kat]
        for kat in kategori_tampil:
            sub_df = hasil[hasil["kategori"] == kat]
            if not sub_df.empty:
                ikon = IKON_KATEGORI.get(kat, "📂")
                st.markdown(f'<div class="cat-header">{ikon} {kat}</div>', unsafe_allow_html=True)
                for _, row in sub_df.iterrows():
                    nama_aman = html.escape(str(row["nama"]))
                    harga_str = format_rupiah(row["harga"])
                    st.markdown(f"""
                    <div class="product-card">
                        <span class="product-name">{nama_aman}</span>
                        <span class="product-price">{harga_str}</span>
                    </div>
                    """, unsafe_allow_html=True)

init_db()
KATEGORI_LIST = ["Makanan", "Snack", "Minuman"]
IKON_KATEGORI = {"Makanan": "🍽️", "Snack": "🍟", "Minuman": "🥤"}

# --- HEADER ---
st.markdown("""
<div class="hero-box">
    <p class="hero-title">Daftar Harga Kedai</p>
    <p class="hero-sub">Cek harga cepat & mudah untuk seluruh menu</p>
</div>
""", unsafe_allow_html=True)

# --- TAMPILAN BERDASARKAN ROLE ---
