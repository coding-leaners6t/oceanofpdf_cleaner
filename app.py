# ===============================
# CLEAN PDF REBUILDER (NO JS)
# FULL GOOGLE COLAB SCRIPT
# ===============================

# ---------- Install dependencies ----------
!pip install pymupdf reportlab pillow pikepdf

# ---------- Upload PDF ----------
from google.colab import files
uploaded = files.upload()
input_pdf = list(uploaded.keys())[0]
print("Uploaded:", input_pdf)

# ---------- Extract text & images ----------
import fitz
import os

doc = fitz.open(input_pdf)
os.makedirs("images", exist_ok=True)

pages = []

for i, page in enumerate(doc):
    text = page.get_text("text")
    imgs = []

    for img_index, img in enumerate(page.get_images(full=True)):
        xref = img[0]
        base = doc.extract_image(xref)
        img_bytes = base["image"]
        img_path = f"images/p{i}_{img_index}.png"

        with open(img_path, "wb") as f:
            f.write(img_bytes)

        imgs.append(img_path)

    pages.append({
        "text": text,
        "images": imgs
    })

# ---------- Build SAFE PDF ----------
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image as RLImage, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from PIL import Image as PILImage

output_pdf = "clean_fixed.pdf"
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

doc = SimpleDocTemplate(
    output_pdf,
    pagesize=A4,
    leftMargin=1 * inch,
    rightMargin=1 * inch,
    topMargin=1 * inch,
    bottomMargin=1 * inch
)

doc.build(story)

# ---------- REMOVE JS / ACTIONS / METADATA (CORRECT) ----------
import pikepdf

with pikepdf.open(output_pdf) as pdf:
    root = pdf.Root

    # Remove Names tree (JS lives here)
    if "/Names" in root:
        del root["/Names"]

    # Remove automatic actions
    if "/OpenAction" in root:
        del root["/OpenAction"]

    if "/AA" in root:
        del root["/AA"]

    # Remove ALL metadata safely
    for key in list(pdf.docinfo.keys()):
        del pdf.docinfo[key]

    pdf.save("clean_fixed_nojs.pdf")

print("PDF cleaned successfully")

# ---------- Download ----------
files.download("clean_fixed_nojs.pdf")
