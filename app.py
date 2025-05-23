import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import plugins
from io import BytesIO
import json

st.set_page_config(page_title="Dynamic Map App", layout="wide")

st.title("🌍️ Dynamic Map Viewer")
st.markdown("""
Upload file Excel berisi titik lokasi dengan kolom minimal: **Latitude**, **Longitude**.  
Jika ada kolom **Warna**, maka titik akan diberi warna sesuai.  
Filter otomatis akan muncul berdasarkan kolom dalam file.  
Pilih warna kustom untuk masing-masing titik jika diperlukan.
""")

uploaded_file = st.sidebar.file_uploader("📄 Upload File Excel", type=["xlsx"])

@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()
    return df

# === Initialize Session States ===
if "kcp_custom_colors" not in st.session_state:
    st.session_state.kcp_custom_colors = {}
if "circle_radius" not in st.session_state:
    st.session_state.circle_radius = 1.0
if "show_circle" not in st.session_state:
    st.session_state.show_circle = False
if "shape_color" not in st.session_state:
    st.session_state.shape_color = "red"
if "shape_target_color" not in st.session_state:  # <-- NEW
    st.session_state.shape_target_color = "green"
if "enable_cluster" not in st.session_state:
    st.session_state.enable_cluster = False

# === Available Colors (19 Folium Colors) ===
available_folium_colors = [
    "red", "blue", "green", "purple", "orange", "darkred", "lightred",
    "beige", "darkblue", "darkgreen", "cadetblue", "darkpurple",
    "white", "pink", "lightblue", "lightgreen", "gray", "black", "lightgray"
]

# === Load from JSON ===
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔄 Lanjutkan dari JSON")
uploaded_json = st.sidebar.file_uploader("Upload file JSON", type="json")
if uploaded_json is not None:
    if st.sidebar.button("🔄 Load Pengaturan JSON"):
        progress = json.load(uploaded_json)
        df = pd.DataFrame(progress["data"])
        st.session_state.kcp_custom_colors = progress.get("kcp_custom_colors", {})
        st.session_state.circle_radius = progress.get("circle_radius", 1.0)
        st.session_state.show_circle = progress.get("show_circle", False)
        st.session_state.shape_color = progress.get("shape_color", "red")
        st.session_state.shape_target_color = progress.get("shape_target_color", "green")  # <-- NEW
        st.session_state.enable_cluster = progress.get("enable_cluster", False)
        st.session_state.saved_df = df
        st.success("Data dan pengaturan berhasil dimuat dari JSON.")

