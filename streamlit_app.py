import streamlit as st
import pandas as pd
import pickle
import altair as alt
import pydeck as pdk

st.title("Dashboard Analitik DJPb")

# Sidebar Filter
st.sidebar.header("Menu Filter")
opsi = st.sidebar.selectbox("Pilih Model:", ["Klasifikasi", "Regresi"])

data = pd.read_csv("data/02_realisasi_anggaran_klasifikasi.csv")

PROVINCE_COORDINATES = {
    "Aceh": (4.6951, 96.7494),
    "Bali": (-8.4095, 115.1889),
    "DKI Jakarta": (-6.2088, 106.8456),
    "Jawa Barat": (-6.9175, 107.6191),
    "Jawa Tengah": (-7.150975, 110.140259),
    "Jawa Timur": (-7.536064, 112.238402),
    "Kalimantan Timur": (0.5387, 116.4194),
    "Lampung": (-4.5586, 105.4068),
    "NTB": (-8.6529, 117.3616),
    "NTT": (-8.6574, 121.0794),
    "Papua": (-4.2699, 138.0804),
    "Riau": (0.2933, 101.7068),
    "Sulawesi Selatan": (-3.6688, 119.9741),
    "Sumatera Barat": (-0.7399, 100.8000),
    "Sumatera Utara": (2.1154, 99.5451),
}

tab_prediksi, tab_visualisasi = st.tabs(["Menu Prediksi", "Visualisasi"])

with tab_prediksi:
    st.header("Prediksi Realisasi 95%")
    st.markdown("Masukkan data input berikut dan klik tombol untuk melihat hasil prediksi.")

    col1, col2 = st.columns(2)
    with col1:
        jumlah_spm = st.number_input(
            "Jumlah SPM",
            min_value=1,
            max_value=200,
            value=10,
            step=1,
            format="%d",
        )
        revisi_dipa = st.number_input(
            "Revisi DIPA",
            min_value=0,
            max_value=5,
            value=1,
            step=1,
            format="%d",
        )
        deviasi_rpd_persen = st.number_input(
            "Deviasi RPD (%)",
            min_value=0.00,
            max_value=30.00,
            value=5.50,
            format="%.2f",
        )
    with col2:
        skor_ikpa = st.number_input(
            "Skor IKPA",
            min_value=70.00,
            max_value=100.00,
            value=85.00,
            format="%.2f",
        )
        tipe_satker = st.selectbox(
            "Tipe Satker",
            ["Dekonsentrasi", "Kantor Daerah", "Kantor Pusat", "Tugas Pembantuan"],
        )

    if st.button("Prediksi", type="primary"):
        if model is None:
            st.error("Model belum tersedia.")
        else:
            tipe_values = [
                "Dekonsentrasi",
                "Kantor Daerah",
                "Kantor Pusat",
                "Tugas Pembantuan",
            ]
            tipe_indicators = [
                1.0 if tipe_satker == tipe_value else 0.0
                for tipe_value in tipe_values
            ]
            input_row = [
                float(jumlah_spm),
                float(revisi_dipa),
                float(deviasi_rpd_persen),
                float(skor_ikpa),
                *tipe_indicators,
            ]

            try:
                table = Orange.data.Table.from_list(model.domain, [input_row])
                prediction_index = int(model(table)[0])
                probabilities = model(table, model.Probs)[0]
                class_name = model.domain.class_var.values[prediction_index]
                confidence = float(probabilities[prediction_index])

                if class_name == "Ya":
                    st.success(f"Prediksi: {class_name} (keyakinan {confidence:.1%})")
                else:
                    st.warning(f"Prediksi: {class_name} (keyakinan {confidence:.1%})")
            except Exception as exc:
                st.error(f"Prediksi gagal dijalankan: {exc}")

