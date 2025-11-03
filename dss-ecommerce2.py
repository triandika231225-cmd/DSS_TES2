import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Konfigurasi halaman
st.set_page_config(
    page_title="DSS Rekomendasi Toko E-Commerce (Diperbarui)",
    page_icon="🛒",
    layout="wide"
)

# Data dummy toko dengan kolom tambahan: promo_terakhir, pelanggan_tetap
@st.cache_data
def load_toko_data():
    np.random.seed(42)
    data = {
        'id': range(1, 21),
        'nama_toko': [
            'TechMart Store', 'Fashion Paradise', 'Beauty Corner', 'Gadget Zone',
            'Style House', 'Kosmetik Cantik', 'Electronics Hub', 'Trendy Fashion',
            'Skin Care Pro', 'Digital World', 'Fashion Elite', 'Beauty Glow',
            'Mega Electronics', 'Boutique Chic', 'Glowing Skin', 'Smart Tech',
            'Urban Fashion', 'Natural Beauty', 'Tech Innovation', 'Premium Style'
        ],
        'kategori': [
            'Elektronik', 'Pakaian', 'Kecantikan', 'Elektronik',
            'Pakaian', 'Kecantikan', 'Elektronik', 'Pakaian',
            'Kecantikan', 'Elektronik', 'Pakaian', 'Kecantikan',
            'Elektronik', 'Pakaian', 'Kecantikan', 'Elektronik',
            'Pakaian', 'Kecantikan', 'Elektronik', 'Pakaian'
        ],
        'lokasi': [
            'Jakarta', 'Bandung', 'Surabaya', 'Jakarta',
            'Jakarta', 'Yogyakarta', 'Surabaya', 'Bandung',
            'Jakarta', 'Semarang', 'Jakarta', 'Surabaya',
            'Jakarta', 'Bandung', 'Yogyakarta', 'Jakarta',
            'Surabaya', 'Bandung', 'Jakarta', 'Semarang'
        ],
        'rating': [4.9, 4.7, 4.8, 4.6, 4.8, 4.5, 4.9, 4.7, 4.6, 4.8, 4.7, 4.9, 4.5, 4.8, 4.7, 4.9, 4.6, 4.8, 4.9, 4.7],
        'jumlah_ulasan': [2500, 1800, 2200, 1500, 1900, 1200, 2800, 1600, 1400, 2100, 1700, 2400, 1300, 2000, 1500, 2600, 1400, 1800, 2900, 1600],
        'waktu_pengiriman': [1, 2, 2, 3, 1, 3, 1, 2, 2, 2, 1, 1, 3, 2, 3, 1, 2, 2, 1, 3],
        'tingkat_sukses': [98, 95, 96, 93, 97, 92, 99, 96, 94, 97, 95, 98, 91, 96, 93, 99, 94, 97, 99, 92],
        'tingkat_komplain': [1, 3, 2, 5, 2, 6, 1, 3, 4, 2, 3, 1, 7, 2, 5, 1, 4, 2, 1, 6],
        'jumlah_promo': [5, 3, 4, 2, 4, 2, 6, 3, 3, 5, 4, 5, 2, 4, 2, 6, 3, 4, 7, 3],
        'total_produk': [1500, 800, 1200, 600, 900, 500, 1800, 850, 700, 1100, 950, 1400, 550, 1000, 650, 1700, 750, 950, 2000, 800],
        'respon_chat_menit': [5, 15, 10, 20, 8, 25, 4, 12, 18, 9, 14, 6, 22, 11, 19, 5, 16, 10, 4, 21]
    }
    df = pd.DataFrame(data)

    # Tambahkan pelanggan_tetap (perkiraan dari ulasan) dan promo_terakhir (random dalam 0-72 jam)
    df['pelanggan_tetap'] = (df['jumlah_ulasan'] * 0.20).round().astype(int)  # asumsi: 20% ulasan adalah pelanggan tetap
    now = datetime.now()
    hours_ago = np.random.randint(0, 72, size=len(df))  # promo dalam 0..71 jam yang lalu
    df['promo_terakhir'] = [now - timedelta(hours=int(h)) for h in hours_ago]

    return df

# Fungsi normalisasi (skala 0..1)
def normalize_data(df, column, reverse=False):
    min_val = df[column].min()
    max_val = df[column].max()
    if max_val == min_val:
        return pd.Series([1.0] * len(df))
    if reverse:
        return (max_val - df[column]) / (max_val - min_val)
    else:
        return (df[column] - min_val) / (max_val - min_val)

