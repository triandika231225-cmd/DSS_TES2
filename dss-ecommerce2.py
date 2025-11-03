import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Konfigurasi halaman
st.set_page_config(
    page_title="DSS Rekomendasi Toko E-Commerce",
    page_icon="🛒",
    layout="wide"
)

# Data dummy toko
@st.cache_data
def load_toko_data():
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
    return pd.DataFrame(data)

# Fungsi normalisasi
def normalize_data(df, column, reverse=False):
    min_val = df[column].min()
    max_val = df[column].max()
    if max_val == min_val:
        return pd.Series([1.0] * len(df), index=df.index)
    if reverse:
        return (max_val - df[column]) / (max_val - min_val)
    else:
        return (df[column] - min_val) / (max_val - min_val)

# Fungsi untuk menghitung skor
def calculate_score(df, weights):
    df_score = df.copy()
    
    # Normalisasi kriteria (semakin tinggi semakin baik)
    df_score['norm_rating'] = normalize_data(df, 'rating')
    df_score['norm_ulasan'] = normalize_data(df, 'jumlah_ulasan')
    df_score['norm_pengiriman'] = normalize_data(df, 'waktu_pengiriman', reverse=True)
    df_score['norm_sukses'] = normalize_data(df, 'tingkat_sukses')
    df_score['norm_komplain'] = normalize_data(df, 'tingkat_komplain', reverse=True)
    df_score['norm_promo'] = normalize_data(df, 'jumlah_promo')
    df_score['norm_respon'] = normalize_data(df, 'respon_chat_menit', reverse=True)
    
    # Hitung skor total
    df_score['skor_total'] = (
        df_score['norm_rating'] * weights['rating'] +
        df_score['norm_ulasan'] * weights['ulasan'] +
        df_score['norm_pengiriman'] * weights['pengiriman'] +
        df_score['norm_sukses'] * weights['sukses'] +
        df_score['norm_komplain'] * weights['komplain'] +
        df_score['norm_promo'] * weights['promo'] +
        df_score['norm_respon'] * weights['respon']
    )
    
    # Pastikan skor_total berada di rentang [0,1]
    df_score['skor_total'] = df_score['skor_total'].clip(lower=0.0, upper=1.0)
    
    return df_score

# Fungsi untuk generate alasan rekomendasi
def generate_reason(row):
    reasons = []
    
    if row['rating'] >= 4.8:
        reasons.append(f"rating tinggi ({row['rating']}/5)")
    
    if row['waktu_pengiriman'] <= 1:
        reasons.append("pengiriman tercepat (1 hari)")
    elif row['waktu_pengiriman'] <= 2:
        reasons.append("pengiriman cepat (2 hari)")
    
    if row['tingkat_sukses'] >= 97:
        reasons.append(f"tingkat keberhasilan pesanan {row['tingkat_sukses']}%")
    
    if row['tingkat_komplain'] <= 2:
        reasons.append("jarang menerima komplain")
    
    if row['jumlah_promo'] >= 5:
        reasons.append(f"{row['jumlah_promo']} promo aktif")
    
    if row['respon_chat_menit'] <= 10:
        reasons.append("respon chat cepat")
    
    if row['jumlah_ulasan'] >= 2000:
        reasons.append("banyak dipercaya pelanggan")
    
    if len(reasons) == 0:
        return "Toko terpercaya dengan performa baik"
    
    return "Toko ini memiliki " + ", ".join(reasons) + "."

# Fungsi untuk menambahkan log
def add_log(kategori, lokasi, raw_weights, normalized_weights, top_toko):
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    
    log_entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'kategori': kategori,
        'lokasi': lokasi,
        'raw_weights': raw_weights,
        'normalized_weights': normalized_weights,
        'top_toko': top_toko
    }
    st.session_state.logs.append(log_entry)

# Header
st.title("🛒 DSS Rekomendasi Toko E-Commerce")
st.markdown("**Sistem Penunjang Keputusan untuk Memilih Toko Terbaik**")
st.markdown("---")

