import streamlit as st
from PIL import Image, ImageDraw, ImageOps
import numpy as np
from scipy.ndimage import label, find_objects
import cv2

# 🧠 Hilfsfunktion zur Schwellenwert-Berechnung
def berechne_beste_schwelle(img_array, min_area, max_area, group_diameter):
    beste_anzahl = 0
    bester_wert = 0
    for schwelle in range(10, 250, 5):
        mask = img_array < schwelle
        labeled_array, _ = label(mask)
        objects = find_objects(labeled_array)
        centers = []
        for obj_slice in objects:
            area = np.sum(labeled_array[obj_slice] > 0)
            if min_area <= area <= max_area:
                y = (obj_slice[0].start + obj_slice[0].stop) // 2
                x = (obj_slice[1].start + obj_slice[1].stop) // 2
                centers.append((x, y))
        grouped = []
        visited = set()
        for i, (x1, y1) in enumerate(centers):
            if i in visited:
                continue
            gruppe = [(x1, y1)]
            visited.add(i)
            for j, (x2, y2) in enumerate(centers):
                if j in visited:
                    continue
                dist = ((x1 - x2)**2 + (y1 - y2)**2)**0.5
                if dist <= group_diameter / 2:
                    gruppe.append((x2, y2))
                    visited.add(j)
            grouped.append(gruppe)
        if len(grouped) > beste_anzahl:
            beste_anzahl = len(grouped)
            bester_wert = schwelle
    return bester_wert, beste_anzahl

# 🌟 UI-Setup
st.set_page_config(layout="wide")
st.title("🧪 Dunkle Fleckengruppen erkennen")

uploaded_file = st.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png", "tif", "tiff"])

if uploaded_file:
    img_rgb = Image.open(uploaded_file).convert("RGB")
    img_gray = img_rgb.convert("L")
    img_array = np.array(img_gray)
    width, height = img_rgb.size

    # 📐 Steuerung
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("🔧 Parameter")
        min_area = st.slider("Minimale Fleckengröße", 10, 500, 50)
        max_area = st.slider("Maximale Fleckengröße", min_area, 1000, 500)
        group_diameter = st.slider("Gruppendurchmesser", 20, 500, 150)
        intensity_threshold = st.slider("Intensitäts-Schwelle", 0, 255, 135)
        circle_color = st.color_picker("Kreisfarbe", "#FF0000")
        circle_width = st.slider("Liniendicke der Kreise", 1, 10, 4)

        show_overlay = st.checkbox("🔴 Maske als Overlay anzeigen")
        show_contours = st.checkbox("🟢 Maske-Konturen anzeigen")

        st.markdown("---")
        st.subheader("🧭 Bereichsverschiebung")
        verschiebung_x = st.slider("Horizontale Verschiebung", -100, 100, 0)
        verschiebung_y = st.slider("Vertikale Verschiebung", -100, 100, 0)

        st.markdown("---")
        if st.button("🎯 Beste Schwelle berechnen"):
            bester_wert, max_anzahl = berechne_beste_schwelle(img_array, min_area, max_area, group_diameter)
            st.success(f"Empfohlene Schwelle: {bester_wert} ({max_anzahl} Gruppen)")
            intensity_threshold = bester_wert  # sofort übernehmen

    with col2:
        x_start = max(0, verschiebung_x)
        x_end = min(width, width + verschiebung_x)
        y_start = max(0, verschiebung_y)
        y_end = min(height, height + verschiebung_y)

        cropped_array = img_array[y_start:y_end, x_start:x_end]
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

        # Gruppenbildung
        grouped = []
        visited = set()
        for i, (x1, y1) in enumerate(centers):
            if i in visited:
                continue
            gruppe = [(x1, y1)]
            visited.add(i)
            for j, (x2, y2) in enumerate(centers):
                if j in visited:
                    continue
                dist = ((x1 - x2)**2 + (y1 - y2)**2)**0.5
                if dist <= group_diameter / 2:
                    gruppe.append((x2, y2))
                    visited.add(j)
            grouped.append(gruppe)

        # Ausgabe-Bild
        draw_img = img_rgb.copy()
        draw = ImageDraw.Draw(draw_img)
        for gruppe in grouped:
            xs, ys = zip(*gruppe)
            x_mean = int(np.mean(xs))
            y_mean = int(np.mean(ys))
            radius = group_diameter // 2
            draw.ellipse(
                [(x_mean - radius, y_mean - radius), (x_mean + radius, y_mean + radius)],
                outline=circle_color,
                width=circle_width,
            )

        # Maske Overlay
        if show_overlay:
            mask_rgb = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
            mask_rgb[mask] = [255, 0, 0]
            mask_img = Image.fromarray(mask_rgb).convert("RGBA")
            mask_img.putalpha(100)
            cropped_rgba = img_rgb.crop((x_start, y_start, x_end, y_end)).convert("RGBA")
            overlay = Image.alpha_composite(cropped_rgba, mask_img)
            st.image(overlay, caption="🔴 Overlay-Maske", use_column_width=True)

        # Maske-Konturen
        if show_contours:
            mask_uint8 = np.uint8(mask * 255)
            contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            draw_img_np = np.array(draw_img)
            cv2.drawContours(draw_img_np, contours, -1, (0, 255, 0), 2)
            st.image(draw_img_np, caption="🟢 Masken-Konturen", use_column_width=True)
        else:
            st.image(draw_img, caption="📍 Erkannte Gruppen", use_column_width=True)

        st.success(f"{len(grouped)} Gruppen erkannt")