# Fungsi perhitungan skor (ditambah parameter lokasi pengguna & aktivitas preferensi)
def calculate_score(df, weights, user_location=None, aktivitas_pref=None):
    df_score = df.copy()

    # Normalisasi kriteria lama
    df_score['norm_rating'] = normalize_data(df_score, 'rating')
    df_score['norm_ulasan'] = normalize_data(df_score, 'jumlah_ulasan')
    df_score['norm_pengiriman'] = normalize_data(df_score, 'waktu_pengiriman', reverse=True)
    df_score['norm_sukses'] = normalize_data(df_score, 'tingkat_sukses')
    df_score['norm_komplain'] = normalize_data(df_score, 'tingkat_komplain', reverse=True)
    df_score['norm_promo_count'] = normalize_data(df_score, 'jumlah_promo')
    df_score['norm_respon'] = normalize_data(df_score, 'respon_chat_menit', reverse=True)
    df_score['norm_langganan'] = normalize_data(df_score, 'pelanggan_tetap')

    # Kriteria baru (binary / boolean)
    # 1) Proximity / Toko terdekat (sederhana: cocok kota)
    if user_location:
        df_score['proximity'] = (df_score['lokasi'].str.lower() == user_location.lower()).astype(int)
    else:
        df_score['proximity'] = 0

    # 2) Rekomendasi berdasarkan aktivitas pengguna (jika aktivitas_pref diberikan sebagai list)
    if aktivitas_pref:
        # jika aktivitas_pref adalah list, beri 1 jika toko kategori ada di daftar
        if isinstance(aktivitas_pref, (list, tuple, set)):
            df_score['aktivitas_match'] = df_score['kategori'].apply(lambda k: 1 if k in aktivitas_pref else 0)
        else:
            df_score['aktivitas_match'] = (df_score['kategori'] == aktivitas_pref).astype(int)
    else:
        df_score['aktivitas_match'] = 0

    # 3) Respon cepat: <= 10 menit
    df_score['fast_respon'] = (df_score['respon_chat_menit'] <= 10).astype(int)

    # 4) Promo terbaru dalam 24 jam
    now = datetime.now()
    df_score['promo_recent'] = ((now - pd.to_datetime(df_score['promo_terakhir'])) <= timedelta(hours=24)).astype(int)

    # Hitung skor total: gabungkan semua norma sesuai bobot
    df_score['skor_total'] = (
        df_score['norm_rating'] * weights['rating'] +
        df_score['norm_ulasan'] * weights['ulasan'] +
        df_score['norm_pengiriman'] * weights['pengiriman'] +
        df_score['norm_sukses'] * weights['sukses'] +
        df_score['norm_komplain'] * weights['komplain'] +
        df_score['norm_promo_count'] * weights['promo'] +
        df_score['norm_respon'] * weights['respon'] +
        df_score['proximity'] * weights['proximity'] +
        df_score['aktivitas_match'] * weights['aktivitas'] +
        df_score['fast_respon'] * weights['fast_respon'] +
        df_score['promo_recent'] * weights['promo_recent'] +
        df_score['norm_langganan'] * weights['langganan']
    )

    return df_score

# Fungsi untuk generate alasan rekomendasi (diperluas)
def generate_reason(row):
    reasons = []

    if row['rating'] >= 4.8:
        reasons.append(f"rating tinggi ({row['rating']}/5)")

    if row['waktu_pengiriman'] <= 1:
        reasons.append("pengiriman tercepat (1 hari)")
    elif row['waktu_pengiriman'] <= 2:
        reasons.append("pengiriman cepat (≤2 hari)")

    if row['tingkat_sukses'] >= 97:
        reasons.append(f"tingkat keberhasilan pesanan {row['tingkat_sukses']}%")

    if row['tingkat_komplain'] <= 2:
        reasons.append("jarang menerima komplain")

    if row['jumlah_promo'] >= 5:
        reasons.append(f"{row['jumlah_promo']} promo aktif")

    if row['respon_chat_menit'] <= 10:
        reasons.append("respon chat cepat (≤10 mnt)")

    if row['jumlah_ulasan'] >= 2000:
        reasons.append("banyak dipercaya pelanggan")

    # Indikator baru
    if 'proximity' in row and row['proximity'] == 1:
        reasons.append("gudang/toko terdekat dengan lokasi Anda")

    if 'aktivitas_match' in row and row['aktivitas_match'] == 1:
        reasons.append("cocok dengan kategori pembelian Anda")

    if 'promo_recent' in row and row['promo_recent'] == 1:
        reasons.append("meluncurkan promo dalam 24 jam terakhir")

    if 'pelanggan_tetap' in row and row['pelanggan_tetap'] >= 500:
        reasons.append("memiliki banyak pelanggan tetap (badge Langganan Banyak Pelanggan)")

    if len(reasons) == 0:
        return "Toko terpercaya dengan performa baik"

    return "Toko ini memiliki " + ", ".join(reasons) + "."

