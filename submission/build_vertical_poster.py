from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont


OUT_DIR = Path(__file__).resolve().parent
FIG_DIR = OUT_DIR / "figures"
PNG_PATH = OUT_DIR / "case2_vertical_poster.png"
PDF_PATH = OUT_DIR / "case2_vertical_poster.pdf"

W, H = 2160, 3840

COL = {
    "cream": "#F6F0E6",
    "paper": "#FFFDF8",
    "ink": "#102238",
    "muted": "#5F6F80",
    "navy": "#14344C",
    "navy2": "#0F2B40",
    "blue": "#2C6EAA",
    "teal": "#247D7F",
    "sage": "#4B8B78",
    "rust": "#C75C46",
    "amber": "#E2A33A",
    "line": "#D8E2E6",
    "soft_blue": "#EAF3F8",
    "soft_teal": "#EAF5F2",
    "soft_rust": "#F8E7DE",
}


def hex_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def blend(a, b, t):
    ar, ag, ab = hex_rgb(a)
    br, bg, bb = hex_rgb(b)
    return (
        int(ar + (br - ar) * t),
        int(ag + (bg - ag) * t),
        int(ab + (bb - ab) * t),
    )


def fnt(size, bold=False, display=False):
    base = Path("C:/Windows/Fonts")
    if display:
        names = ["bahnschrift.ttf", "segoeuib.ttf", "arialbd.ttf"]
    elif bold:
        names = ["segoeuib.ttf", "arialbd.ttf"]
    else:
        names = ["segoeui.ttf", "arial.ttf"]
    for name in names:
        path = base / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


F = {
    "kicker": fnt(24, True),
    "title": fnt(82, True, True),
    "title2": fnt(66, True, True),
    "subtitle": fnt(28),
    "section": fnt(36, True, True),
    "section_small": fnt(28, True, True),
    "body": fnt(27),
    "body_bold": fnt(27, True),
    "small": fnt(22),
    "small_bold": fnt(22, True),
    "tiny": fnt(18),
    "metric": fnt(54, True, True),
    "metric_small": fnt(42, True, True),
    "footer": fnt(20),
}


