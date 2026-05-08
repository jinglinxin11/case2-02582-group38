from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


OUT_DIR = Path(__file__).resolve().parent
FIG_DIR = OUT_DIR / "figures"
PNG_PATH = OUT_DIR / "case2_reference_grade_poster.png"
PDF_PATH = OUT_DIR / "case2_reference_grade_poster.pdf"

W, H = 3840, 2160

PALETTE = {
    "bg": "#F4F0E8",
    "paper": "#FFFCF6",
    "ink": "#122033",
    "muted": "#637284",
    "slate": "#17344C",
    "slate2": "#244B63",
    "sage": "#4E8B7A",
    "teal": "#287B84",
    "blue": "#2F6FAD",
    "rust": "#C95D49",
    "amber": "#D8982F",
    "line": "#D5E0E5",
    "pale_blue": "#EAF3F8",
    "pale_sage": "#EAF4EF",
    "pale_amber": "#FFF3DD",
}


def font(size, bold=False):
    base = Path("C:/Windows/Fonts")
    names = ["arialbd.ttf" if bold else "arial.ttf", "segoeuib.ttf" if bold else "segoeui.ttf"]
    for name in names:
        path = base / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


F = {
    "title": font(72, True),
    "subtitle": font(31, False),
    "objective": font(35, True),
    "panel": font(31, True),
    "body": font(25, False),
    "body_bold": font(25, True),
    "small": font(21, False),
    "small_bold": font(21, True),
    "metric": font(42, True),
    "take": font(34, True),
    "footer": font(18, False),
}