# Fungsi untuk menambahkan log
def add_log(kategori, lokasi, lokasi_pengguna, aktivitas_pref, weights, top_toko):
    if 'logs' not in st.session_state:
        st.session_state.logs = []

    log_entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'kategori_filter': kategori,
        'lokasi_filter': lokasi,
        'lokasi_pengguna': lokasi_pengguna,
        'aktivitas_pref': aktivitas_pref,
        'weights': weights,
        'top_toko': top_toko
    }
    st.session_state.logs.append(log_entry)

# Header
st.title("🛒 DSS Rekomendasi Toko E-Commerce (Diperbarui)")
st.markdown("**Sistem Penunjang Keputusan — indikator diperbarui: proximity, aktivitas, respon cepat, promo terbaru, langganan**")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Preferensi Pengguna")

    # Load data
    df_toko = load_toko_data()

    # Input kategori filter (seperti sebelumnya)
    kategori_options = ['Semua Kategori'] + sorted(df_toko['kategori'].unique().tolist())
    kategori = st.selectbox("📦 Kategori Produk (filter)", kategori_options)

    # Input lokasi filter
    lokasi_options = ['Semua Lokasi'] + sorted(df_toko['lokasi'].unique().tolist())
    lokasi = st.selectbox("📍 Lokasi Pengiriman (filter)", lokasi_options)

    st.markdown("---")
    st.subheader("📍 Informasi Lokasi & Aktivitas")
    lokasi_pengguna = st.selectbox("Lokasi Anda (untuk proximity/gudang terdekat)", sorted(df_toko['lokasi'].unique().tolist()))
    aktivitas_pref = st.multiselect("Kategori aktivitas pembelian (jika ada)", sorted(df_toko['kategori'].unique().tolist()))

    st.markdown("---")
    st.subheader("🎯 Prioritas Kriteria (total: 100%)")
    st.caption("Sesuaikan bobot; usahakan jumlah = 100%")

    # Slider untuk bobot lama
    weight_rating = st.slider("Rating Toko", 0, 100, 18, 1)
    weight_ulasan = st.slider("Jumlah Ulasan", 0, 100, 10, 1)
    weight_pengiriman = st.slider("Kecepatan Pengiriman", 0, 100, 15, 1)
    weight_sukses = st.slider("Tingkat Keberhasilan", 0, 100, 10, 1)
    weight_komplain = st.slider("Tingkat Komplain (rendah)", 0, 100, 8, 1)
    weight_promo = st.slider("Jumlah Promo (count)", 0, 100, 8, 1)
    weight_respon = st.slider("Respon Chat (rata-rata)", 0, 100, 6, 1)

    # Slider untuk kriteria baru
    weight_proximity = st.slider("Proximity (gudang terdekat)", 0, 100, 8, 1)
    weight_aktivitas = st.slider("Prioritaskan Kategori Aktivitas Anda", 0, 100, 7, 1)
    weight_fast_respon = st.slider("Respon Cepat (≤10 mnt) Bonus", 0, 100, 5, 1)
    weight_promo_recent = st.slider("Promo Terbaru (24 jam)", 0, 100, 3, 1)
    weight_langganan = st.slider("Langganan Banyak Pelanggan (badge)", 0, 100, 7, 1)

    total_weight = (weight_rating + weight_ulasan + weight_pengiriman + weight_sukses +
                    weight_komplain + weight_promo + weight_respon + weight_proximity +
                    weight_aktivitas + weight_fast_respon + weight_promo_recent + weight_langganan)

    if total_weight != 100:
        st.warning(f"⚠️ Total bobot: {total_weight}%. Sebaiknya 100% untuk interpretasi yang lebih mudah.")
    else:
        st.success("✅ Total bobot: 100%")

    # Normalisasi bobot ke 0..1 (agar fungsi memakai bobot yang diberikan)
    # Jika total_weight==0 (edge case), bagi sama rata
    if total_weight == 0:
        # fallback: bobot rata
        n = 12
        weights = dict.fromkeys(['rating','ulasan','pengiriman','sukses','komplain','promo','respon',
                                 'proximity','aktivitas','fast_respon','promo_recent','langganan'], 1/n)
    else:
        weights = {
            'rating': weight_rating / total_weight,
            'ulasan': weight_ulasan / total_weight,
            'pengiriman': weight_pengiriman / total_weight,
            'sukses': weight_sukses / total_weight,
            'komplain': weight_komplain / total_weight,
            'promo': weight_promo / total_weight,
            'respon': weight_respon / total_weight,
            'proximity': weight_proximity / total_weight,
            'aktivitas': weight_aktivitas / total_weight,
            'fast_respon': weight_fast_respon / total_weight,
            'promo_recent': weight_promo_recent / total_weight,
            'langganan': weight_langganan / total_weight
        }

    st.markdown("---")
    cari_button = st.button("🔍 Cari Rekomendasi", type="primary", use_container_width=True)

