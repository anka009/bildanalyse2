import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
from scipy.ndimage import label, find_objects
from streamlit_drawable_canvas import st_canvas

# 🌟 Titel
st.title("🧪 Fleckenerkennung & Runder Zuschnitt")

# 📤 Bild hochladen
uploaded_file = st.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png", "tif", "tiff"])
if uploaded_file:
    img_rgb = Image.open(uploaded_file).convert("RGB")
    img_gray = img_rgb.convert("L")
    width, height = img_rgb.size
    st.image(img_rgb, caption="Originalbild", use_column_width=True)

    st.markdown("---")
    st.subheader("🟠 Rundes Fragment manuell ausschneiden")

    # 📍 Mittelpunkt und Radius
    cx = st.slider("Mittelpunkt X", 0, width, width // 2)
    cy = st.slider("Mittelpunkt Y", 0, height, height // 2)
    radius = st.slider("Radius", 10, min(width, height) // 2, 100)

    # ✂️ Runde Ausschneidefunktion
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

    # 💾 Ausschneiden & Speichern
    if st.button("✂️ Rundes Fragment ausschneiden & speichern"):
        fragment = rundes_fragment(img_rgb, (cx, cy), radius)
        fragment.save("rundes_fragment.tif", format="TIFF")
        st.image(fragment, caption="Rundes Fragment", use_column_width=True)
        st.success("✅ 'rundes_fragment.tif' gespeichert!")

    st.markdown("---")
    st.subheader("🎯 Rechteck-Ausschnitt zur Fleckenerkennung")

    x_start = st.slider("Start-X", 0, width - 1, 0)
    x_end = st.slider("End-X", x_start + 1, width, width)
    y_start = st.slider("Start-Y", 0, height - 1, 0)
    y_end = st.slider("End-Y", y_start + 1, height, height)
    cropped_array = np.array(img_gray)[y_start:y_end, x_start:x_end]

    # 🔬 Fleckenerkennung
    min_area = st.slider("Min. Fleckengröße", 10, 500, 50)
    max_area = st.slider("Max. Fleckengröße", min_area, 1000, 500)
    group_diameter = st.slider("Gruppendurchmesser", 20, 500, 150)
    circle_color = st.color_picker("Kreisfarbe", "#FF0000")
    circle_width = st.slider("Liniendicke", 1, 10, 4)

    if "intensity" not in st.session_state:
        st.session_state.intensity = 135

    # 🔍 Beste Schwelle suchen
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
            # Gruppieren
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
            if len(grouped) > beste_anzahl:
                beste_anzahl = len(grouped)
                bester_wert = schwelle
        return bester_wert, beste_anzahl

    if st.button("🎯 Beste Intensitäts-Schwelle suchen"):
        bester_wert, max_anzahl = berechne_beste_schwelle(cropped_array, min_area, max_area, group_diameter)
        st.session_state.intensity = bester_wert
        st.success(f"Empfohlene Schwelle: {bester_wert} → {max_anzahl} Gruppen erkannt")

    # 🌡️ Schwellenwert-Regler
    intensity_threshold = st.slider("Intensitäts-Schwelle", 0, 255, value=st.session_state.intensity)

    # 🎯 Fleckenerkennung ausführen
    mask = cropped_array < intensity_threshold
    labeled_array, _ = label(mask)
    objects = find_objects(labeled_array)
    centers = []
    for obj_slice in objects:
        area = np.sum(labeled_array[obj_slice] > 0)
        if min_area <= area <= max_area:
            y = (obj_slice[0].start + obj_slice[0].stop) // 2
            x = (obj_slice[1].start + obj_slice[1].stop) // 2
            centers.append((x, y))

    # 🧠 Gruppenbildung
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
        if gruppe:
            xs, ys = zip(*gruppe)
            x_mean = int(np.mean(xs))
            y_mean = int(np.mean(ys))
            radius = group_diameter // 2
            draw.ellipse([
                (x_mean - radius, y_mean - radius),
                (x_mean + radius, y_mean + radius)
            ], outline=circle_color, width=circle_width)

    st.success(f"📍 {len(grouped)} Fleckengruppen erkannt")
    st.image(draw_img, caption="Erkannte Gruppen", use_column_width=True)
