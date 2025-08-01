import streamlit as st
from PIL import Image, ImageDraw
import numpy as np

# 🚀 App-Konfiguration
st.set_page_config(page_title="Kreis-Overlay App", layout="wide")
st.title("🔍 Kreis-Overlay Analyse")

# 📁 Bild-Upload
uploaded_file = st.sidebar.file_uploader("📂 Bild auswählen", type=["png", "jpg", "jpeg", "tif", "tiff"])
if not uploaded_file:
    st.warning("Bitte zuerst ein Bild hochladen.")
    st.stop()

# 🖼️ Bild laden & vorbereiten
img_rgb = Image.open(uploaded_file).convert("RGB")
w, h = img_rgb.size

# 🎯 Kreis-Parameter aus Sidebar
cx = st.sidebar.slider("🔹 Mittelpunkt X", 0, w, w // 2)
cy = st.sidebar.slider("🔹 Mittelpunkt Y", 0, h, h // 2)
r = st.sidebar.slider("🔹 Radius", 0, min(w, h) // 2, min(w, h) // 4)
farbe = st.sidebar.color_picker("🎨 Kreisfarbe", "#FF0000")
linien_dicke = st.sidebar.slider("🖊️ Liniendicke", 1, 10, 3)

# 🖼️ Overlay erzeugen
overlay = Image.new("RGBA", img_rgb.size, (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)
draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=farbe + "FF", width=linien_dicke)

# 🌈 Vorschau anzeigen
vorschau = Image.alpha_composite(img_rgb.convert("RGBA"), overlay)
st.image(vorschau, caption="🎯 Kreis-Vorschau", use_column_width=True)

# ✂️ Kreis ausschneiden
if st.button("✂️ Kreis ausschneiden"):
    mask = Image.new("L", img_rgb.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=255)

    result = Image.new("RGBA", img_rgb.size, (0, 0, 0, 0))
    result.paste(img_rgb.convert("RGBA"), mask=mask)

    bbox = mask.getbbox()
    ausschnitt = result.crop(bbox)

    st.success("✅ Kreis-Ausschnitt erstellt")
    st.image(ausschnitt, caption="📸 Ausgeschnittener Bereich", use_column_width=False)