# Main content
if cari_button:
    # Filter data sesuai pilihan filter
    df_filtered = df_toko.copy()
    if kategori != 'Semua Kategori':
        df_filtered = df_filtered[df_filtered['kategori'] == kategori]
    if lokasi != 'Semua Lokasi':
        df_filtered = df_filtered[df_filtered['lokasi'] == lokasi]

    if len(df_filtered) == 0:
        st.error("❌ Tidak ada toko yang sesuai dengan filter Anda.")
    else:
        # Hitung skor baru (mengirim lokasi pengguna & aktivitas preferensi)
        df_result = calculate_score(df_filtered, weights, user_location=lokasi_pengguna, aktivitas_pref=aktivitas_pref)
        df_result = df_result.sort_values('skor_total', ascending=False)

        # Generate alasan dan tambahan kolom
        df_result['alasan'] = df_result.apply(generate_reason, axis=1)
        df_result['skor_persen'] = (df_result['skor_total'] * 100).round(1)

        # Tambah log
        add_log(kategori, lokasi, lokasi_pengguna, aktivitas_pref, weights, df_result.iloc[0]['nama_toko'])

        # Tampilkan hasil
        st.header("🏆 Hasil Rekomendasi Toko (Versi Indikator Baru)")
        st.caption(f"Ditemukan {len(df_result)} toko yang sesuai dengan preferensi Anda")

        # Filter tambahan seperti sebelumnya
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_pengiriman = st.checkbox("🚀 Hanya Pengiriman Cepat (≤2 hari)")
        with col2:
            filter_promo = st.checkbox("🎁 Hanya dengan Promo (≥3)")
        with col3:
            filter_rating = st.checkbox("⭐ Hanya Rating Tinggi (≥4.7)")

        # Apply filters
        df_display = df_result.copy()
        if filter_pengiriman:
            df_display = df_display[df_display['waktu_pengiriman'] <= 2]
        if filter_promo:
            df_display = df_display[df_display['jumlah_promo'] >= 3]
        if filter_rating:
            df_display = df_display[df_display['rating'] >= 4.7]

        st.markdown("---")

        # Tampilkan top 3 dengan badge dan info promo_terakhir, pelanggan_tetap
        top_3 = df_display.head(3)

        if len(top_3) > 0:
            st.subheader("🥇 Top 3 Rekomendasi")
            for idx, (_, row) in enumerate(top_3.iterrows(), 1):
                with st.container():
                    col1, col2, col3 = st.columns([1, 3, 1])

                    with col1:
                        medal = ["🥇", "🥈", "🥉"][idx-1]
                        st.markdown(f"## {medal}")
                        st.metric("Skor", f"{row['skor_persen']}%")

                    with col2:
                        st.markdown(f"### {row['nama_toko']}")
                        st.markdown(f"**Kategori:** {row['kategori']} | **Lokasi:** {row['lokasi']}")
                        # badges
                        badges = []
                        if row.get('proximity', 0) == 1:
                            badges.append("📍 Terdekat")
                        if row.get('promo_recent', 0) == 1:
                            badges.append("🔥 Promo 24j")
                        if row.get('pelanggan_tetap', 0) >= 500:
                            badges.append("🏅 Langganan Banyak Pelanggan")
                        if badges:
                            st.markdown(" ".join(badges))

                        col_a, col_b, col_c, col_d = st.columns(4)
                        col_a.metric("⭐ Rating", f"{row['rating']}/5")
                        col_b.metric("📦 Pengiriman", f"{row['waktu_pengiriman']} hari")
                        col_c.metric("🎁 Promo", row['jumlah_promo'])
                        col_d.metric("💬 Respon", f"{row['respon_chat_menit']} mnt")

                        st.info(f"💡 **Alasan:** {row['alasan']}")

                    with col3:
                        st.markdown("###")
                        if st.button("🛒 Kunjungi Toko", key=f"visit_{row['id']}", use_container_width=True):
                            st.success(f"Membuka {row['nama_toko']}...")
                        if st.button("📊 Detail", key=f"detail_{row['id']}", use_container_width=True):
                            with st.expander("Detail Lengkap", expanded=True):
                                st.write(f"**Jumlah Ulasan:** {row['jumlah_ulasan']:,}")
                                st.write(f"**Total Produk:** {row['total_produk']:,}")
                                st.write(f"**Tingkat Sukses:** {row['tingkat_sukses']}%")
                                st.write(f"**Tingkat Komplain:** {row['tingkat_komplain']}%")
                                st.write(f"**Pelanggan Tetap (perkiraan):** {row['pelanggan_tetap']:,}")
                                st.write(f"**Promo Terakhir:** {pd.to_datetime(row['promo_terakhir']).strftime('%Y-%m-%d %H:%M:%S')}")

                    st.markdown("---")

        # Tampilkan semua hasil dalam tabel (tambahkan kolom promo_terakhir & pelanggan_tetap)
        st.subheader("📋 Semua Hasil Rekomendasi")
        df_table = df_display[['nama_toko', 'kategori', 'lokasi', 'rating', 'waktu_pengiriman',
                                'jumlah_promo', 'tingkat_sukses', 'pelanggan_tetap', 'promo_terakhir', 'skor_persen']].copy()
        df_table.columns = ['Nama Toko', 'Kategori', 'Lokasi', 'Rating', 'Pengiriman (hari)',
                            'Promo', 'Sukses (%)', 'Pelanggan Tetap (perk.)', 'Promo Terakhir', 'Skor (%)']
        df_table = df_table.reset_index(drop=True)
        df_table.index = df_table.index + 1

        # format promo_terakhir
        df_table['Promo Terakhir'] = pd.to_datetime(df_table['Promo Terakhir']).dt.strftime('%Y-%m-%d %H:%M')

        st.dataframe(df_table, use_container_width=True, height=400)

        # Analisis ringkas
        st.subheader("📊 Analisis Hasil")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Rata-rata Rating", f"{df_display['rating'].mean():.2f}/5")
        with col2:
            st.metric("Rata-rata Pengiriman", f"{df_display['waktu_pengiriman'].mean():.1f} hari")
        with col3:
            st.metric("Rata-rata Promo", f"{df_display['jumlah_promo'].mean():.1f}")
        with col4:
            st.metric("Rata-rata Sukses", f"{df_display['tingkat_sukses'].mean():.1f}%")