def shadow(base, box, radius=28, alpha=42, blur=20, offset=(8, 12)):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    shifted = (box[0] + offset[0], box[1] + offset[1], box[2] + offset[0], box[3] + offset[1])
    d.rounded_rectangle(shifted, radius=radius, fill=(12, 30, 45, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(layer)


def rounded(draw, box, radius, fill, outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text(draw, xy, s, font, fill=COL["ink"], anchor=None):
    draw.text(xy, s, font=font, fill=fill, anchor=anchor)


def wrap(draw, x, y, s, font, max_w, fill=COL["ink"], leading=1.12, bullet=False):
    words = s.split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_w:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    line_h = int(font.size * leading)
    for i, line in enumerate(lines):
        if bullet and i == 0:
            rounded(draw, (x, y + 9, x + 10, y + 19), 5, fill)
            draw.text((x + 24, y), line, font=font, fill=fill)
        else:
            indent = 24 if bullet else 0
            draw.text((x + indent, y), line, font=font, fill=fill)
        y += line_h
    return y


def card(base, box, radius=26, fill=COL["paper"], outline=COL["line"], accent=None):
    shadow(base, box, radius=radius)
    d = ImageDraw.Draw(base)
    rounded(d, box, radius, fill, outline, 2)
    if accent:
        d.rounded_rectangle((box[0], box[1], box[0] + 12, box[3]), radius=radius, fill=accent)


def panel_header(draw, x, y, w, title, color, num=None):
    rounded(draw, (x, y, x + w, y + 68), 24, color)
    if num:
        rounded(draw, (x + 22, y + 15, x + 70, y + 53), 14, "#FFFFFF")
        text(draw, (x + 46, y + 22), num, F["section_small"], color, anchor="ma")
        text(draw, (x + 88, y + 18), title, F["section"], "white")
    else:
        text(draw, (x + 32, y + 18), title, F["section"], "white")


def paste_fig(base, path, box, bg="#FFFFFF", radius=22, outline="#EEF2F5"):
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
    d = ImageDraw.Draw(base)
    rounded(d, box, radius, None, outline, 1)


def metric_card(draw, box, value, label, color, fill="#F8FBFC"):
    rounded(draw, box, 22, fill, "#C9D8E1", 2)
    text(draw, ((box[0] + box[2]) // 2, box[1] + 28), value, F["metric"], color, anchor="ma")
    wrap(draw, box[0] + 24, box[1] + 92, label, F["small_bold"], box[2] - box[0] - 48, COL["muted"], 1.02)


def small_metric(draw, x, y, value, label, color):
    rounded(draw, (x, y, x + 240, y + 106), 20, "#FFFFFF", "#D7E3E8", 2)
    text(draw, (x + 24, y + 20), value, F["metric_small"], color)
    text(draw, (x + 24, y + 70), label, F["tiny"], COL["muted"])


def simple_table(draw, x, y):
    headers = ["Method", "Sil.", "kNN acc."]
    rows = [["PCA", "0.107", "0.737"], ["UMAP", "0.069", "0.769"], ["t-SNE", "0.058", "0.763"]]
    widths = [220, 150, 185]
    row_h = 52
    total = sum(widths)
    rounded(draw, (x, y, x + total, y + row_h * 4), 16, "#FFFFFF", "#CDD9DF", 2)
    draw.rounded_rectangle((x, y, x + total, y + row_h), radius=16, fill=COL["navy"])
    cx = x
    for i, h in enumerate(headers):
        text(draw, (cx + 18, y + 14), h, F["small_bold"], "white")
        cx += widths[i]
    for r_i, row in enumerate(rows):
        ry = y + row_h * (r_i + 1)
        if r_i % 2 == 0:
            draw.rectangle((x, ry, x + total, ry + row_h), fill="#F2F5F7")
        cx = x
        for c_i, cell in enumerate(row):
            text(draw, (cx + 18, ry + 14), cell, F["small"], COL["ink"])
            cx += widths[c_i]


def draw_background(base):
    draw = ImageDraw.Draw(base)
    for y in range(H):
        t = y / H
        col = blend("#F8F1E7", "#F1E8DB", t)
        draw.line((0, y, W, y), fill=col)
    for i in range(-80, W, 116):
        draw.line((i, 0, i + 620, H), fill=(228, 220, 204), width=1)
    for j in range(0, H, 116):
        draw.line((0, j, W, j), fill=(231, 224, 211), width=1)

    blob = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(blob)
    bd.ellipse((-500, 150, 620, 1180), fill=(83, 157, 147, 48))
    bd.ellipse((1430, 210, 2620, 1300), fill=(78, 139, 190, 38))
    bd.ellipse((1300, 2820, 2650, 4100), fill=(204, 92, 70, 34))
    blob = blob.filter(ImageFilter.GaussianBlur(10))
    base.alpha_composite(blob)


def draw_wave(draw, x0, y0, w, h):
    pts = []
    for i in range(0, w, 18):
        x = x0 + i
        y = y0 + h / 2 + math.sin(i / 44) * h * 0.18 + math.sin(i / 17) * h * 0.08
        pts.append((x, y))
    draw.line(pts, fill="#9DD2CB", width=4)
    for i, (x, y) in enumerate(pts[::4]):
        color = COL["amber"] if i % 3 == 0 else "#B8D8E8"
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=color)


def build():
    base = Image.new("RGBA", (W, H), COL["cream"])
    draw_background(base)
    draw = ImageDraw.Draw(base)

    # Header.
    draw.rounded_rectangle((0, 0, W, 430), radius=0, fill=COL["navy"])
    draw.rectangle((0, 0, W, 430), fill=COL["navy"])
    draw.polygon([(0, 430), (W, 430), (W, 340), (0, 410)], fill=COL["navy2"])
    draw_wave(draw, 1150, 92, 840, 125)

    text(draw, (90, 50), "CASE II | EMOPAIRCOMPETE WEARABLE BIOSIGNALS", F["kicker"], "#A9D3CE")
    text(draw, (90, 100), "Subject-Normalized", F["title"], "white")
    text(draw, (90, 188), "Stress-State Discovery", F["title"], "white")
    text(draw, (93, 294), "A baseline-aware representation study using HR, TEMP, and EDA features", F["subtitle"], "#DCEAF2")
    rounded(draw, (1548, 42, 2048, 104), 24, "#264B63", "#5E8295", 2)
    text(draw, (1798, 58), "02582 | Case 2 | s252646", F["small_bold"], "white", anchor="ma")
    rounded(draw, (1425, 250, 2048, 365), 26, "#1E5B52", "#6C9F96", 2)
    text(draw, (1465, 272), "Key claim", F["small_bold"], COL["amber"])
    wrap(draw, 1465, 306, "Baseline removal and subject-level validation are essential before interpreting wearable biosignals as stress states.", F["small_bold"], 535, "white", 1.04)

    # Research question.
    card(base, (90, 465, W - 90, 585), radius=24, fill="#EAF3F8", outline="#93BBCB", accent=COL["blue"])
    draw = ImageDraw.Draw(base)
    text(draw, (135, 497), "Research question", F["section_small"], COL["blue"])
    wrap(
        draw,
        465,
        492,
        "After removing subject baselines, do HR/TEMP/EDA features contain generalizable stress-phase structure, and how strongly do they relate to affect ratings?",
        F["body_bold"],
        1530,
        COL["ink"],
        1.08,
    )

    # Overview cards.
    y0 = 625
    cards = {
        "data": (90, y0, 690, 990),
        "pipeline": (735, y0, 1425, 990),
        "valid": (1470, y0, W - 90, 990),
    }
    for box, accent in [(cards["data"], COL["teal"]), (cards["pipeline"], COL["blue"]), (cards["valid"], COL["rust"])]:
        card(base, box, radius=28, accent=accent)
    draw = ImageDraw.Draw(base)

    text(draw, (130, y0 + 34), "Data", F["section"], COL["teal"])
    small_metric(draw, 130, y0 + 95, "312", "observations", COL["blue"])
    small_metric(draw, 380, y0 + 95, "26", "individuals", COL["sage"])
    text(draw, (130, y0 + 235), "Phase design", F["small_bold"], COL["ink"])
    phase_y = y0 + 277
    for i, (label, col, fill) in enumerate(
        [
            ("Pre-rest", COL["blue"], "#EAF3F8"),
            ("Puzzle", COL["rust"], "#F8E7DE"),
            ("Post-rest", COL["sage"], "#EAF5F2"),
        ]
    ):
        x = 130 + i * 170
        rounded(draw, (x, phase_y, x + 150, phase_y + 48), 16, fill, col, 2)
        text(draw, (x + 75, phase_y + 13), label, F["tiny"], col, anchor="ma")
    wrap(draw, 130, y0 + 318, "51 HR/TEMP/EDA features plus 11 affect variables.", F["small"], 500, COL["muted"], 1.05)

    text(draw, (775, y0 + 34), "Pipeline", F["section"], COL["blue"])
    steps = [
        ("01", "Median imputation"),
        ("02", "Subject z-score"),
        ("03", "PCA + KMeans"),
        ("04", "CCA + embeddings"),
    ]
    for i, (num, label) in enumerate(steps):
        yy = y0 + 100 + i * 63
        rounded(draw, (780, yy, 846, yy + 44), 15, COL["navy"], None)
        text(draw, (813, yy + 11), num, F["tiny"], "white", anchor="ma")
        text(draw, (865, yy + 8), label, F["small_bold"], COL["ink"])
        if i < len(steps) - 1:
            draw.line((813, yy + 46, 813, yy + 61), fill="#C7D6DD", width=3)
    text(draw, (1510, y0 + 34), "Model Checks", F["section"], COL["rust"])
    small_metric(draw, 1510, y0 + 95, "0.075", "KMeans ARI", COL["rust"])
    small_metric(draw, 1760, y0 + 95, "0.779", "LOSO AUC", COL["blue"])
    wrap(draw, 1510, y0 + 240, "Unsupervised structure is weak, but a supervised subject-held-out sanity check confirms nonzero stress-related signal.", F["body"], 505, COL["ink"], 1.08)

    # PCA panel.
    pca_box = (90, 1045, W - 90, 1990)
    card(base, pca_box, radius=30, accent=COL["blue"])
    draw = ImageDraw.Draw(base)
    panel_header(draw, 90, 1045, W - 180, "PCA: Baselines Dominate Low-Dimensional Structure", COL["blue"], "1")
    paste_fig(base, FIG_DIR / "figure1_pca_comparison.png", (150, 1155, 1360, 1655), radius=24)
    paste_fig(base, FIG_DIR / "figure2_metadata_r2.png", (150, 1705, 685, 1985), radius=20)
    paste_fig(base, FIG_DIR / "figure3_cluster_phase_heatmap.png", (735, 1705, 1058, 1985), radius=20)
    draw = ImageDraw.Draw(base)
    metric_card(draw, (1450, 1155, 2010, 1288), "0.030", "Raw phase R2 in PC1-PC5", COL["rust"], "#FFF7F1")
    metric_card(draw, (1450, 1322, 2010, 1455), "0.645", "Raw individual R2 in PC1-PC5", COL["sage"], "#F2FAF7")
    metric_card(draw, (1450, 1489, 2010, 1622), "0.075", "Best KMeans ARI after subject z-score", COL["blue"], "#F5FAFD")
    y = 1685
    for b in [
        "Subject and cohort effects dominate raw PCA; phase explains little variance.",
        "Subject normalization improves phase signal, but KMeans still gives mixed phase clusters.",
        "Conclusion: use PCA as a diagnostic representation, not as proof of clean stress-state discovery.",
    ]:
        y = wrap(draw, 1115, y, b, F["small_bold"], 880, COL["ink"], bullet=True, leading=1.08)

    # CCA panel.
    cca_box = (90, 2045, W - 90, 2790)
    card(base, cca_box, radius=30, accent=COL["sage"])
    draw = ImageDraw.Draw(base)
    panel_header(draw, 90, 2045, W - 180, "CCA: Cross-Modal Physiology-Affect Coupling", COL["sage"], "2")
    paste_fig(base, FIG_DIR / "figure5_cca_loadings.png", (150, 2150, 1500, 2762), radius=24)
    metric_card(draw, (1570, 2150, 2010, 2282), "0.477", "In-sample canonical correlation", COL["sage"], "#F2FAF7")
    metric_card(draw, (1570, 2320, 2010, 2452), "0.362", "Held-out-subject GroupKFold r", COL["blue"], "#F5FAFD")
    metric_card(draw, (1570, 2490, 2010, 2622), "p=0.005", "Subject-block permutation test", COL["rust"], "#FFF7F1")
    wrap(draw, 1570, 2662, "EDA-phasic variables are strongest; affective loadings form an arousal-like axis.", F["body_bold"], 420, COL["ink"], 1.08)

    # Embedding panel.
    emb_box = (90, 2845, W - 90, 3338)
    card(base, emb_box, radius=30, accent=COL["rust"])
    draw = ImageDraw.Draw(base)
    panel_header(draw, 90, 2845, W - 180, "PCA vs UMAP vs t-SNE: Non-linear Comparison", COL["rust"], "3")
    paste_fig(base, FIG_DIR / "figure6_embedding_comparison.png", (150, 2948, 1415, 3310), radius=24)
    simple_table(draw, 1486, 2958)
    wrap(
        draw,
        1486,
        3172,
        "UMAP has slightly higher kNN accuracy, but lower silhouette. Non-linear embeddings do not clearly improve phase geometry over interpretable PCA.",
        F["body_bold"],
        520,
        COL["ink"],
        1.08,
    )

    # Takeaways.
    take_box = (90, 3348, W - 90, 3745)
    shadow(base, take_box, radius=34, alpha=54, blur=24)
    draw = ImageDraw.Draw(base)
    rounded(draw, take_box, 34, COL["navy"], None)
    text(draw, (140, 3402), "Key Take-aways", F["section"], COL["amber"])
    takeaways = [
        ("1", "Individual/cohort baselines dominate raw wearable features."),
        ("2", "EDA-phasic activity is the strongest cross-modal signal carrier."),
        ("3", "CCA supports moderate arousal-like physiology-affect coupling."),
        ("4", "No robust unsupervised separation of emotional states."),
    ]
    for i, (num, body) in enumerate(takeaways):
        tx = 140 + (i % 2) * 960
        ty = 3480 + (i // 2) * 108
        rounded(draw, (tx, ty, tx + 860, ty + 78), 20, "#234B63", "#5E8295", 2)
        text(draw, (tx + 30, ty + 20), f"{num}.", F["body_bold"], COL["amber"])
        wrap(draw, tx + 82, ty + 17, body, F["small_bold"], 720, "white", 1.0)

    text(draw, (W // 2, 3800), "Generated locally from reproducible scripts in submission/; no raw data uploaded.", F["footer"], COL["muted"], anchor="ma")

    rgb = base.convert("RGB")
    rgb.save(PNG_PATH, quality=96)
    rgb.save(PDF_PATH, "PDF", resolution=180)
    print(PNG_PATH)
    print(PDF_PATH)


if __name__ == "__main__":
    build()
