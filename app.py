# ===============================
# STREAMLIT PDF CLEANER (JS-FREE)
# ===============================

import streamlit as st
import fitz
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image as RLImage, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import pikepdf
import tempfile
import os

st.title("PDF Cleaner – Remove JS & Actions")

# ---------- Upload PDF ----------
uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
if uploaded_file is not None:
    st.write("Processing...")

    # Save uploaded PDF temporarily
    temp_dir = tempfile.mkdtemp()
    input_pdf_path = os.path.join(temp_dir, "input.pdf")
    with open(input_pdf_path, "wb") as f:
        f.write(uploaded_file.read())

    # ---------- Extract text & images ----------
    doc = fitz.open(input_pdf_path)
    img_dir = os.path.join(temp_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        imgs = []

        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base = doc.extract_image(xref)
            img_bytes = base["image"]
            img_path = os.path.join(img_dir, f"p{i}_{img_index}.png")
            with open(img_path, "wb") as f:
                f.write(img_bytes)
            imgs.append(img_path)

        pages.append({"text": text, "images": imgs})

    # ---------- Build new PDF ----------
    output_pdf_path = os.path.join(temp_dir, "clean_fixed.pdf")
    styles = getSampleStyleSheet()
    story = []

    def compress_image(path):
        img = PILImage.open(path)
        img.thumbnail((1200, 1200))
        new_path = path.replace(".png", "_small.jpg")
        img.save(new_path, "JPEG", quality=70)
        return new_path

    for page in pages:
        if page["text"].strip():
            for line in page["text"].split("\n"):
                story.append(Paragraph(line, styles["Normal"]))
            story.append(Spacer(1, 0.25 * inch))

        for img_path in page["images"]:
            small = compress_image(img_path)
            img = RLImage(small)
            img._restrictSize(5.5 * inch, 7 * inch)
            story.append(img)
            story.append(Spacer(1, 0.3 * inch))

        story.append(PageBreak())

    doc_r = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch
    )

    doc_r.build(story)

    # ---------- Remove JS / Actions ----------
    final_pdf_path = os.path.join(temp_dir, "clean_fixed_nojs.pdf")
    with pikepdf.open(output_pdf_path) as pdf:
        root = pdf.Root

        if "/Names" in root:
            del root["/Names"]
        if "/OpenAction" in root:
            del root["/OpenAction"]
        if "/AA" in root:
            del root["/AA"]

        for key in list(pdf.docinfo.keys()):
            del pdf.docinfo[key]

        pdf.save(final_pdf_path)

    # ---------- Provide download ----------
    with open(final_pdf_path, "rb") as f:
        st.download_button(
            label="Download Clean PDF",
            data=f.read(),
            file_name="clean_fixed_nojs.pdf",
            mime="application/pdf"
        )

    st.success("PDF cleaned successfully! ✅")
