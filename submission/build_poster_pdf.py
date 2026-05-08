from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


OUT_DIR = Path(__file__).resolve().parent
FIG_DIR = OUT_DIR / "figures"
POSTER_PATH = OUT_DIR / "case2_video_poster.pdf"


def draw_wrapped(c, text, x, y, max_width, font="Helvetica", size=8, leading=10, color=colors.black):
    c.setFont(font, size)
    c.setFillColor(color)
    words = text.split()
    line = ""
    for word in words:
        test = (line + " " + word).strip()
        if c.stringWidth(test, font, size) <= max_width:
            line = test
        else:
            c.drawString(x, y, line)
            y -= leading
            line = word
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y


def draw_box(c, x, y, w, h, title):
    c.setFillColor(colors.HexColor("#F7F9FC"))
    c.roundRect(x, y, w, h, 8, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#D6DEE8"))
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, 8, fill=0, stroke=1)
    c.setFillColor(colors.HexColor("#20364D"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + 0.35 * cm, y + h - 0.65 * cm, title)


def draw():
    page_w, page_h = landscape(A4)
    c = canvas.Canvas(str(POSTER_PATH), pagesize=landscape(A4))

    margin = 0.9 * cm
    title_h = 1.4 * cm
    c.setFillColor(colors.HexColor("#20364D"))
    c.rect(0, page_h - title_h, page_w, title_h, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(margin, page_h - 0.62 * cm, "Can Wearable Biosignals Reveal Subject-Invariant Stress States?")
    c.setFont("Helvetica", 8)
    c.drawRightString(page_w - margin, page_h - 1.08 * cm, "02582 Computational Data Analysis - Case 2")

    gutter = 0.45 * cm
    col_w = (page_w - 2 * margin - 2 * gutter) / 3
    top_y = page_h - title_h - 0.5 * cm
    box_h_top = 6.3 * cm
    box_h_bottom = 9.4 * cm

    # Top boxes
    draw_box(c, margin, top_y - box_h_top, col_w, box_h_top, "Aim and Data")
    y = top_y - 1.2 * cm
    y = draw_wrapped(
        c,
        "Research question: do HR, TEMP, and EDA features reveal experimental phase, or are they dominated by individual baselines and cohort effects?",
        margin + 0.35 * cm,
        y,
        col_w - 0.7 * cm,
        size=8.5,
    )
    y -= 0.15 * cm
    for bullet in [
        "312 observations = 26 individuals x 4 rounds x 3 phases.",
        "51 physiological features from HR, TEMP, and EDA.",
        "Labels used only for validation: Phase, Individual, Cohort, Puzzler, Frustrated.",
    ]:
        y = draw_wrapped(c, "- " + bullet, margin + 0.45 * cm, y, col_w - 0.9 * cm, size=8.2)

    x2 = margin + col_w + gutter
    draw_box(c, x2, top_y - box_h_top, col_w, box_h_top, "Pipeline")
    y = top_y - 1.2 * cm
    for bullet in [
        "Median imputation for the two missing feature values.",
        "Compare raw scaling, subject-wise z-score normalization, and phase1 baseline subtraction.",
        "PCA gives low-dimensional representations.",
        "KMeans with k=3 tests latent state discovery.",
        "LOSO logistic regression is used only as a supervised sanity check.",
    ]:
        y = draw_wrapped(c, "- " + bullet, x2 + 0.45 * cm, y, col_w - 0.9 * cm, size=8.2)

    x3 = margin + 2 * (col_w + gutter)
    draw_box(c, x3, top_y - box_h_top, col_w, box_h_top, "Key Numerical Results")
    y = top_y - 1.2 * cm
    for bullet in [
        "Raw PC1-PC5 explained variance: 58.4%.",
        "Raw representation R2: Individual 64.5%, Cohort 32.8%, Phase 3.0%.",
        "Subject-normalized phase R2 improves to 9.9%.",
        "KMeans phase agreement remains weak: ARI 0.075 after subject normalization.",
        "LOSO supervised sanity check: phase2-vs-phase1 AUC 0.779.",
    ]:
        y = draw_wrapped(c, "- " + bullet, x3 + 0.45 * cm, y, col_w - 0.9 * cm, size=8.2)

    # Bottom boxes
    bottom_y = margin
    wide_w = (page_w - 2 * margin - gutter) * 0.62
    right_w = page_w - 2 * margin - gutter - wide_w
    draw_box(c, margin, bottom_y, wide_w, box_h_bottom, "Evidence")
    c.drawImage(str(FIG_DIR / "figure1_pca_comparison.png"), margin + 0.35 * cm, bottom_y + 4.45 * cm, width=wide_w - 0.7 * cm, height=4.15 * cm, preserveAspectRatio=True)
    c.drawImage(str(FIG_DIR / "figure2_metadata_r2.png"), margin + 0.35 * cm, bottom_y + 0.55 * cm, width=(wide_w - 1.0 * cm) * 0.55, height=3.45 * cm, preserveAspectRatio=True)
    c.drawImage(str(FIG_DIR / "figure3_cluster_phase_heatmap.png"), margin + 0.35 * cm + (wide_w - 1.0 * cm) * 0.57, bottom_y + 0.55 * cm, width=(wide_w - 1.0 * cm) * 0.38, height=3.45 * cm, preserveAspectRatio=True)

    right_x = margin + wide_w + gutter
    draw_box(c, right_x, bottom_y, right_w, box_h_bottom, "Interpretation")
    y = bottom_y + box_h_bottom - 1.2 * cm
    y = draw_wrapped(
        c,
        "Main conclusion: the raw biosignal representation mainly captures who was measured and which cohort the measurement came from, not a clean emotional state.",
        right_x + 0.45 * cm,
        y,
        right_w - 0.9 * cm,
        font="Helvetica-Bold",
        size=8.6,
    )
    y -= 0.2 * cm
    for bullet in [
        "Subject-wise normalization is essential for wearable biosignals.",
        "The phase signal is weak but nonzero.",
        "Unsupervised PCA plus KMeans does not robustly discover pre-rest, puzzle, and post-rest states.",
        "A negative result is valid here because the pipeline diagnoses baseline dependence and weak signal strength.",
        "Future work should use temporal features or self-supervised representations with subject-level validation.",
    ]:
        y = draw_wrapped(c, "- " + bullet, right_x + 0.45 * cm, y, right_w - 0.9 * cm, size=8.2)

    c.setFillColor(colors.HexColor("#666666"))
    c.setFont("Helvetica", 7)
    c.drawString(margin, 0.35 * cm, "Use with video_poster_script.md. Student ID: s252646.")
    c.save()


if __name__ == "__main__":
    draw()
    print(POSTER_PATH)
