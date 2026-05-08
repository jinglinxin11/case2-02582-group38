from pathlib import Path
import subprocess
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from mutagen.mp4 import MP4
from imageio_ffmpeg import get_ffmpeg_exe, write_frames


POSTER = Path(r"C:\Users\jingl\Downloads\ChatGPT Image 2026年5月7日 22_18_11.png")
AUDIO_DIR = Path(r"C:\Users\jingl\Documents\xwechat_files\wxid_cnaw19bhwxir12_4322\msg\file\2026-05")
OUT_DIR = Path(r"C:\Users\jingl\Desktop\data\case2\submission\video")
OUT_DIR.mkdir(parents=True, exist_ok=True)

FPS = 20
OUT_SIZE = (1920, 1080)
SPEED = 1.12

CONCAT_LIST = OUT_DIR / "audio_concat_list_static.txt"
CONCAT_AUDIO = OUT_DIR / "narration_static_concat_original.m4a"
FAST_AUDIO = OUT_DIR / "narration_static_1p12x.m4a"
SILENT_VIDEO = OUT_DIR / "case2_video_poster_static_subtitled_silent.mp4"
FINAL_VIDEO = OUT_DIR / "case2_video_poster_static_subtitled_1p12x.mp4"
SRT_PATH = OUT_DIR / "case2_video_poster_static_subtitled_1p12x.srt"
PLAN_PATH = OUT_DIR / "segment_plan_static_subtitled.txt"


SEGMENTS = [
    {
        "audio": "1.m4a",
        "label": "Opening and title",
        "crop": (0.50, 0.10, 0.98),
        "text": (
            "This video poster presents our Case 2 analysis on the EmoPairCompete wearable biosignal dataset. "
            "The central question is whether heart rate, temperature, and electrodermal activity can reveal "
            "subject-normalized stress-state structure."
        ),
    },
    {
        "audio": "2.m4a",
        "label": "Research question",
        "crop": (0.50, 0.22, 0.98),
        "text": (
            "Our research question is: after removing subject baselines, do HR, TEMP, and EDA features contain "
            "generalizable stress-phase structure, and how strongly do they relate to affect ratings? "
            "The key point is that we do not assume stress states are directly visible in the raw signals."
        ),
    },
    {
        "audio": "3.m4a",
        "label": "Data",
        "crop": (0.33, 0.29, 0.64),
        "text": (
            "The dataset contains 312 observations from 26 individuals. Each participant completed pre-rest, "
            "puzzle, and post-rest phases. We use 51 physiological features from HR, TEMP, and EDA, together "
            "with 11 affect variables for interpretation and CCA."
        ),
    },
    {
        "audio": "4.m4a",
        "label": "Pipeline and model checks",
        "crop": (0.67, 0.30, 0.72),
        "text": (
            "Our pipeline is baseline-aware. We first apply median imputation, then subject-wise z-score normalization. "
            "After that, we use PCA and KMeans to inspect latent structure, CCA to study physiology-affect coupling, "
            "and embedding comparisons to test whether non-linear methods improve separation."
        ),
    },
    {
        "audio": "5.m4a",
        "label": "PCA: scatter plots and metrics",
        "crop": (0.50, 0.47, 0.98),
        "text": (
            "The first major result is from PCA. In the raw standardized representation, the data are strongly affected "
            "by individual and cohort baselines. The raw phase R-squared is only 0.030, while the raw individual "
            "R-squared is 0.645. This means participant identity explains much more low-dimensional variance than "
            "the experimental phase."
        ),
    },
    {
        "audio": "6.m4a",
        "label": "PCA diagnostics and interpretation",
        "crop": (0.50, 0.56, 0.98),
        "text": (
            "Subject normalization improves the interpretation, but it does not create clean unsupervised stress-state "
            "clusters. KMeans reaches an adjusted Rand index of only 0.075 after subject z-score normalization. "
            "Therefore, PCA is useful as a diagnostic tool, but not as proof of clean stress-state discovery."
        ),
    },
    {
        "audio": "7.m4a",
        "label": "CCA: loadings and metrics",
        "crop": (0.50, 0.69, 0.98),
        "text": (
            "The second major result is from CCA. The in-sample canonical correlation is 0.477, while the held-out-subject "
            "GroupKFold correlation is 0.362. The subject-block permutation test gives p equals 0.005. This supports "
            "a moderate but meaningful cross-modal relationship between physiology and affect ratings."
        ),
    },
    {
        "audio": "8.m4a",
        "label": "CCA interpretation",
        "crop": (0.60, 0.69, 0.78),
        "text": (
            "The physiological side is mainly driven by EDA-phasic variables. On the affect side, the strongest loadings "
            "include active, alert, attentive, frustrated, and determined. We therefore interpret this as an arousal-like "
            "axis, rather than a simple positive-versus-negative emotion axis."
        ),
    },
    {
        "audio": "9.m4a",
        "label": "PCA versus UMAP versus t-SNE",
        "crop": (0.50, 0.83, 0.98),
        "text": (
            "We also compare PCA, UMAP, and t-SNE for puzzle-versus-rest separation. UMAP gives slightly higher kNN "
            "accuracy, but its silhouette score is lower than PCA. Overall, the non-linear embeddings do not clearly "
            "improve the phase geometry over interpretable PCA."
        ),
    },
    {
        "audio": "10.m4a",
        "label": "Key takeaways and conclusion",
        "crop": (0.50, 0.92, 0.98),
        "text": (
            "The main takeaways are: individual and cohort baselines dominate raw wearable features; EDA-phasic activity "
            "is the strongest cross-modal signal carrier; CCA supports moderate arousal-like physiology-affect coupling; "
            "and there is no robust unsupervised separation of emotional states. In conclusion, baseline-aware preprocessing "
            "and subject-level validation are essential before interpreting wearable biosignals as invariant stress states."
        ),
    },
]


