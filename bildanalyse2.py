import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
from streamlit_drawable_canvas import st_canvas

# 🎨 App-Konfiguration
st.set_page_config(page_title="Kreis-Radar", layout="wide")
st.title("🔍 Kreis-Radar")

# 📂 Bild-Upload im Sidebar
uploaded_file = st.sidebar.file_uploader("📁 Bild auswählen", type=["png", "jpg", "jpeg", "tif", "tiff"])
if not uploaded_file:
    st.warning("Bitte zuerst ein Bild hochladen.")
    st.stop()

# 🖼️ Bild laden & vorbereiten
img = Image.open(uploaded_file).convert("RGB")
img_array = np.array(img)
w, h = img.size

# 🎯 Zeichen-Parameter
circle_color = st.sidebar.color_picker("🎨 Kreisfarbe", "#FF0000")
circle_width = st.sidebar.slider("🖊️ Liniendicke", 1, 10, 4)

# 🎨 Zeichenfläche anzeigen
canvas_result = st_canvas(
    fill_color="rgba(0,0,0,0)",  # transparenter Hintergrund
    stroke_width=circle_width,
    stroke_color=circle_color,
    background_image=img_array,  # ✅ korrekter NumPy-Array
    update_streamlit=True,
    height=h,
    width=w,
    drawing_mode="circle",
    key="canvas"
)

# 💾 Ergebnis anzeigen
if canvas_result.image_data is not None:
    st.subheader("🎉 Deine Zeichnung:")
    st.image(canvas_result.image_data, caption="Canvas-Ergebnis", use_column_width=True)
