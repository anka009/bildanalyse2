import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
from scipy.ndimage import label, find_objects
from streamlit_drawable_canvas import st_canvas

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

# 🌟 Streamlit UI
st.title("Dunkle Fleckengruppen erkennen 🧪")

uploaded_file = st.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png", "tif", "tiff"])

min_area = st.slider("Minimale Fleckengröße (Pixel)", 10, 500, 50)
max_area = st.slider("Maximale Fleckengröße (Pixel)", min_area, 1000, 500)
group_diameter = st.slider("Gruppendurchmesser", 20, 500, 150)
circle_color = st.color_picker("Kreisfarbe 🎨", "#FF0000")
circle_width = st.slider("Liniendicke der Kreise", 1, 10, 4)

# Session State für Intensität
if "intensity" not in st.session_state:
    st.session_state.intensity = 135

if uploaded_file:
    # 📥 Bild vorbereiten
    img_rgb = Image.open(uploaded_file).convert("RGB")
    img_gray = img_rgb.convert("L")

    st.subheader("🎯 Polygon zeichnen zum Beschneiden")
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0.3)",
        stroke_width=2,
        stroke_color="#0000FF",
        background_image=img_rgb,
        update_streamlit=True,
        height=img_rgb.height,
        width=img_rgb.width,
        drawing_mode="polygon",
        point_display_radius=3,
        key="canvas",
    )

    # 🖍️ Polygon-Maske anwenden
    img_array = np.array(img_gray)
    if canvas_result.json_data and "objects" in canvas_result.json_data:
        obj = canvas_result.json_data["objects"]
        if obj and obj[0]["type"] == "polygon":
            punkte = [(p["x"], p["y"]) for p in obj[0]["points"]]
            maske = Image.new("L", img_rgb.size, 0)
            draw_mask = ImageDraw.Draw(maske)
            draw_mask.polygon(punkte, fill=255)
            masked = Image.composite(Image.fromarray(img_array), Image.new("L", img_rgb.size, 0), maske)
            img_array = np.array(masked)

    # 🎯 Button zur Schwellenwertsuche
    if st.button("🎯 Beste Intensitäts-Schwelle suchen"):
        bester_wert, max_anzahl = berechne_beste_schwelle(img_array, min_area, max_area, group_diameter)
        st.session_state.intensity = bester_wert
        st.success(f"Empfohlene Schwelle: {bester_wert} → {max_anzahl} Gruppen erkannt")

    # 🎚️ Intensitätsregler anzeigen
    intensity_threshold = st.slider("Intensitäts-Schwelle", 0, 255, value=st.session_state.intensity)

    # 🔍 Fleckenerkennung
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

    # 📍 Gruppenbildung
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

    # 📷 Ausgabe erzeugen
    draw_img = img_rgb.copy()
    draw = ImageDraw.Draw(draw_img)
    for gruppe in grouped:
        if gruppe:
            xs, ys = zip(*gruppe)
            x_mean = int(np.mean(xs))
            y_mean = int(np.mean(ys))
            radius = group_diameter // 2
            draw.ellipse(
                [(x_mean - radius, y_mean - radius), (x_mean + radius, y_mean + radius)],
                outline=circle_color,
                width=circle_width,
            )

    st.success(f"📍 {len(grouped)} Fleckengruppen erkannt")
    st.image(draw_img, caption="Erkannte Gruppen", use_column_width=True)