# Sidebar untuk input preferensi
with st.sidebar:
    st.header("⚙️ Preferensi Pengguna")
    
    # Load data
    df_toko = load_toko_data()
    
    # Input kategori
    kategori_options = ['Semua Kategori'] + sorted(df_toko['kategori'].unique().tolist())
    kategori = st.selectbox("📦 Kategori Produk", kategori_options)
    
    # Input lokasi
    lokasi_options = ['Semua Lokasi'] + sorted(df_toko['lokasi'].unique().tolist())
    lokasi = st.selectbox("📍 Lokasi Pengiriman", lokasi_options)
    
    st.markdown("---")
    st.subheader("🎯 Prioritas Kriteria")
    st.caption("Sesuaikan bobot sesuai prioritas Anda (total: 100%)")
    
    # Slider untuk bobot (nilai 0-100)
    weight_rating = st.slider("Rating Toko", 0, 100, 25, 5)
    weight_ulasan = st.slider("Jumlah Ulasan", 0, 100, 10, 5)
    weight_pengiriman = st.slider("Kecepatan Pengiriman", 0, 100, 20, 5)
    weight_sukses = st.slider("Tingkat Keberhasilan", 0, 100, 15, 5)
    weight_komplain = st.slider("Tingkat Komplain (rendah)", 0, 100, 10, 5)
    weight_promo = st.slider("Jumlah Promo", 0, 100, 10, 5)
    weight_respon = st.slider("Respon Chat", 0, 100, 10, 5)
    
    total_weight = weight_rating + weight_ulasan + weight_pengiriman + weight_sukses + weight_komplain + weight_promo + weight_respon
    
    if total_weight != 100:
        st.warning(f"⚠️ Total bobot: {total_weight}%. Sistem akan menormalisasi bobot agar jumlah = 100%.")
    else:
        st.success("✅ Total bobot: 100%")
    
    # Raw bobot (0..1) berdasarkan slider
    raw_weights = {
        'rating': weight_rating / 100,
        'ulasan': weight_ulasan / 100,
        'pengiriman': weight_pengiriman / 100,
        'sukses': weight_sukses / 100,
        'komplain': weight_komplain / 100,
        'promo': weight_promo / 100,
        'respon': weight_respon / 100
    }
    
    # Normalisasi bobot sehingga jumlah = 1 (untuk mencegah skor > 100%)
    sum_raw = sum(raw_weights.values())
    if sum_raw == 0:
        # Jika semua slider 0, beri bobot rata-rata
        normalized_weights = {k: 1.0/len(raw_weights) for k in raw_weights}
        st.info("Semua bobot 0 → digunakan bobot rata-rata otomatis.")
    else:
        normalized_weights = {k: v / sum_raw for k, v in raw_weights.items()}
    
    # Tampilkan bobot yang digunakan (dinormalisasi)
    st.caption("Bobot yang digunakan (dinormalisasi):")
    st.write({
        'Rating': f"{normalized_weights['rating']*100:.1f}%",
        'Ulasan': f"{normalized_weights['ulasan']*100:.1f}%",
        'Pengiriman': f"{normalized_weights['pengiriman']*100:.1f}%",
        'Sukses': f"{normalized_weights['sukses']*100:.1f}%",
        'Komplain': f"{normalized_weights['komplain']*100:.1f}%",
        'Promo': f"{normalized_weights['promo']*100:.1f}%",
        'Respon': f"{normalized_weights['respon']*100:.1f}%"
    })
    
    st.markdown("---")
    cari_button = st.button("🔍 Cari Rekomendasi", type="primary", use_container_width=True)

# Main content
if cari_button:
    # Filter data
    df_filtered = df_toko.copy()
    
    if kategori != 'Semua Kategori':
        df_filtered = df_filtered[df_filtered['kategori'] == kategori]
    
    if lokasi != 'Semua Lokasi':
        df_filtered = df_filtered[df_filtered['lokasi'] == lokasi]
    
    if len(df_filtered) == 0:
        st.error("❌ Tidak ada toko yang sesuai dengan filter Anda.")
    else:
        # Hitung skor (menggunakan normalized_weights)
        df_result = calculate_score(df_filtered, normalized_weights)
        df_result = df_result.sort_values('skor_total', ascending=False)
        
        # Generate alasan
        df_result['alasan'] = df_result.apply(generate_reason, axis=1)
        df_result['skor_persen'] = (df_result['skor_total'] * 100).round(1).clip(upper=100.0)
        
        # Tambah log (simpan raw dan normalized weights)
        add_log(kategori, lokasi, raw_weights, normalized_weights, df_result.iloc[0]['nama_toko'])
        
        # Tampilkan hasil
        st.header("🏆 Hasil Rekomendasi Toko")
        st.caption(f"Ditemukan {len(df_result)} toko yang sesuai dengan preferensi Anda")
        
        # Filter tambahan
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
        
        # Tampilkan top 3 dalam card
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
                    
                    st.markdown("---")
        
        # Tampilkan semua hasil dalam tabel
        st.subheader("📋 Semua Hasil Rekomendasi")
        
        df_table = df_display[['nama_toko', 'kategori', 'lokasi', 'rating', 'waktu_pengiriman', 
                                'jumlah_promo', 'tingkat_sukses', 'skor_persen']].copy()
        df_table.columns = ['Nama Toko', 'Kategori', 'Lokasi', 'Rating', 'Pengiriman (hari)', 
                            'Promo', 'Sukses (%)', 'Skor (%)']
        df_table = df_table.reset_index(drop=True)
        df_table.index = df_table.index + 1
        
        st.dataframe(df_table, use_container_width=True, height=400)
        
        # Analisis
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
    
    # Info tentang sistem
    st.subheader("ℹ️ Tentang Sistem DSS")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Fitur Utama:**
        - ✅ Filter berdasarkan kategori dan lokasi
        - ✅ Penyesuaian bobot kriteria
        - ✅ Ranking otomatis dengan weighted scoring
        - ✅ Alasan rekomendasi yang jelas
        - ✅ Filter tambahan hasil
        - ✅ Analisis perbandingan toko
        """)
    
    with col2:
        st.markdown("""
        **Kriteria Penilaian:**
        - 📊 Rating pelanggan
        - 💬 Jumlah ulasan
        - 🚀 Kecepatan pengiriman
        - ✅ Tingkat keberhasilan pesanan
        - ⚠️ Tingkat komplain
        - 🎁 Jumlah promo aktif
        - 💬 Kecepatan respon chat
        """)

# Footer dengan log
if 'logs' in st.session_state and len(st.session_state.logs) > 0:
    with st.expander("📝 Riwayat Pencarian (Logging)"):
        for i, log in enumerate(reversed(st.session_state.logs[-5:]), 1):
            st.text(f"{i}. [{log['timestamp']}] Kategori: {log['kategori']}, Lokasi: {log['lokasi']}, Top: {log['top_toko']}")

st.markdown("---")
st.caption("DSS Rekomendasi Toko E-Commerce | Kelompok 3C - Sistem Informasi PSTI-C")
