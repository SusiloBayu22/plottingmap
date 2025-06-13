import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import json
import io

st.set_page_config(layout="wide", page_title="Dynamic Map Viewer")

st.sidebar.header("📁 Upload File Excel")
uploaded_file = st.sidebar.file_uploader("Upload file Excel", type=["xlsx"])

st.sidebar.markdown("---")
st.sidebar.header("📄 Lanjutkan dari JSON")
json_file = st.sidebar.file_uploader("Upload file JSON", type=["json"])

# Inisialisasi session state
if "marker_colors" not in st.session_state:
    st.session_state.marker_colors = {}

# Fungsi caching dan pembersih koordinat
@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()
    return df

def clean_coordinate(value):
    if isinstance(value, str):
        value = value.strip().replace("\n", "").replace("\t", "")
        value = value.replace(",", ".").replace(" ", "")
        value = value.replace("−", "-")
        value = value.replace("..", ".")
        parts = value.split(".")
        if len(parts) > 2:
            value = "".join(parts[:-1]) + "." + parts[-1]
    try:
        return float(value)
    except:
        return None

# Proses file
if uploaded_file:
    df = load_data(uploaded_file)

    st.subheader("📍 Konfigurasi Kolom Lokasi")
    lat_col = st.selectbox("Pilih Kolom Latitude", df.columns, index=list(df.columns).index("Latitude") if "Latitude" in df.columns else 0)
    lon_col = st.selectbox("Pilih Kolom Longitude", df.columns, index=list(df.columns).index("Longitude") if "Longitude" in df.columns else 0)
    name_col = st.selectbox("Pilih Kolom Nama Titik", df.columns, index=list(df.columns).index("Lokasi") if "Lokasi" in df.columns else 0)

    # Bersihkan koordinat dan simpan ke kolom baru
    df["Latitude_clean"] = df[lat_col].apply(clean_coordinate)
    df["Longitude_clean"] = df[lon_col].apply(clean_coordinate)
    df = df.dropna(subset=["Latitude_clean", "Longitude_clean"])

    # Filter berjenjang dengan tombol "Pilih Semua"
    st.sidebar.header("🔍 Filter Lokasi")
    filter_cols = [col for col in df.columns if df[col].nunique() < 100 and df[col].dtype == "object"]
    selected_filters = {}
    for col in filter_cols:
        with st.sidebar.expander(f"Filter: {col}", expanded=False):
            unique_vals = sorted(df[col].dropna().unique())
            all_key = f"select_all_{col}"
            st.session_state.setdefault(all_key, True)
            select_all = st.checkbox("Pilih Semua", key=all_key)
            if select_all:
                selected = st.multiselect(f"Pilih {col}", unique_vals, default=unique_vals, key=f"multi_{col}")
            else:
                selected = st.multiselect(f"Pilih {col}", unique_vals, key=f"multi_{col}")
            selected_filters[col] = selected
            df = df[df[col].isin(selected)]

    # Load warna marker dari JSON
    if json_file:
        try:
            colors = json.load(json_file)
            st.session_state.marker_colors = colors
        except Exception as e:
            st.error(f"Gagal membaca file JSON: {e}")

    # ✅ Opsi clustering
    st.sidebar.markdown("---")
    use_cluster = st.sidebar.checkbox("Aktifkan Clustering", value=True)

    # Peta
    st.subheader("🗺️ Peta Lokasi")
    map_center = [df["Latitude_clean"].mean(), df["Longitude_clean"].mean()]
    folium_map = folium.Map(location=map_center, zoom_start=6)

    if use_cluster:
        marker_layer = MarkerCluster().add_to(folium_map)
    else:
        marker_layer = folium.FeatureGroup(name="Markers").add_to(folium_map)

    for _, row in df.iterrows():
        name = str(row[name_col])
        lat = row["Latitude_clean"]
        lon = row["Longitude_clean"]
        color = st.session_state.marker_colors.get(name, "blue")

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(name, max_width=300),
            tooltip=name,
            icon=folium.Icon(color=color)
        ).add_to(marker_layer)

        if color == "green":
            for radius, opacity in zip([25000, 50000, 75000, 100000], [0.25, 0.5, 0.75, 1]):
                folium.Circle(
                    location=[lat, lon],
                    radius=radius,
                    color="green",
                    fill=True,
                    fill_opacity=opacity,
                ).add_to(folium_map)

    st_data = st_folium(folium_map, width=1000, height=600)

    # Simpan warna ke JSON
    st.sidebar.markdown("---")
    if st.sidebar.button("💾 Simpan Warna Marker ke JSON"):
        json_bytes = io.BytesIO()
        json_bytes.write(json.dumps(st.session_state.marker_colors, indent=2).encode("utf-8"))
        json_bytes.seek(0)
        st.sidebar.download_button("Download JSON", json_bytes, file_name="marker_colors.json")

    # Ekspor ke Excel
    st.sidebar.markdown("---")
    if st.sidebar.button("⬇️ Export Filtered Excel"):
        export_df = df.copy()
        export_df["Warna"] = export_df[name_col].map(lambda x: st.session_state.marker_colors.get(str(x), "blue"))
        towrite = io.BytesIO()
        with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
            export_df.to_excel(writer, index=False)
        towrite.seek(0)
        st.sidebar.download_button("Download Excel", towrite, file_name="filtered_data.xlsx")