if uploaded_file is not None:
    df = load_data(uploaded_file)

    st.subheader("🧫 Pilih Kolom Latitude, Longitude, dan Nama Titik")
    col_lat = st.selectbox("Pilih Kolom Latitude", df.columns, index=None)
    col_lon = st.selectbox("Pilih Kolom Longitude", df.columns, index=None)
    name_column = st.selectbox("Pilih Kolom Nama Titik", df.columns, index=None)

    if not col_lat or not col_lon or not name_column:
        st.warning("Silakan pilih ketiga kolom terlebih dahulu.")
        st.stop()

    df = df.rename(columns={col_lat: "Latitude", col_lon: "Longitude", name_column: "NamaTitik"})
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
    df.dropna(subset=["Latitude", "Longitude"], inplace=True)

    # === Sidebar Filters ===
    st.sidebar.title("🔎 Filter Lokasi")
    filter_conditions = {}
    for col in df.columns:
        if df[col].nunique() < 100 and col not in ["Latitude", "Longitude", "NamaTitik"]:
            options = sorted(df[col].dropna().unique())
            select_all = st.sidebar.checkbox(f"Pilih Semua {col}", value=False, key=f"all_{col}")
            selected = options if select_all else st.sidebar.multiselect(f"Cari atau pilih {col.lower()}", options, key=f"filter_{col}")
            if selected:
                filter_conditions[col] = selected

    for col, selected_vals in filter_conditions.items():
        df = df[df[col].isin(selected_vals)]

    # === Sidebar Color Settings ===
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎨 Pilih Warna Untuk Titik Tertentu")

    warna_column = st.sidebar.selectbox("🖍️ Pilih Kolom Referensi Warna", df.columns, index=None)
    if warna_column:
        name_list = sorted(df[warna_column].dropna().unique())
        selected_names = st.sidebar.multiselect("Pilih Nilai dari Kolom Warna", name_list)
        color_choice = st.sidebar.selectbox("Pilih Warna", available_folium_colors)
        if selected_names:
            if st.sidebar.button("🎯 Tandai Nilai dengan Warna Ini"):
                for val in selected_names:
                    st.session_state.kcp_custom_colors[val] = color_choice

    if st.sidebar.button("🔄 Reset Semua Warna"):
        st.session_state.kcp_custom_colors = {}

    # === Sidebar Circle Settings ===
    st.sidebar.markdown("---")
    st.session_state.show_circle = st.sidebar.checkbox("🟢 Tampilkan Lingkaran Radius", value=st.session_state.show_circle)
    st.session_state.circle_radius = st.sidebar.number_input("Masukkan Radius (km) untuk Lingkaran", min_value=0.0, value=st.session_state.circle_radius, step=0.5)
    st.session_state.shape_color = st.sidebar.selectbox("Pilih Warna Lingkaran", available_folium_colors, index=available_folium_colors.index(st.session_state.shape_color))
    st.session_state.shape_target_color = st.sidebar.selectbox("Pilih Warna Titik yang Diberi Lingkaran", available_folium_colors, index=available_folium_colors.index(st.session_state.shape_target_color))

    st.sidebar.markdown("---")
    st.session_state.enable_cluster = st.sidebar.checkbox("📍 Aktifkan Cluster Marker", value=st.session_state.enable_cluster)

    # === Save Progress to JSON ===
    st.sidebar.markdown("---")
    progress = {
        "data": df.to_dict(orient="records"),
        "kcp_custom_colors": st.session_state.kcp_custom_colors,
        "circle_radius": st.session_state.circle_radius,
        "show_circle": st.session_state.show_circle,
        "shape_color": st.session_state.shape_color,
        "shape_target_color": st.session_state.shape_target_color,
        "enable_cluster": st.session_state.enable_cluster
    }
    json_bytes = json.dumps(progress).encode('utf-8')
    st.sidebar.download_button(
        label="📅 Simpan Progress (JSON)",
        data=json_bytes,
        file_name="saved_progress.json",
        mime="application/json"
    )

    # === Main Map ===
    lat_center = df["Latitude"].mean()
    lon_center = df["Longitude"].mean()

    m = folium.Map(location=[lat_center, lon_center], zoom_start=6)
    plugins.Draw(export=True).add_to(m)

    marker_group = folium.FeatureGroup(name="Markers")
    marker_cluster = plugins.MarkerCluster() if st.session_state.enable_cluster else None

    for _, row in df.iterrows():
        lat, lon = row["Latitude"], row["Longitude"]
        warna = "blue"
        ref_value = row[warna_column] if warna_column in row else None
        if ref_value in st.session_state.kcp_custom_colors:
            warna = st.session_state.kcp_custom_colors[ref_value]
        elif "Warna" in row and pd.notna(row["Warna"]):
            warna = row["Warna"]

        popup_text = row["NamaTitik"]

        marker = folium.Marker(
            location=[lat, lon],
            popup=popup_text,
            icon=folium.Icon(color=warna if warna in available_folium_colors else "blue", icon="info-sign")
        )

        if st.session_state.enable_cluster:
            marker_cluster.add_child(marker)
        else:
            marker.add_to(marker_group)

        # New: Circle if warna == selected shape_target_color
        if warna == st.session_state.shape_target_color and st.session_state.show_circle:
            folium.Circle(
                radius=st.session_state.circle_radius * 1000,
                location=[lat, lon],
                color=st.session_state.shape_color,
                fill=True,
                fill_opacity=0.2
            ).add_to(m)

    if st.session_state.enable_cluster:
        marker_cluster.add_to(m)
    else:
        marker_group.add_to(m)

    st_data = st_folium(m, use_container_width=True, height=700)

    # === Export Data with Final Color ===
    df_export = df.copy()
    def get_final_color(row):
        ref_val = row[warna_column] if warna_column in row else None
        if ref_val in st.session_state.kcp_custom_colors:
            return st.session_state.kcp_custom_colors[ref_val]
        elif "Warna" in row and pd.notna(row["Warna"]):
            return row["Warna"]
        else:
            return "blue"

    df_export["Warna_Akhir"] = df_export.apply(get_final_color, axis=1)

    buffer = BytesIO()
    df_export.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    st.download_button(
        label="⬇️ Download Seluruh Data (Excel)",
        data=buffer,
        file_name="seluruh_data_dengan_warna.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Silakan upload file Excel untuk memulai.")
    if "saved_df" in st.session_state:
        df = st.session_state.saved_df
        st.success("Menampilkan data yang dimuat dari JSON sebelumnya.")
        st.write(df.head())
