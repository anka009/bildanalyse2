import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
from scipy.ndimage import label, find_objects

# 🔧 Schwellenwert-Optimierung
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

# 🎯 Streamlit Oberfläche
st.title("Dunkle Fleckengruppen erkennen")

uploaded_file = st.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png", "tif", "tiff"])

min_area = st.slider("Minimale Fleckengröße", 10, 500, 50)
max_area = st.slider("Maximale Fleckengröße", min_area, 1000, 500)
group_diameter = st.slider("Gruppendurchmesser", 20, 500, 100)
circle_color = st.color_picker("Kreisfarbe 🎨", "#FF0000")
circle_width = st.slider("Liniendicke der Kreise", 1, 10, 6)

# Initialwert setzen
if "intensity" not in st.session_state:
    st.session_state.intensity = 135

# 📤 Nach Upload – Empfehlung nur per Knopf
if uploaded_file:
    img = Image.open(uploaded_file).convert("L")
    img_array = np.array(img)

    # 🔘 Button zur Schwellenwert-Suche
    if st.button("🎯 Beste Intensitäts-Schwelle suchen"):
        bester_wert, max_anzahl = berechne_beste_schwelle(
            img_array, min_area, max_area, group_diameter
        )
        st.session_state.intensity = bester_wert
        st.success(f"Empfohlene Schwelle: {bester_wert} → {max_anzahl} Gruppen erkannt")

    # 🎚️ Slider mit aktualisiertem Startwert
    intensity_threshold = st.slider(
        "Intensitäts-Schwelle", 0, 255, value=st.session_state.intensity
    )


    # 🖼️ Fleckengruppen zeichnen
    mask = img_array < intensity_threshold
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

    img_draw = Image.open(uploaded_file).convert("RGB")
    draw = ImageDraw.Draw(img_draw)
    for gruppe in grouped:
        if gruppe:
            xs, ys = zip(*gruppe)
            x_mean = int(np.mean(xs))
            y_mean = int(np.mean(ys))
            radius = group_diameter // 2
            draw.ellipse(
                [(x_mean - radius, y_mean - radius), (x_mean + radius, y_mean + radius)],
                outline=circle_color,
                width=circle_width
            )

    st.success(f"📍 {len(grouped)} Fleckengruppen erkannt")
    st.image(img_draw, caption="Markierte Fleckengruppen", use_column_width=True)
