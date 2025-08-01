import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="🔍 Kreis-Radar", layout="wide")
st.title("🛰️ Kreis-Radar Komfort-App")

# Sidebar: Upload & Parameter
uploaded_file = st.sidebar.file_uploader("📁 Bild hochladen", type=["jpg", "jpeg", "png"])
if not uploaded_file:
    st.warning("Bitte lade ein Bild hoch 🖼️")
    st.stop()

circle_color = st.sidebar.color_picker("🎨 Kreisfarbe", "#FF0000")
circle_width = st.sidebar.slider("🖌️ Liniendicke", 1, 10, 3)
analyse_farbe = st.sidebar.selectbox("🎯 Analyse-Farbe", ["Rot", "Grün", "Blau"])
min_intens = st.sidebar.slider("🔬 Min. Farbintensität", 0, 255, 150)

# Bild vorbereiten
img = Image.open(uploaded_file).convert("RGB")
img_array = np.array(img)
w, h = img.size

# Spaltenlayout
col_canvas, col_analysis = st.columns([2, 1])

with col_canvas:
    st.subheader("🖱️ Zeichne einen Kreis")
    canvas_result = st_canvas(
        fill_color="rgba(0,0,0,0)",
        stroke_width=circle_width,
        stroke_color=circle_color,
        background_image=img_array,  # ✅ FIX: korrektes Format
        update_streamlit=True,
        height=h,
        width=w,
        drawing_mode="circle",
        key="canvas"
    )

if canvas_result.json_data and canvas_result.json_data["objects"]:
    obj = canvas_result.json_data["objects"][0]
    cx = int(obj["left"] + obj["radius"])
    cy = int(obj["top"] + obj["radius"])
    r = int(obj["radius"])

    # Maske erstellen
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

        # Ausschnitt anzeigen
        result = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        result.paste(img.convert("RGBA"), mask=mask)
        bbox = mask.getbbox()
        cropped = result.crop(bbox)
        st.image(cropped, caption="✂️ Kreis-Ausschnitt", use_column_width=False)

else:
    with col_analysis:
        st.info("⚡ Zeichne einen Kreis im Bild, um ihn auszuschneiden und zu analysieren.")
