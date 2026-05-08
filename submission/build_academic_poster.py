from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


BASE_DIR = Path(__file__).resolve().parent
FIG_DIR = BASE_DIR / "figures"
TABLE_DIR = BASE_DIR / "tables"

OUT_PNG = BASE_DIR / "case2_academic_poster.png"
OUT_PDF = BASE_DIR / "case2_academic_poster.pdf"

W, H = 5760, 3240
DPI = 300

COLORS = {
    "bg": "#F6F1E8",
    "card": "#FFFEFA",
    "card2": "#FBF7EF",
    "ink": "#0B1F33",
    "muted": "#59707A",
    "blue": "#143A5A",
    "green": "#1B4D3E",
    "orange": "#C66A23",
    "sand": "#EADFCB",
    "line": "#D8CCB8",
    "pale_blue": "#E6EEF2",
    "pale_green": "#E7F0EA",
    "pale_orange": "#F4E2D2",
}


def font_path(name: str) -> str:
    candidates = [
        Path(r"C:\Windows\Fonts") / name,
        Path("/usr/share/fonts/truetype/dejavu") / name,
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    return str(Path(r"C:\Windows\Fonts\arial.ttf"))


FONT_TITLE = font_path("bahnschrift.ttf")
FONT_BODY = font_path("Candara.ttf")
FONT_BODY_BOLD = font_path("Candarab.ttf")
FONT_SERIF_BOLD = font_path("georgiab.ttf")


def fnt(size: int, bold: bool = False, title: bool = False, serif: bool = False) -> ImageFont.FreeTypeFont:
    if title:
        return ImageFont.truetype(FONT_TITLE, size)
    if serif:
        return ImageFont.truetype(FONT_SERIF_BOLD, size)
    return ImageFont.truetype(FONT_BODY_BOLD if bold else FONT_BODY, size)


def text_len(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> float:
    return draw.textlength(text, font=font)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if text_len(draw, trial, font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
    max_width: int,
    line_gap: int = 8,
) -> int:
    x, y = xy
    line_h = int(font.size * 1.16)
    for line in wrap_text(draw, text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h + line_gap
    return y


def shadow_box(
    image: Image.Image,
    box: tuple[int, int, int, int],
    radius: int,
    fill: str,
    outline: str | None = None,
    shadow: tuple[int, int, int, int] = (22, 31, 43, 32),
    offset: tuple[int, int] = (0, 16),
) -> None:
    x1, y1, x2, y2 = box
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(layer)
    sx, sy = offset
    layer_draw.rounded_rectangle((x1 + sx, y1 + sy, x2 + sx, y2 + sy), radius=radius, fill=shadow)
    layer = layer.filter(ImageFilter.GaussianBlur(22))
    image.alpha_composite(layer)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=3 if outline else 1)


def draw_section_header(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    title: str,
    color: str,
    kicker: str | None = None,
) -> None:
    draw.rounded_rectangle((x, y + 8, x + 18, y + 78), radius=9, fill=color)
    draw.text((x + 36, y), title, font=fnt(50, bold=True, title=True), fill=COLORS["ink"])
    if kicker:
        draw.text((x + 38, y + 62), kicker.upper(), font=fnt(24, bold=True), fill=color)


def draw_bullets(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    width: int,
    items: list[str],
    font: ImageFont.FreeTypeFont,
    fill: str = COLORS["ink"],
    bullet_color: str = COLORS["orange"],
    gap: int = 22,
) -> int:
    line_h = int(font.size * 1.13)
    for item in items:
        lines = wrap_text(draw, item, font, width - 44)
        draw.ellipse((x, y + 14, x + 17, y + 31), fill=bullet_color)
        tx = x + 42
        for i, line in enumerate(lines):
            draw.text((tx, y + i * line_h), line, font=font, fill=fill)
        y += len(lines) * line_h + gap
    return y


def load_summary() -> dict:
    with open(TABLE_DIR / "analysis_summary.json", "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_metric_csv(path: Path) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def metric_lookup(rows: list[dict[str, str]], version: str, label: str) -> float:
    for row in rows:
        if row["version"] == version and row["label"] == label:
            return float(row["weighted_r2"])
    raise KeyError((version, label))


def model_lookup(rows: list[dict[str, str]], version: str, field: str) -> float:
    for row in rows:
        if row["version"] == version:
            return float(row[field])
    raise KeyError((version, field))


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def trim_white(image: Image.Image, border: int = 14) -> Image.Image:
    rgb = image.convert("RGB")
    bg = Image.new("RGB", rgb.size, (255, 255, 255))
    diff = ImageChops.difference(rgb, bg).convert("L")
    mask = diff.point(lambda p: 255 if p > 8 else 0)
    bbox = mask.getbbox()
    if not bbox:
        return rgb
    left, top, right, bottom = bbox
    left = max(0, left - border)
    top = max(0, top - border)
    right = min(rgb.width, right + border)
    bottom = min(rgb.height, bottom + border)
    return rgb.crop((left, top, right, bottom))


def load_figure(name: str) -> Image.Image:
    image = Image.open(FIG_DIR / name).convert("RGBA")
    white = Image.new("RGBA", image.size, (255, 255, 255, 255))
    white.alpha_composite(image)
    return trim_white(white.convert("RGB"))


def paste_fit(canvas: Image.Image, image: Image.Image, box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    scale = min(bw / image.width, bh / image.height)
    new_w, new_h = int(image.width * scale), int(image.height * scale)
    resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    px = x1 + (bw - new_w) // 2
    py = y1 + (bh - new_h) // 2
    canvas.paste(resized, (px, py))
    return (px, py, px + new_w, py + new_h)


def figure_panel(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    image: Image.Image,
    caption: str,
    accent: str,
    caption_size: int = 27,
) -> None:
    x1, y1, x2, y2 = box
    shadow_box(canvas, box, radius=30, fill="#FFFFFF", outline="#E7DECF", shadow=(18, 32, 45, 20), offset=(0, 10))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((x1 + 24, y1 + 22, x1 + 38, y2 - 22), radius=7, fill=accent)
    caption_h = 72
    paste_fit(canvas, image, (x1 + 58, y1 + 28, x2 - 36, y2 - caption_h - 12))
    draw_wrapped(
        draw,
        (x1 + 58, y2 - caption_h + 3),
        caption,
        fnt(caption_size),
        COLORS["muted"],
        x2 - x1 - 96,
        line_gap=3,
    )


def draw_metric_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    value: str,
    note: str,
    accent: str,
) -> None:
    x1, y1, x2, y2 = box
    shadow_box(canvas, box, radius=26, fill="#FFFFFF", outline="#E9DDCC", shadow=(18, 32, 45, 18), offset=(0, 8))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((x1, y1, x2, y1 + 13), radius=7, fill=accent)
    draw.text((x1 + 28, y1 + 28), label.upper(), font=fnt(24, bold=True), fill=accent)
    draw.text((x1 + 28, y1 + 66), value, font=fnt(61, bold=True, serif=True), fill=COLORS["ink"])
    draw.text((x1 + 30, y1 + 128), note, font=fnt(25), fill=COLORS["muted"])


def draw_phase_timeline(draw: ImageDraw.ImageDraw, x: int, y: int, width: int) -> None:
    phases = [
        ("Phase 1", "pre-rest", COLORS["blue"], COLORS["pale_blue"]),
        ("Phase 2", "puzzle competition", COLORS["orange"], COLORS["pale_orange"]),
        ("Phase 3", "post-rest", COLORS["green"], COLORS["pale_green"]),
    ]
    gap = 18
    seg_w = (width - 2 * gap) // 3
    for i, (phase, label, color, fill) in enumerate(phases):
        x1 = x + i * (seg_w + gap)
        x2 = x1 + seg_w
        draw.rounded_rectangle((x1, y, x2, y + 116), radius=28, fill=fill, outline=color, width=3)
        draw.text((x1 + 28, y + 21), phase, font=fnt(26, bold=True), fill=color)
        draw.text((x1 + 28, y + 59), label, font=fnt(30), fill=COLORS["ink"])
        if i < 2:
            ax = x2 + 4
            ay = y + 58
            draw.line((ax, ay, ax + gap - 8, ay), fill=COLORS["line"], width=5)
            draw.polygon([(ax + gap - 8, ay - 10), (ax + gap - 8, ay + 10), (ax + gap + 4, ay)], fill=COLORS["line"])


def draw_pipeline(draw: ImageDraw.ImageDraw, x: int, y: int, width: int) -> None:
    steps = [
        ("01", "Median imputation", "Resolve sparse missing EDA features"),
        ("02", "Raw scaling", "Standardize feature scale"),
        ("03", "Subject-wise z-score", "Remove personal baseline offsets"),
        ("04", "Phase1 baseline subtraction", "Model phase2/phase3 as deviations"),
        ("05", "PCA representation", "Use PC1-PC5 for structure checks"),
        ("06", "KMeans clustering", "k=3 compared against phase labels"),
        ("07", "LOSO sanity check", "Supervised subject-level validation"),
    ]
    box_h = 126
    gap = 24
    for i, (num, title, desc) in enumerate(steps):
        y1 = y + i * (box_h + gap)
        fill = "#FFFFFF" if i not in (2, 3, 6) else COLORS["pale_green"]
        outline = COLORS["green"] if i in (2, 3, 6) else COLORS["line"]
        draw.rounded_rectangle((x, y1, x + width, y1 + box_h), radius=24, fill=fill, outline=outline, width=3)
        draw.rounded_rectangle((x + 22, y1 + 27, x + 96, y1 + 99), radius=18, fill=COLORS["blue"] if i < 4 else COLORS["orange"])
        draw.text((x + 43, y1 + 45), num, font=fnt(27, bold=True, title=True), fill="#FFFFFF")
        draw.text((x + 124, y1 + 22), title, font=fnt(35, bold=True), fill=COLORS["ink"])
        draw.text((x + 124, y1 + 70), desc, font=fnt(27), fill=COLORS["muted"])
        if i < len(steps) - 1:
            cx = x + width // 2
            ay = y1 + box_h + 4
            draw.line((cx, ay, cx, ay + gap - 8), fill=COLORS["line"], width=4)
            draw.polygon([(cx - 10, ay + gap - 8), (cx + 10, ay + gap - 8), (cx, ay + gap + 4)], fill=COLORS["line"])


def build() -> None:
    summary = load_summary()
    metadata_rows = load_metric_csv(TABLE_DIR / "metadata_r2.csv")
    model_rows = load_metric_csv(TABLE_DIR / "model_summary.csv")

    n_rows = summary["n_rows"]
    n_people = summary["n_individuals"]
    n_features = summary["n_features"]
    phase_r2_raw = metric_lookup(metadata_rows, "raw_scaled", "Phase")
    phase_r2_subject = metric_lookup(metadata_rows, "subject_z", "Phase")
    individual_r2_raw = metric_lookup(metadata_rows, "raw_scaled", "Individual")
    cohort_r2_raw = metric_lookup(metadata_rows, "raw_scaled", "Cohort")
    ari_subject = model_lookup(model_rows, "subject_z", "kmeans_ari_phase")
    auc_loso = summary["supervised_sanity_loso_logistic"]["auc"]

    fig1 = load_figure("figure1_pca_comparison.png")
    fig2 = load_figure("figure2_metadata_r2.png")
    fig3 = load_figure("figure3_cluster_phase_heatmap.png")
    fig4 = load_figure("figure4_supervised_sanity_roc.png")

    canvas = Image.new("RGBA", (W, H), COLORS["bg"])
    draw = ImageDraw.Draw(canvas)

    # Soft background fields keep the academic layout from feeling flat.
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wash_draw = ImageDraw.Draw(wash)
    wash_draw.ellipse((4440, -430, 6420, 1190), fill=(20, 58, 90, 35))
    wash_draw.ellipse((-430, 2460, 1400, 3860), fill=(198, 106, 35, 28))
    wash_draw.rounded_rectangle((3420, 2540, 6200, 3560), radius=260, fill=(27, 77, 62, 24))
    wash = wash.filter(ImageFilter.GaussianBlur(42))
    canvas.alpha_composite(wash)

    # Header.
    draw.text((150, 64), "CASE II | EMOPAIRCOMPETE WEARABLE BIOSIGNALS", font=fnt(30, bold=True), fill=COLORS["green"])
    title = "Subject-Normalized Stress-State Discovery from Wearable Biosignals"
    draw.text((150, 116), title, font=fnt(87, bold=True, title=True), fill=COLORS["ink"])
    subtitle = "A baseline-aware representation study using HR, TEMP, and EDA features"
    draw.text((154, 238), subtitle, font=fnt(39), fill=COLORS["muted"])

    draw.rounded_rectangle((150, 350, 5610, 495), radius=42, fill=COLORS["blue"])
    draw.rounded_rectangle((150, 350, 720, 495), radius=42, fill=COLORS["green"])
    draw.text((205, 390), "KEY TAKEAWAY", font=fnt(35, bold=True, title=True), fill="#FFF8EC")
    takeaway = "Weak but nonzero stress signal: individual baselines dominate raw PCA, so preprocessing and LOSO validation are essential."
    draw.text((785, 388), takeaway, font=fnt(40, bold=True), fill="#FFF8EC")

    # Layout cards.
    left_x, left_w = 150, 1450
    center_x, center_w = 1690, 2500
    right_x, right_w = 4280, 1330
    top_y = 590
    problem_h = 875
    pipe_y = 1545
    pipe_h = 1515
    main_h = 2470

    problem_box = (left_x, top_y, left_x + left_w, top_y + problem_h)
    pipe_box = (left_x, pipe_y, left_x + left_w, pipe_y + pipe_h)
    key_box = (center_x, top_y, center_x + center_w, top_y + main_h)
    interp_box = (right_x, top_y, right_x + right_w, top_y + main_h)

    for box in [problem_box, pipe_box, key_box, interp_box]:
        shadow_box(canvas, box, radius=44, fill=COLORS["card"], outline="#E5D9C8")
    draw = ImageDraw.Draw(canvas)

    # Problem & Data.
    x, y, w = left_x, top_y, left_w
    draw_section_header(draw, x + 58, y + 52, "Problem & Data", COLORS["blue"], "What is being tested")
    stat_y = y + 190
    stat_w = 408
    for i, (value, label, color) in enumerate(
        [
            (str(n_rows), "observations", COLORS["blue"]),
            (str(n_people), "individuals", COLORS["green"]),
            (str(n_features), "features", COLORS["orange"]),
        ]
    ):
        sx = x + 58 + i * (stat_w + 38)
        draw.rounded_rectangle((sx, stat_y, sx + stat_w, stat_y + 150), radius=30, fill="#FFFFFF", outline="#EADFCC", width=3)
        draw.text((sx + 28, stat_y + 22), value, font=fnt(58, bold=True, serif=True), fill=color)
        draw.text((sx + 31, stat_y + 91), label.upper(), font=fnt(25, bold=True), fill=COLORS["muted"])

    biosignal_y = stat_y + 188
    for i, (label, color) in enumerate([("HR", COLORS["blue"]), ("TEMP", COLORS["green"]), ("EDA", COLORS["orange"])]):
        px = x + 58 + i * 210
        draw.rounded_rectangle((px, biosignal_y, px + 168, biosignal_y + 72), radius=22, fill=color)
        draw.text((px + 42, biosignal_y + 17), label, font=fnt(33, bold=True, title=True), fill="#FFFFFF")
    draw.text((x + 710, biosignal_y + 17), "wearable biosignals", font=fnt(34, bold=True), fill=COLORS["ink"])

    problem_items = [
        "EmoPairCompete dataset with repeated rest, competition, and recovery phases.",
        "Question: do low-dimensional biosignal features capture phase, or mostly who was measured?",
        "Balanced phase design: 104 observations per phase.",
    ]
    draw_bullets(draw, x + 68, biosignal_y + 112, w - 136, problem_items, fnt(33), bullet_color=COLORS["blue"], gap=20)
    draw_phase_timeline(draw, x + 58, y + 710, w - 116)

    # Pipeline.
    x, y, w = left_x, pipe_y, left_w
    draw_section_header(draw, x + 58, y + 50, "Pipeline", COLORS["green"], "Preprocess, represent, validate")
    draw_pipeline(draw, x + 76, y + 185, w - 152)

    # Key results.
    x, y, w = center_x, top_y, center_w
    draw_section_header(draw, x + 58, y + 52, "Key Results", COLORS["orange"], "Signal is weak and baseline-dependent")
    metric_y = y + 188
    metric_gap = 28
    metric_w = (w - 116 - metric_gap * 3) // 4
    metrics = [
        ("Raw phase R2", pct(phase_r2_raw), "PC1-PC5", COLORS["blue"]),
        ("Subject z phase R2", pct(phase_r2_subject), "improved", COLORS["green"]),
        ("KMeans ARI", f"{ari_subject:.3f}", "subject z", COLORS["orange"]),
        ("LOSO AUC", f"{auc_loso:.3f}", "phase2 vs phase1", COLORS["blue"]),
    ]
    for i, (label, value, note, color) in enumerate(metrics):
        mx = x + 58 + i * (metric_w + metric_gap)
        draw_metric_card(canvas, draw, (mx, metric_y, mx + metric_w, metric_y + 170), label, value, note, color)
    draw = ImageDraw.Draw(canvas)

    figure_panel(
        canvas,
        draw,
        (x + 58, y + 395, x + w - 58, y + 1355),
        fig1,
        "Figure 1. Raw PCA is visibly cohort/individual dominated; subject z-score reduces baseline shifts but phases still overlap.",
        COLORS["blue"],
    )
    figure_panel(
        canvas,
        draw,
        (x + 58, y + 1430, x + 1198, y + 2230),
        fig2,
        f"Figure 2. Metadata R2 on PC1-PC5: raw individual {pct(individual_r2_raw)}, cohort {pct(cohort_r2_raw)}, phase {pct(phase_r2_raw)}.",
        COLORS["green"],
        caption_size=25,
    )
    figure_panel(
        canvas,
        draw,
        (x + 1276, y + 1430, x + w - 58, y + 2230),
        fig3,
        "Figure 3. KMeans clusters after subject normalization are phase mixtures, not clean phase-pure states.",
        COLORS["orange"],
        caption_size=25,
    )
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((x + 58, y + 2284, x + w - 58, y + 2412), radius=32, fill=COLORS["pale_orange"], outline="#E7C8AA", width=3)
    draw.text((x + 95, y + 2318), "Result summary:", font=fnt(35, bold=True), fill=COLORS["orange"])
    draw.text((x + 365, y + 2318), "PCA + KMeans does not recover clean phase clusters; supervision confirms only weak nonzero signal.", font=fnt(35), fill=COLORS["ink"])

    # Interpretation.
    x, y, w = right_x, top_y, right_w
    draw_section_header(draw, x + 58, y + 52, "Interpretation", COLORS["green"], "How to read the negative result")
    figure_panel(
        canvas,
        draw,
        (x + 58, y + 178, x + w - 58, y + 1118),
        fig4,
        "Figure 4. LOSO logistic regression reaches AUC about 0.779, so the data are not uninformative.",
        COLORS["blue"],
        caption_size=25,
    )
    draw = ImageDraw.Draw(canvas)
    interp_items = [
        "Wearable biosignals contain weak but nonzero stress-related signal.",
        "Individual baselines dominate raw representations.",
        "Subject-wise normalization is necessary before interpretation.",
        "PCA + KMeans should not be overclaimed as discovering clean emotional states.",
        "Subject-level validation is essential for wearable biosignal claims.",
    ]
    draw_bullets(draw, x + 78, y + 1188, w - 144, interp_items, fnt(35), bullet_color=COLORS["green"], gap=26)

    draw.rounded_rectangle((x + 58, y + 2185, x + w - 58, y + 2408), radius=40, fill=COLORS["green"])
    draw.text((x + 102, y + 2225), "Main conclusion", font=fnt(38, bold=True, title=True), fill="#FFF8EC")
    conclusion = "Baseline-aware preprocessing and subject-level validation are essential before interpreting wearable biosignals as invariant stress states."
    draw_wrapped(draw, (x + 102, y + 2282), conclusion, fnt(35, bold=True), "#FFF8EC", w - 200, line_gap=5)

    # Footer.
    footer = "Sources: submission/case2_report.tex, submission/video_poster_script.md, tables/analysis_summary.json, and local figures."
    draw.text((160, 3130), footer, font=fnt(26), fill=COLORS["muted"])
    draw.text((4680, 3130), "Generated locally - no raw data uploaded", font=fnt(26, bold=True), fill=COLORS["green"])

    rgb = canvas.convert("RGB")
    rgb.save(OUT_PNG, "PNG", dpi=(DPI, DPI), optimize=True)

    try:
        from reportlab.lib.units import inch
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas as pdf_canvas

        page_w, page_h = 19.2 * inch, 10.8 * inch
        c = pdf_canvas.Canvas(str(OUT_PDF), pagesize=(page_w, page_h))
        c.drawImage(ImageReader(str(OUT_PNG)), 0, 0, width=page_w, height=page_h, preserveAspectRatio=False, mask="auto")
        c.showPage()
        c.save()
    except Exception:
        rgb.save(OUT_PDF, "PDF", resolution=DPI)

    print(f"Wrote {OUT_PNG}")
    print(f"Wrote {OUT_PDF}")


if __name__ == "__main__":
    build()