def font(size, bold=False):
    base = Path("C:/Windows/Fonts")
    names = ["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]
    for name in names:
        path = base / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


F_SUB = font(36, True)
F_SUB_SMALL = font(31, True)


def duration(path):
    return float(MP4(path).info.length)


def make_audio():
    CONCAT_LIST.write_text(
        "\n".join(f"file '{(AUDIO_DIR / seg['audio']).as_posix()}'" for seg in SEGMENTS),
        encoding="utf-8",
    )
    ffmpeg = get_ffmpeg_exe()
    subprocess.run(
        [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(CONCAT_LIST), "-c", "copy", str(CONCAT_AUDIO)],
        check=True,
    )
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(CONCAT_AUDIO),
            "-filter:a",
            f"atempo={SPEED}",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            str(FAST_AUDIO),
        ],
        check=True,
    )


def normalized_crop(cx, cy, width_frac, img_w, img_h):
    norm_ratio = (OUT_SIZE[0] / OUT_SIZE[1]) / (img_w / img_h)
    w = max(0.25, min(width_frac, 1.0))
    h = w / norm_ratio
    if h > 1.0:
        h = 1.0
        w = h * norm_ratio
    x0 = max(0.0, min(cx - w / 2, 1.0 - w))
    y0 = max(0.0, min(cy - h / 2, 1.0 - h))
    return (int(x0 * img_w), int(y0 * img_h), int((x0 + w) * img_w), int((y0 + h) * img_h))


def wrap_subtitle(text, max_chars=54):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) <= 2:
        return lines
    # Keep captions readable by allowing a smaller font for occasional 3-line subtitles.
    return lines[:3]


def split_text(text, max_chars=86):
    sentence_parts = []
    for piece in text.replace("? ", "?|").replace(". ", ".|").replace("; ", ";|").split("|"):
        piece = piece.strip()
        if not piece:
            continue
        if len(piece) <= max_chars:
            sentence_parts.append(piece)
        else:
            words = piece.split()
            current = ""
            for word in words:
                candidate = f"{current} {word}".strip()
                if len(candidate) <= max_chars:
                    current = candidate
                else:
                    if current:
                        sentence_parts.append(current)
                    current = word
            if current:
                sentence_parts.append(current)
    return sentence_parts


def make_caption_timeline(segment_durations):
    captions = []
    t = 0.0
    for seg, seg_dur in zip(SEGMENTS, segment_durations):
        chunks = split_text(seg["text"])
        weights = [max(1, len(chunk.split())) for chunk in chunks]
        total = sum(weights)
        seg_start = t
        local = 0.0
        for i, (chunk, weight) in enumerate(zip(chunks, weights)):
            dur = seg_dur * weight / total
            start = seg_start + local
            end = seg_start + local + dur
            if i < len(chunks) - 1:
                end -= 0.05
            captions.append({"start": start, "end": end, "text": chunk})
            local += dur
        t += seg_dur
    return captions