with tab_visualisasi:
    st.header("Visualisasi Interaktif")
    st.markdown(
        "Gunakan filter untuk membandingkan satker pada grafik batang, pie, "
        "peta, dan bubble plot."
    )

    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        selected_province = st.selectbox(
            "Provinsi",
            ["Semua Provinsi", *sorted(data["provinsi"].dropna().unique())],
        )
    with filter_col2:
        selected_satker_type = st.selectbox(
            "Tipe Satker",
            ["Semua Tipe", *sorted(data["tipe_satker"].dropna().unique())],
        )

    filtered_data = data
    if selected_province != "Semua Provinsi":
        filtered_data = filtered_data[
            filtered_data["provinsi"] == selected_province
        ]
    if selected_satker_type != "Semua Tipe":
        filtered_data = filtered_data[
            filtered_data["tipe_satker"] == selected_satker_type
        ]

    if filtered_data.empty:
        st.info("Tidak ada data untuk filter yang dipilih.")
    else:
        bar_col, pie_col = st.columns(2)
        province_summary = filtered_data.groupby(
            "provinsi", as_index=False
        ).agg(
            jumlah_satker=("kode_satker", "nunique"),
            rata_rata_ikpa=("skor_ikpa", "mean"),
        )

        with bar_col:
            st.subheader("Realisasi per Provinsi")
            bar_metric = st.selectbox(
                "Metrik grafik batang",
                ["Jumlah Satker", "Rata-rata Skor IKPA"],
            )
            metric_column = (
                "jumlah_satker"
                if bar_metric == "Jumlah Satker"
                else "rata_rata_ikpa"
            )
            bar_chart = (
                alt.Chart(province_summary)
                .mark_bar(cornerRadiusEnd=4)
                .encode(
                    x=alt.X(f"{metric_column}:Q", title=bar_metric),
                    y=alt.Y("provinsi:N", title="Provinsi", sort="-x"),
                    color=alt.Color(
                        f"{metric_column}:Q",
                        title=bar_metric,
                        scale=alt.Scale(scheme="tealblues"),
                    ),
                    tooltip=[
                        alt.Tooltip("provinsi:N", title="Provinsi"),
                        alt.Tooltip(
                            "jumlah_satker:Q", title="Jumlah Satker"
                        ),
                        alt.Tooltip(
                            "rata_rata_ikpa:Q",
                            title="Rata-rata IKPA",
                            format=".2f",
                        ),
                    ],
                )
                .properties(height=max(300, len(province_summary) * 24))
                .interactive()
            )
            st.altair_chart(bar_chart, width="stretch")

        with pie_col:
            st.subheader("Pencapaian Realisasi 95%")
            pie_data = (
                filtered_data["realisasi_tercapai_95persen"]
                .value_counts()
                .rename_axis("status")
                .reset_index(name="jumlah_satker")
            )
            pie_data["persentase"] = (
                pie_data["jumlah_satker"] / pie_data["jumlah_satker"].sum()
            )
            pie_chart = (
                alt.Chart(pie_data)
                .mark_arc(outerRadius=120)
                .encode(
                    theta=alt.Theta("jumlah_satker:Q"),
                    color=alt.Color(
                        "status:N",
                        title="Tercapai 95%",
                        scale=alt.Scale(
                            domain=["Ya", "Tidak"],
                            range=["#2a9d8f", "#e76f51"],
                        ),
                    ),
                    tooltip=[
                        alt.Tooltip("status:N", title="Status"),
                        alt.Tooltip(
                            "jumlah_satker:Q", title="Jumlah Satker"
                        ),
                        alt.Tooltip(
                            "persentase:Q",
                            title="Persentase",
                            format=".1%",
                        ),
                    ],
                )
                .properties(height=320)
                .interactive()
            )
            st.altair_chart(pie_chart, width="stretch")

        st.subheader("Sebaran Satker per Provinsi")
        map_data = province_summary.copy()
        map_data["latitude"] = map_data["provinsi"].map(
            lambda province: PROVINCE_COORDINATES.get(
                province, (None, None)
            )[0]
        )
        map_data["longitude"] = map_data["provinsi"].map(
            lambda province: PROVINCE_COORDINATES.get(
                province, (None, None)
            )[1]
        )
        provinces_without_coordinates = map_data.loc[
            map_data["latitude"].isna(), "provinsi"
        ].tolist()
        if provinces_without_coordinates:
            st.warning(
                "Koordinat belum tersedia untuk: "
                + ", ".join(provinces_without_coordinates)
            )

        map_data = map_data.dropna(subset=["latitude", "longitude"])
        if not map_data.empty:
            map_data["radius"] = map_data["jumlah_satker"] * 500
            deck = pdk.Deck(
                layers=[
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=map_data,
                        get_position="[longitude, latitude]",
                        get_radius="radius",
                        radius_min_pixels=7,
                        radius_max_pixels=26,
                        get_fill_color=[42, 157, 143, 190],
                        pickable=True,
                        auto_highlight=True,
                    )
                ],
                initial_view_state=pdk.ViewState(
                    latitude=-2, longitude=118, zoom=3, pitch=0
                ),
                map_style=(
                    "https://basemaps.cartocdn.com/gl/positron-gl-style/"
                    "style.json"
                ),
                tooltip={
                    "html": (
                        "<b>{provinsi}</b><br/>"
                        "Jumlah satker: {jumlah_satker}<br/>"
                        "Rata-rata IKPA: {rata_rata_ikpa}"
                    ),
                    "style": {
                        "backgroundColor": "#1f2937",
                        "color": "white",
                    },
                },
            )
            st.pydeck_chart(deck, width="stretch")
            st.caption(
                "Titik menunjukkan perkiraan pusat provinsi, bukan lokasi "
                "tepat satker. Arahkan kursor untuk melihat ringkasan; "
                "peta dapat digeser dan diperbesar."
            )

        st.subheader("Bubble Plot IKPA dan Deviasi RPD")
        bubble_chart = (
            alt.Chart(filtered_data)
            .mark_circle(opacity=0.7, size=100)
            .encode(
                x=alt.X(
                    "skor_ikpa",
                    title="Skor IKPA",
                    scale=alt.Scale(domain=[70, 100]),
                ),
                y=alt.Y("deviasi_rpd_persen", title="Deviasi RPD (%)"),
                color=alt.Color(
                    "realisasi_tercapai_95persen:N",
                    title="Realisasi Tercapai 95%",
                ),
                tooltip=[
                    "kode_satker",
                    "provinsi",
                    "tipe_satker",
                    "skor_ikpa",
                    "deviasi_rpd_persen",
                    "realisasi_tercapai_95persen",
                ],
            )
            .properties(height=450)
            .interactive()
        )
        st.altair_chart(bubble_chart, width="stretch")