def shadow(base, box, radius=28, alpha=55, offset=(8, 12), blur=20):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    shifted = (box[0] + offset[0], box[1] + offset[1], box[2] + offset[0], box[3] + offset[1])
    d.rounded_rectangle(shifted, radius=radius, fill=(18, 32, 51, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(layer)


def rounded(draw, box, radius, fill, outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def txt(draw, xy, s, fnt, fill=PALETTE["ink"], anchor=None):
    draw.text(xy, s, font=fnt, fill=fill, anchor=anchor)


def wrap_text(draw, x, y, s, fnt, max_w, fill=PALETTE["ink"], leading=1.15, bullet=False):
    words = s.split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=fnt) <= max_w:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    lh = int(fnt.size * leading)
    for i, line in enumerate(lines):
        indent = 24 if bullet and i else 0
        prefix = "- " if bullet and i == 0 else ""
        draw.text((x + indent, y), prefix + line, font=fnt, fill=fill)
        y += lh
    return y


def header_bar(draw, box, label, color):
    rounded(draw, box, 12, color, None)
    txt(draw, ((box[0] + box[2]) // 2, box[1] + 16), label, F["panel"], "white", anchor="ma")


def panel(base, box, label, color):
    shadow(base, box, radius=34)
    d = ImageDraw.Draw(base)
    rounded(d, box, 34, PALETTE["paper"], PALETTE["line"], 3)
    header_bar(d, (box[0], box[1], box[2], box[1] + 64), label, color)


def paste_fig(base, path, box, bg="#FFFFFF", radius=18):
    img = Image.open(path).convert("RGBA")
    tw, th = box[2] - box[0], box[3] - box[1]
    scale = min(tw / img.width, th / img.height)
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    layer = Image.new("RGBA", (tw, th), bg)
    layer.alpha_composite(img, ((tw - img.width) // 2, (th - img.height) // 2))
    mask = Image.new("L", (tw, th), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, tw, th), radius=radius, fill=255)
    base.paste(layer, (box[0], box[1]), mask)


def metric_box(draw, box, value, label, color):
    rounded(draw, box, 20, "#F7FAFB", "#C9D9E1", 2)
    txt(draw, ((box[0] + box[2]) // 2, box[1] + 28), value, F["metric"], color, anchor="ma")
    wrap_text(draw, box[0] + 22, box[1] + 82, label, F["small_bold"], box[2] - box[0] - 44, PALETTE["muted"], leading=1.05)


def table(draw, x, y, headers, rows, col_w, row_h=46, header_color=PALETTE["slate"]):
    total_w = sum(col_w)
    rounded(draw, (x, y, x + total_w, y + row_h * (len(rows) + 1)), 12, "#FFFFFF", "#CDD9DF", 2)
    draw.rounded_rectangle((x, y, x + total_w, y + row_h), radius=12, fill=header_color)
    cx = x
    for i, h in enumerate(headers):
        txt(draw, (cx + 14, y + 13), h, F["small_bold"], "white")
        cx += col_w[i]
    for r_i, row in enumerate(rows):
        ry = y + row_h * (r_i + 1)
        if r_i % 2 == 0:
            draw.rectangle((x, ry, x + total_w, ry + row_h), fill="#F6F8FA")
        cx = x
        for c_i, cell in enumerate(row):
            txt(draw, (cx + 14, ry + 13), str(cell), F["small"], PALETTE["ink"])
            cx += col_w[c_i]
    cx = x
    for w in col_w[:-1]:
        cx += w
        draw.line((cx, y, cx, y + row_h * (len(rows) + 1)), fill="#DDE5EA", width=2)


def build():
    base = Image.new("RGBA", (W, H), PALETTE["bg"])
    draw = ImageDraw.Draw(base)

    # Quiet grid and soft scientific backdrop.
    for i in range(0, W, 120):
        draw.line((i, 0, i, H), fill="#E7E0D4", width=1)
    for j in range(0, H, 120):
        draw.line((0, j, W, j), fill="#E7E0D4", width=1)
    draw.ellipse((-620, -420, 900, 1030), fill="#DCEEEB")
    draw.ellipse((2800, -320, 4380, 1020), fill="#E3ECF5")
    draw.ellipse((2550, 1570, 4300, 2700), fill="#F1D9C9")

    # Header.
    draw.rectangle((0, 0, W, 210), fill=PALETTE["slate"])
    txt(draw, (W // 2, 38), "Subject-Normalized Stress-State Discovery from Wearable Biosignals", F["title"], "white", anchor="ma")
    txt(draw, (W // 2, 130), "02582 Computational Data Analysis  |  Case 2  |  s252646", F["subtitle"], "#DCEAF2", anchor="ma")

    rounded(draw, (110, 242, W - 110, 326), 16, PALETTE["pale_blue"], "#8DB8C8", 3)
    txt(
        draw,
        (W // 2, 262),
        "Research question: After removing subject baselines, do HR/TEMP/EDA features contain generalizable stress-phase structure, and how strongly do they relate to affect ratings?",
        F["objective"],
        PALETTE["slate"],
        anchor="ma",
    )

    # Main top panels.
    top_y = 370
    left = (70, top_y, 930, 1470)
    mid = (980, top_y, 2380, 1470)
    right = (2430, top_y, 3770, 1470)
    panel(base, left, "1. Data and Preprocessing", PALETTE["teal"])
    panel(base, mid, "2. PCA: Baselines Dominate", PALETTE["blue"])
    panel(base, right, "3. CCA: Physiology-Affect Coupling", PALETTE["sage"])

    # Section 1.
    x, y = left[0] + 48, left[1] + 105
    pipeline = [
        ("EmoPairCompete", "26 participants"),
        ("Preprocess", "median impute"),
        ("Subject z-score", "baseline-aware"),
        ("PCA + KMeans", "latent states"),
        ("CCA", "cross-modal"),
        ("UMAP + t-SNE", "non-linear check"),
    ]
    for i, (a, b) in enumerate(pipeline):
        by = y + i * 110
        rounded(draw, (x + 45, by, left[2] - 70, by + 70), 16, "#F4F7FA", "#D2DCE4", 2)
        txt(draw, (x + 75, by + 12), a, F["small_bold"], PALETTE["ink"])
        txt(draw, (x + 75, by + 39), b, F["footer"], PALETTE["muted"])
        if i < len(pipeline) - 1:
            draw.line((left[0] + 430, by + 72, left[0] + 430, by + 104), fill=PALETTE["teal"], width=3)
            draw.polygon([(left[0] + 430, by + 108), (left[0] + 420, by + 94), (left[0] + 440, by + 94)], fill=PALETTE["teal"])
    y = left[1] + 790
    bullets = [
        "Data: 312 samples = 26 individuals x 4 rounds x 3 phases.",
        "Inputs: 51 HR/TEMP/EDA features; 11 self-report variables used for CCA/evaluation.",
        "Validation: GroupKFold split by individual; no sample-level leakage.",
        "Goal: discover representations, not maximize a supervised classifier.",
    ]
    for b in bullets:
        y = wrap_text(draw, x, y, b, F["body"], 760, bullet=True, leading=1.08)
        y += 12

    # Section 2.
    paste_fig(base, FIG_DIR / "figure1_pca_comparison.png", (1025, 470, 2335, 810))
    paste_fig(base, FIG_DIR / "figure2_metadata_r2.png", (1025, 862, 1700, 1255))
    paste_fig(base, FIG_DIR / "figure3_cluster_phase_heatmap.png", (1740, 862, 2335, 1255))
    y = 1280
    for b in [
        "Raw PC1-PC5 variance is mostly individual identity (R2=0.645) and cohort (R2=0.328).",
        "Experimental phase explains only R2=0.030 in raw PCA, increasing to R2=0.099 after subject normalization.",
        "KMeans does not recover clean latent phases: best ARI=0.075 after subject normalization.",
    ]:
        y = wrap_text(draw, 1025, y, b, F["small"], 1280, bullet=True, leading=1.08)
        y += 7

    # Section 3.
    paste_fig(base, FIG_DIR / "figure5_cca_loadings.png", (2475, 470, 3725, 920))
    metric_box(draw, (2495, 965, 2848, 1115), "0.477", "In-sample canonical correlation", PALETTE["sage"])
    metric_box(draw, (2885, 965, 3265, 1115), "0.362", "GroupKFold r across held-out subjects", PALETTE["blue"])
    metric_box(draw, (3302, 965, 3705, 1115), "p=0.005", "Subject-block permutation test", PALETTE["rust"])
    y = 1160
    for b in [
        "CCA links physiological variation to self-reported affect, but the held-out-subject estimate is moderate.",
        "Top physiological contributors are mainly EDA phasic features, especially peaks, median, AUC, and skewness.",
        "The affective axis loads on active, alert, attentive, frustrated, and determined: more arousal-like than pure valence.",
    ]:
        y = wrap_text(draw, 2495, y, b, F["small"], 1170, bullet=True, leading=1.08)
        y += 10

    # Bottom panel.
    bottom = (70, 1518, 3770, 2020)
    panel(base, bottom, "4. PCA vs UMAP vs t-SNE: Non-linear Comparison", PALETTE["rust"])
    paste_fig(base, FIG_DIR / "figure6_embedding_comparison.png", (125, 1608, 2340, 1908))
    table(
        draw,
        2405,
        1615,
        ["Method", "Silhouette", "kNN acc."],
        [["PCA", "0.107", "0.737"], ["UMAP", "0.069", "0.769"], ["t-SNE", "0.058", "0.763"]],
        [220, 210, 190],
        row_h=52,
        header_color=PALETTE["slate2"],
    )
    y = 1830
    wrap_text(
        draw,
        2405,
        y,
        "Non-linear embeddings do not clearly improve phase geometry. UMAP gives slightly higher kNN accuracy, but lower silhouette; t-SNE is visually mixed. PCA remains the most interpretable representation.",
        F["body"],
        1280,
        leading=1.08,
    )

    # Key takeaways.
    draw.rectangle((0, 2050, W, 2160), fill=PALETTE["slate"])
    txt(draw, (120, 2077), "Key Take-aways", F["take"], "#F6C25B")
    takeaways = [
        "Individual/cohort baselines dominate raw wearable features.",
        "EDA-phasic activity is the strongest cross-modal signal carrier.",
        "CCA finds moderate arousal-like physiology-affect coupling.",
        "No robust unsupervised separation of emotional states.",
    ]
    start_x = 620
    card_w = 710
    for i, t in enumerate(takeaways):
        bx = start_x + i * (card_w + 44)
        rounded(draw, (bx, 2066, bx + card_w, 2138), 18, "#25475F", "#42677B", 2)
        txt(draw, (bx + 22, 2083), f"{i + 1}.", F["small_bold"], "#F6C25B")
        wrap_text(draw, bx + 62, 2076, t, F["small_bold"], card_w - 82, "white", leading=1.0)
    txt(draw, (W - 120, 2142), "Generated from reproducible scripts in submission/.", F["footer"], "#D8E6ED", anchor="ra")

    base.convert("RGB").save(PNG_PATH, quality=96)
    base.convert("RGB").save(PDF_PATH, "PDF", resolution=180)
    print(PNG_PATH)
    print(PDF_PATH)


if __name__ == "__main__":
    build()