def srt_time(seconds):
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(captions):
    entries = []
    for i, cap in enumerate(captions, start=1):
        lines = textwrap.wrap(cap["text"], width=58)
        entries.append(f"{i}\n{srt_time(cap['start'])} --> {srt_time(cap['end'])}\n" + "\n".join(lines))
    SRT_PATH.write_text("\n\n".join(entries) + "\n", encoding="utf-8")


def frame_for_segment(poster, seg):
    box = normalized_crop(*seg["crop"], poster.width, poster.height)
    return poster.crop(box).resize(OUT_SIZE, Image.Resampling.LANCZOS).convert("RGB")


def draw_subtitle(frame, text):
    img = frame.convert("RGBA")
    layer = Image.new("RGBA", OUT_SIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lines = wrap_subtitle(text)
    font_obj = F_SUB if len(lines) <= 2 else F_SUB_SMALL
    line_h = int(font_obj.size * 1.25)
    box_h = line_h * len(lines) + 42
    box = (120, OUT_SIZE[1] - box_h - 40, OUT_SIZE[0] - 120, OUT_SIZE[1] - 40)
    d.rounded_rectangle(box, radius=24, fill=(5, 23, 38, 205), outline=(255, 255, 255, 95), width=2)
    y = box[1] + 22
    for line in lines:
        tw = d.textlength(line, font=font_obj)
        d.text(((OUT_SIZE[0] - tw) / 2, y), line, font=font_obj, fill=(255, 255, 255, 255))
        y += line_h
    img.alpha_composite(layer)
    return img.convert("RGB")


def make_video(segment_durations, captions):
    poster = Image.open(POSTER).convert("RGB")
    frames_by_segment = [frame_for_segment(poster, seg) for seg in SEGMENTS]
    caption_idx = 0

    writer = write_frames(
        str(SILENT_VIDEO),
        OUT_SIZE,
        fps=FPS,
        codec="libx264",
        quality=8,
        macro_block_size=1,
        output_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    )
    writer.send(None)
    try:
        global_t = 0.0
        for seg_i, seg_dur in enumerate(segment_durations):
            base_frame = frames_by_segment[seg_i]
            frame_count = max(1, int(round(seg_dur * FPS)))
            for local_i in range(frame_count):
                t = global_t + local_i / FPS
                while caption_idx + 1 < len(captions) and captions[caption_idx]["end"] <= t:
                    caption_idx += 1
                cap = captions[caption_idx]
                frame = base_frame
                if cap["start"] <= t <= cap["end"]:
                    frame = draw_subtitle(frame, cap["text"])
                writer.send(np.asarray(frame))
            global_t += seg_dur
    finally:
        writer.close()


def mux_audio_video():
    ffmpeg = get_ffmpeg_exe()
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(SILENT_VIDEO),
            "-i",
            str(FAST_AUDIO),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            str(FINAL_VIDEO),
        ],
        check=True,
    )


def main():
    if not POSTER.exists():
        raise FileNotFoundError(POSTER)
    for seg in SEGMENTS:
        path = AUDIO_DIR / seg["audio"]
        if not path.exists():
            raise FileNotFoundError(path)

    original = [duration(AUDIO_DIR / seg["audio"]) for seg in SEGMENTS]
    segment_durations = [d / SPEED for d in original]
    captions = make_caption_timeline(segment_durations)
    write_srt(captions)
    make_audio()
    make_video(segment_durations, captions)
    mux_audio_video()

    plan = []
    for i, (seg, orig, dur) in enumerate(zip(SEGMENTS, original, segment_durations), start=1):
        plan.append(f"{i:02d}. {seg['audio']} | {seg['label']} | original {orig:.2f}s | video {dur:.2f}s")
    plan.append(f"Final video duration: {sum(segment_durations):.2f}s")
    plan.append(f"Subtitles: {SRT_PATH}")
    plan.append(f"Output: {FINAL_VIDEO}")
    PLAN_PATH.write_text("\n".join(plan), encoding="utf-8")

    print(FINAL_VIDEO)
    print(SRT_PATH)
    print(PLAN_PATH)


if __name__ == "__main__":
    main()
