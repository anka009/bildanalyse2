import streamlit as st
from PIL import Image, ImageDraw, ImageStat
import numpy as np
from scipy.ndimage import label, find_objects
import io

st.set_page_config(layout="wide", page_title="Bildanalyse Komfort-App")

st.title("📷 Komfort-App für Bildzuschnitt & Fleckenerkennung")

# 📤 Bild hochladen
uploaded_file = st.sidebar.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png", "tif", "tiff"])
if uploaded_file:
    img_rgb = Image.open(uploaded_file).convert("RGB")
    img_gray = img_rgb.convert("L")
    width, height = img_rgb.size

    # 📑 Tabs für Navigation
    tab1, tab2 = st.tabs(["🟠 Runder Zuschnitt", "🔬 Fleckenerkennung"])

    with tab1:
        st.subheader("🎯 Kreisausschnitt erstellen")
        cx = st.slider("Mittelpunkt X", 0, width, width // 2)
        cy = st.slider("Mittelpunkt Y", 0, height, height // 2)
        radius = st.slider("Radius", 10, min(width, height) // 2, 100)

        def rundes_fragment(img, center, radius):
            mask = Image.new("L", img.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse([
                (center[0] - radius, center[1] - radius),
                (center[0] + radius, center[1] + radius)
            ], fill=255)
            img_rgba = img.convert("RGBA")
            img_rgba.putalpha(mask)
            fragment = img_rgba.crop((
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius
            ))
            return fragment

        if st.button("✂️ Ausschneiden & anzeigen"):
            fragment = rundes_fragment(img_rgb, (cx, cy), radius)
            st.image(fragment, caption="🖼️ Rundes Fragment", use_column_width=True)

            # 📊 Histogramm-Vorschau
            gray_frag = fragment.convert("L")
            hist = gray_frag.histogram()
            st.bar_chart(hist)

            # 💾 TIFF-Download vorbereiten
            buffer = io.BytesIO()
            fragment.save(buffer, format="TIFF")
            st.download_button("⬇️ Download TIFF", buffer.getvalue(), "fragment.tif", mime="image/tiff")

    with tab2:
        st.subheader("🧪 Fleckenerkennung im Ausschnitt")

        x_start = st.slider("Start-X", 0, width - 1, 0)
        x_end = st.slider("End-X", x_start + 1, width, width)
        y_start = st.slider("Start-Y", 0, height - 1, 0)
        y_end = st.slider("End-Y", y_start + 1, height, height)
        cropped_array = np.array(img_gray)[y_start:y_end, x_start:x_end]

        st.image(img_rgb.crop((x_start, y_start, x_end, y_end)), caption="🔍 Ausschnitt für Analyse", use_column_width=True)

        st.markdown("### ⚙️ Analyseparameter")
        min_area = st.slider("Min. Fleckengröße", 10, 500, 50)
        max_area = st.slider("Max. Fleckengröße", min_area, 1000, 500)
        group_diameter = st.slider("Gruppendurchmesser", 20, 500, 150)
        intensity_threshold = st.slider("Intensitäts-Schwelle", 0, 255, value=135)

        mask = cropped_array < intensity_threshold
        labeled_array, _ = label(mask)
        objects = find_objects(labeled_array)
        centers = []
        for obj_slice in objects:
            area = np.sum(labeled_array[obj_slice] > 0)
            if min_area <= area <= max_area:
                y = (obj_slice[0].start + obj_slice[0].stop) // 2 + y_start
                x = (obj_slice[1].start + obj_slice[1].stop) // 2 + x_start
                centers.append((x, y))

        # 🧠 Gruppierung
        grouped = []
        visited = set()
        for i, (x1, y1) in enumerate(centers):
            if i in visited: continue
            gruppe = [(x1, y1)]
            visited.add(i)
            for j, (x2, y2) in enumerate(centers):
                if j in visited: continue
                dist = ((x1 - x2)**2 + (y1 - y2)**2)**0.5
                if dist <= group_diameter / 2:
                    gruppe.append((x2, y2))
                    visited.add(j)
            grouped.append(gruppe)

        # 📷 Ergebnisse anzeigen
        draw_img = img_rgb.copy()
        draw = ImageDraw.Draw(draw_img)
        for gruppe in grouped:
            xs, ys = zip(*gruppe)
            x_mean = int(np.mean(xs))
            y_mean = int(np.mean(ys))
            r = group_diameter // 2
            draw.ellipse([
                (x_mean - r, y_mean - r),
                (x_mean + r, y_mean + r)
            ], outline="red", width=3)

        st.image(draw_img, caption=f"🧬 {len(grouped)} Fleckengruppen erkannt", use_column_width=True)

        # 📋 Tabelle ausgeben
        st.subheader("📋 Gruppenzentren")
        gruppe_data = [{"Gruppe": i+1, "X": int(np.mean([pt[0] for pt in g])), "Y": int(np.mean([pt[1] for pt in g]))}
                       for i, g in enumerate(grouped)]
        st.dataframe(gruppe_data)

else:
    st.info("📥 Lade zuerst ein Bild hoch, um loszulegen.")
