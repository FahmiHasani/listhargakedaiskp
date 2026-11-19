import streamlit as st
import sqlite3
import pandas as pd

# Konfigurasi halaman
st.set_page_config(page_title="Daftar Harga Toko", page_icon="🛒", layout="centered")

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
    # Isi data contoh jika tabel masih kosong
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

# Inisialisasi DB
init_db()
KATEGORI_LIST = ["Makanan", "Snack", "Minuman"]

# --- TAMPILAN WEB ---
st.title("🛒 Daftar Harga Toko")

tab1, tab2, tab3 = st.tabs(["🔍 Cek Harga", "➕ Tambah Produk", "✏️ Ubah Harga"])

# --- TAB 1: CEK HARGA & SEARCH ---
with tab1:
    df = get_data()

    col1, col2 = st.columns([2, 1])
    with col1:
        keyword = st.text_input("Cari produk...", placeholder="Ketik nama makanan/snack/minuman")
    with col2:
        filter_kat = st.selectbox("Kategori", ["Semua"] + KATEGORI_LIST)

    # Filter data berdasarkan pencarian dan kategori
    hasil = df.copy()
    if keyword:
        hasil = hasil[hasil["nama"].str.contains(keyword, case=False, na=False)]
    if filter_kat != "Semua":
        hasil = hasil[hasil["kategori"] == filter_kat]

    if hasil.empty:
        st.warning("Produk tidak ditemukan.")
    else:
        # Tampilkan dibedakan per kategori
        kategori_tampil = KATEGORI_LIST if filter_kat == "Semua" else [filter_kat]
        for kat in kategori_tampil:
            sub_df = hasil[hasil["kategori"] == kat]
            if not sub_df.empty:
                st.subheader(f"📂 {kat}")
                tampil = sub_df[["nama", "harga"]].copy()
                tampil["harga"] = tampil["harga"].apply(format_rupiah)
                tampil.columns = ["Nama Produk", "Harga"]
                st.dataframe(tampil, use_container_width=True, hide_index=True)

# --- TAB 2: TAMBAH PRODUK ---
with tab2:
    st.subheader("Tambah Produk Baru")
    with st.form("form_tambah", clear_on_submit=True):
        nama_baru = st.text_input("Nama Produk")
        kat_baru = st.selectbox("Kategori", KATEGORI_LIST)
        harga_baru = st.number_input("Harga (Rp)", min_value=0, step=500)
        simpan = st.form_submit_button("Simpan Produk")

        if simpan:
            if nama_baru.strip() == "":
                st.error("Nama produk tidak boleh kosong!")
            else:
                tambah_produk(nama_baru.strip(), kat_baru, int(harga_baru))
                st.success(f"Berhasil menambahkan '{nama_baru}' ({format_rupiah(harga_baru)})!")
                st.rerun()

# --- TAB 3: UBAH HARGA / HAPUS ---
with tab3:
    st.subheader("Ubah Harga atau Hapus Produk")
    df_edit = get_data()

    if df_edit.empty:
        st.info("Belum ada produk yang tersimpan.")
    else:
        # Buat pilihan dropdown dengan format rapi
        opsi = {
            f"{row['nama']} ({row['kategori']}) - {format_rupiah(row['harga'])}": row
            for _, row in df_edit.iterrows()
        }
        pilihan = st.selectbox("Pilih produk yang ingin diubah:", list(opsi.keys()))
        produk_terpilih = opsi[pilihan]

        with st.form("form_edit"):
            edit_nama = st.text_input("Nama Produk", value=produk_terpilih["nama"])
            edit_kat = st.selectbox(
                "Kategori",
                KATEGORI_LIST,
                index=KATEGORI_LIST.index(produk_terpilih["kategori"])
            )
            edit_harga = st.number_input(
                "Harga Baru (Rp)",
                min_value=0,
                step=500,
                value=int(produk_terpilih["harga"])
            )

            col_simpan, col_hapus = st.columns(2)
            with col_simpan:
                btn_update = st.form_submit_button("💾 Simpan Perubahan", use_container_width=True)
            with col_hapus:
                btn_hapus = st.form_submit_button("🗑️ Hapus Produk", use_container_width=True)

            if btn_update:
                update_harga(int(produk_terpilih["id"]), edit_nama.strip(), edit_kat, int(edit_harga))
                st.success("Data produk berhasil diperbarui!")
                st.rerun()

            if btn_hapus:
                hapus_produk(int(produk_terpilih["id"]))
                st.warning("Produk telah dihapus.")
                st.rerun()