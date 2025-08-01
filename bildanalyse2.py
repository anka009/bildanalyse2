import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
from streamlit_drawable_canvas import st_canvas

# Breites Layout
st.set_page_config(page_title="🔍 Kreis-Radar", layout="wide")
st.title("🛰️ Kreis-Radar Komfort-App")

# Sidebar: Bild & Einstellungen
uploaded_file = st.sidebar.file_uploader("📁 Bild auswählen", type=["png", "jpg", "jpeg"])
if not uploaded_file:
    st.warning("Bitte lade ein Bild hoch 🖼️")
    st.stop()

# Sidebar: Parameter
circle_color = st.sidebar.color_picker("🎨 Kreisfarbe", "#FF0000")
circle_width = st.sidebar.slider("🖌️ Liniendicke", 1, 10, 3)
analyse_farbe = st.sidebar.selectbox("🎯 Analyse-Farbe", ["Rot", "Grün", "Blau"])
min_intens = st.sidebar.slider("🔬 Min. Farbintensität", 0, 255, 150)

# Bild vorbereiten
img = Image.open(uploaded_file).convert("RGB")
w, h = img.size
img_array = np.array(img)

# Spalten-Layout
col_canvas, col_analysis = st.columns([2, 1])

# ▶️ Mausgesteuerte Kreiseingabe
with col_canvas:
    st.subheader("🖱️ Kreis zeichnen (Maus)")
    canvas_result = st_canvas(
        fill_color="rgba(0,0,0,0)",
        stroke_width=circle_width,
        stroke_color=circle_color,
        background_image=img_array,  # ✅ FIX: korrekt als NumPy-Array
        update_streamlit=True,
        height=h,
        width=w,
        drawing_mode="circle",
        key="canvas"
    )

# Auswertung nur wenn Kreis gezeichnet wurde
if canvas_result.json_data and canvas_result.json_data["objects"]:
    obj = canvas_result.json_data["objects"][0]
    cx = int(obj["left"] + obj["radius"])
    cy = int(obj["top"] + obj["radius"])
    r = int(obj["radius"])

    # Maske im Kreisbereich
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=255)

    masked_img = np.array(img) * np.array(mask)[:, :, None] // 255

    channel_index = {"Rot": 0, "Grün": 1, "Blau": 2}[analyse_farbe]
    farbkanal = masked_img[:, :, channel_index]
    pixel_count = np.count_nonzero(mask)
    matching_pixels = np.count_nonzero(farbkanal > min_intens)
    anteil = matching_pixels / pixel_count * 100 if pixel_count else 0

    with col_analysis:
        st.subheader("📊 Analyse-Ergebnis")
        st.write(f"• Mittelpunkt: ({cx}, {cy})")
        st.write(f"• Radius: {r} px")
        st.write(f"• Farbkanal: **{analyse_farbe}**")
        st.write(f"• Anteil intensiver Pixel: **{anteil:.1f}%**")

        # Vorschau des Ausschnitts
        result = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        result.paste(img.convert("RGBA"), mask=mask)
        bbox = mask.getbbox()
        cropped = result.crop(bbox)
        st.image(cropped, caption="✂️ Kreis-Ausschnitt", use_column_width=False)

else:
    with col_analysis:
        st.info("🔍 Zeichne zuerst einen Kreis mit der Maus, um Analyse zu starten.")
