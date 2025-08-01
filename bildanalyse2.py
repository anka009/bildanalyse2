import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
from scipy.ndimage import label, find_objects
from streamlit_drawable_canvas import st_canvas
from skimage.filters import threshold_otsu

st.set_page_config(page_title="Bildanalyse Komfort-App", layout="wide")
st.title("🧪 Bildanalyse Komfort-App")

# Sidebar: Upload
uploaded_file = st.sidebar.file_uploader("📁 Bild auswählen", type=["png", "jpg", "jpeg", "tif", "tiff"])
if not uploaded_file:
    st.stop()

# Bild laden & vorbereiten
img_rgb = Image.open(uploaded_file).convert("RGB")
img_gray = img_rgb.convert("L")
img_array = np.array(img_gray)
w, h = img_rgb.size

# Sidebar: Modus-Auswahl
modus = st.sidebar.radio("🛠️ Analyse-Modus", ["Fleckengruppen", "Kreis-Ausschnitt"])

# Session State für Intensitäts-Schwelle
if "intensity" not in st.session_state:
    st.session_state.intensity = 135

# Gemeinsame Parameter
min_area = st.sidebar.slider("🧬 Minimale Fleckengröße", 10, 500, 50)
max_area = st.sidebar.slider("🧬 Maximale Fleckengröße", min_area, 1000, 500)
group_diameter = st.sidebar.slider("📏 Gruppendurchmesser", 20, 500, 150)
circle_color = st.sidebar.color_picker("🎨 Kreisfarbe", "#FF0000")
circle_width = st.sidebar.slider("🖊️ Liniendicke", 1, 10, 4)

# ▓▓▓ MODUS 1: Fleckengruppen erkennen ▓▓▓
if modus == "Fleckengruppen":
    st.subheader("🧠 Fleckengruppen erkennen")

    # Bildbereich wählen
    x_start = st.slider("Start-X", 0, w - 1, 0)
    x_end = st.slider("End-X", x_start + 1, w, w)
    y_start = st.slider("Start-Y", 0, h - 1, 0)
    y_end = st.slider("End-Y", y_start + 1, h, h)
    cropped_array = img_array[y_start:y_end, x_start:x_end]

    # Auto-Schwelle
    def berechne_beste_schwelle(img_array, min_area, max_area, group_diameter):
        beste_anzahl, bester_wert = 0, 0
        for schwelle in range(10, 250, 5):
            mask = img_array < schwelle
            labeled_array, _ = label(mask)
            objects = find_objects(labeled_array)
            centers = [
                ((obj[1].start + obj[1].stop) // 2, (obj[0].start + obj[0].stop) // 2)
                for obj in objects
                if min_area <= np.sum(labeled_array[obj] > 0) <= max_area
            ]
            grouped, visited = [], set()
            for i, (x1, y1) in enumerate(centers):
                if i in visited: continue
                gruppe = [(x1, y1)]
                visited.add(i)
                for j, (x2, y2) in enumerate(centers):
                    if j in visited: continue
                    if ((x1 - x2)**2 + (y1 - y2)**2)**0.5 <= group_diameter / 2:
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

    # Schwellenwert-Slider
    intensity = st.slider("Intensitäts-Schwelle", 0, 255, st.session_state.intensity)

    # Fleckenerkennung & Gruppierung
    mask = cropped_array < intensity
    labeled_array, _ = label(mask)
    objects = find_objects(labeled_array)
    centers = [
        ((obj[1].start + obj[1].stop) // 2, (obj[0].start + obj[0].stop) // 2)
        for obj in objects
        if min_area <= np.sum(labeled_array[obj] > 0) <= max_area
    ]
    grouped, visited = [], set()
    for i, (x1, y1) in enumerate(centers):
        if i in visited: continue
        gruppe = [(x1, y1)]
        visited.add(i)
        for j, (x2, y2) in enumerate(centers):
            if j in visited: continue
            if ((x1 - x2)**2 + (y1 - y2)**2)**0.5 <= group_diameter / 2:
                gruppe.append((x2, y2))
                visited.add(j)
        grouped.append(gruppe)

    # Ergebnisse anzeigen
    draw_img = img_rgb.copy()
    draw = ImageDraw.Draw(draw_img)
    for gruppe in grouped:
        if gruppe:
            xs, ys = zip(*gruppe)
            x_mean, y_mean = int(np.mean(xs)), int(np.mean(ys))
            r = group_diameter // 2
            draw.ellipse([(x_mean - r, y_mean - r), (x_mean + r, y_mean + r)], outline=circle_color, width=circle_width)
    st.success(f"📍 {len(grouped)} Fleckengruppen erkannt")
    st.image(draw_img, caption="Gruppen-Vorschau", use_column_width=True)

# ▓▓▓ MODUS 2: Kreis-Ausschnitt ▓▓▓
elif modus == "Kreis-Ausschnitt":
    st.subheader("🔴 Kreis-Ausschnitt mit Live-Vorschau")

    # Kreis-Parameter
    cx = st.slider("Mittelpunkt X", 0, w, w // 2)
    cy = st.slider("Mittelpunkt Y", 0, h, h // 2)
    r  = st.slider("Radius", 0, min(w, h) // 2, min(w, h) // 4)

    # Kreis-Overlay
    def kreis_overlay(img, center, r, farbe="#FF0000"):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        x0, y0, x1, y1 = center[0] - r, center[1] - r, center[0] + r, center[1] + r
        draw.ellipse([(x0, y0), (x1, y1)], outline=farbe + "FF", width=3)
        return Image.alpha_composite(img.convert("RGBA"), overlay)

    preview = kreis_overlay(img_rgb, (cx, cy), r, farbe=circle_color)
    st.image(preview, caption="🔴 Kreis-Vorschau", use_column_width=True)

    # Ausschneiden
    if st.button("✂️ Kreis ausschneiden"):
        mask = Image.new("L", img_rgb.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=255)
        result = Image.new("RGBA", img_rgb.size, (0, 0, 0, 0))
        result.paste(img_rgb.convert("RGBA"), mask=mask)
        bbox = mask.getbbox()
        cropped = result.crop(bbox)
        st.success("📷 Ausschnitt erzeugt")
        st.image(cropped, caption="Kreis-Ausschnitt", use_column_width=False)