else:
    # Tampilan awal
    st.info("👈 Silakan atur preferensi Anda di sidebar, lalu klik **Cari Rekomendasi**")

    # Statistik umum
    df_toko = load_toko_data()
    st.subheader("📊 Statistik Platform")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Toko", len(df_toko))
    with col2:
        st.metric("Kategori", df_toko['kategori'].nunique())
    with col3:
        st.metric("Lokasi", df_toko['lokasi'].nunique())
    with col4:
        st.metric("Rating Rata-rata", f"{df_toko['rating'].mean():.2f}/5")

    st.markdown("---")
    st.subheader("ℹ️ Tentang Sistem DSS (indikator baru)")
    st.markdown("""
        Sistem kini menambahkan indikator:
        - 📍 Proximity (gudang/toko terdekat) berdasarkan lokasi pengguna
        - 🛒 Prioritaskan kategori berdasarkan aktivitas pembelian pengguna
        - 💬 Respon cepat (bonus jika <=10 menit)
        - 🔥 Promo terbaru (dalam 24 jam terakhir)
        - 🏅 Badge "Langganan Banyak Pelanggan" jika pelanggan_tetap >= 500
    """)

# Footer dengan log
if 'logs' in st.session_state and len(st.session_state.logs) > 0:
    with st.expander("📝 Riwayat Pencarian (Logging)"):
        for i, log in enumerate(reversed(st.session_state.logs[-5:]), 1):
            st.text(f"{i}. [{log['timestamp']}] Filter: {log['kategori_filter']}, LokasiFilter: {log['lokasi_filter']}, LokasiUser: {log['lokasi_pengguna']}, Aktivitas: {log['aktivitas_pref']}, Top: {log['top_toko']}")

st.markdown("---")
st.caption("DSS Rekomendasi Toko E-Commerce | Kelompok 3C - Sistem Informasi PSTI-C (indikator diperbarui)")
