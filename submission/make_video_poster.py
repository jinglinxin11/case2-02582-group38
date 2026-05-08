from pathlib import Path
import subprocess

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

SILENT_VIDEO = OUT_DIR / "case2_video_poster_silent.mp4"
CONCAT_LIST = OUT_DIR / "audio_concat_list.txt"
CONCAT_AUDIO = OUT_DIR / "narration_concat_original.m4a"
FAST_AUDIO = OUT_DIR / "narration_1p12x.m4a"
FINAL_VIDEO = OUT_DIR / "case2_video_poster_final_1p12x.mp4"
SEGMENT_PLAN = OUT_DIR / "segment_plan.txt"


SEGMENTS = [
    {
        "audio": "1.m4a",
        "label": "Opening and title",
        "start": None,
        "end": (0.50, 0.12, 0.98),
    },
    {
        "audio": "2.m4a",
        "label": "Research question",
        "start": (0.50, 0.19, 0.98),
        "end": (0.50, 0.24, 0.90),
    },
    {
        "audio": "3.m4a",
        "label": "Data panel",
        "start": (0.34, 0.27, 0.66),
        "end": (0.25, 0.27, 0.58),
    },
    {
        "audio": "4.m4a",
        "label": "Pipeline and model checks",
        "start": (0.67, 0.27, 0.72),
        "end": (0.73, 0.27, 0.64),
    },
    {
        "audio": "5.m4a",
        "label": "PCA scatter plots and metrics",
        "start": (0.50, 0.45, 0.98),
        "end": (0.43, 0.43, 0.72),
    },
    {
        "audio": "6.m4a",
        "label": "PCA diagnostics and interpretation",
        "start": (0.50, 0.55, 0.98),
        "end": (0.62, 0.54, 0.72),
    },
    {
        "audio": "7.m4a",
        "label": "CCA loadings and metrics",
        "start": (0.50, 0.69, 0.98),
        "end": (0.46, 0.68, 0.72),
    },
    {
        "audio": "8.m4a",
        "label": "CCA interpretation",
        "start": (0.62, 0.69, 0.82),
        "end": (0.73, 0.69, 0.56),
    },
    {
        "audio": "9.m4a",
        "label": "PCA versus UMAP versus t-SNE",
        "start": (0.50, 0.84, 0.98),
        "end": (0.50, 0.83, 0.82),
    },
    {
        "audio": "10.m4a",
        "label": "Key takeaways and conclusion",
        "start": (0.50, 0.91, 0.98),
        "end": (0.50, 0.92, 0.88),
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


F_LABEL = font(34, True)
F_SMALL = font(22, False)


def audio_duration(path):
    return float(MP4(path).info.length)


def make_audio():
    lines = []
    for segment in SEGMENTS:
        path = AUDIO_DIR / segment["audio"]
        lines.append(f"file '{path.as_posix()}'")
    CONCAT_LIST.write_text("\n".join(lines), encoding="utf-8")

    ffmpeg = get_ffmpeg_exe()
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(CONCAT_LIST),
            "-c",
            "copy",
            str(CONCAT_AUDIO),
        ],
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


def clamp_crop(cx, cy, width_frac, img_w, img_h):
    # Output is 16:9. In normalized poster coordinates, dx/dy = (16/9)/(img_w/img_h).
    norm_ratio = (OUT_SIZE[0] / OUT_SIZE[1]) / (img_w / img_h)
    w = max(0.25, min(width_frac, 1.0))
    h = w / norm_ratio
    if h > 1.0:
        h = 1.0
        w = h * norm_ratio
    x0 = cx - w / 2
    y0 = cy - h / 2
    x0 = max(0.0, min(x0, 1.0 - w))
    y0 = max(0.0, min(y0, 1.0 - h))
    return (int(x0 * img_w), int(y0 * img_h), int((x0 + w) * img_w), int((y0 + h) * img_h))


def ease(t):
    return 0.5 - 0.5 * np.cos(np.pi * t)


def lerp(a, b, t):
    return a + (b - a) * t


def full_frame(poster):
    w, h = OUT_SIZE
    bg = poster.resize((w, int(w * poster.height / poster.width)), Image.Resampling.LANCZOS)
    if bg.height < h:
        bg = poster.resize((int(h * poster.width / poster.height), h), Image.Resampling.LANCZOS)
    left = (bg.width - w) // 2
    top = (bg.height - h) // 2
    bg = bg.crop((left, top, left + w, top + h)).filter(ImageFilter.GaussianBlur(22))
    overlay = Image.new("RGBA", OUT_SIZE, (8, 28, 45, 120))
    bg = bg.convert("RGBA")
    bg.alpha_composite(overlay)

    target_h = h - 72
    target_w = int(target_h * poster.width / poster.height)
    if target_w > w - 110:
        target_w = w - 110
        target_h = int(target_w * poster.height / poster.width)
    resized = poster.resize((target_w, target_h), Image.Resampling.LANCZOS).convert("RGBA")
    x = (w - target_w) // 2
    y = (h - target_h) // 2

    shadow = Image.new("RGBA", OUT_SIZE, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((x + 14, y + 14, x + target_w + 14, y + target_h + 14), radius=18, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    bg.alpha_composite(shadow)
    bg.alpha_composite(resized, (x, y))
    return bg.convert("RGB")


def crop_frame(poster, box):
    crop = poster.crop(box)
    frame = crop.resize(OUT_SIZE, Image.Resampling.LANCZOS).convert("RGB")
    return frame


def draw_segment_label(frame, label, idx, total):
    img = frame.convert("RGBA")
    overlay = Image.new("RGBA", OUT_SIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    text = f"{idx}/{total}  {label}"
    tw = int(d.textlength(text, font=F_LABEL))
    box = (38, 38, 76 + tw, 96)
    d.rounded_rectangle(box, radius=18, fill=(8, 30, 48, 180), outline=(160, 210, 220, 160), width=2)
    d.text((58, 52), text, font=F_LABEL, fill=(255, 255, 255, 255))
    img.alpha_composite(overlay)
    return img.convert("RGB")


def segment_frame(poster, segment, frame_index, frame_count, idx):
    if segment["start"] is None:
        # Hold the full poster briefly, then move into the title area.
        if frame_index < frame_count * 0.38:
            frame = full_frame(poster)
            return draw_segment_label(frame, segment["label"], idx, len(SEGMENTS))
        local_t = (frame_index - frame_count * 0.38) / max(1, frame_count * 0.62)
        local_t = float(max(0.0, min(1.0, local_t)))
        start = (0.50, 0.50, 1.0)
        end = segment["end"]
    else:
        start = segment["start"]
        end = segment["end"]
        local_t = frame_index / max(1, frame_count - 1)

    t = ease(float(local_t))
    cx = lerp(start[0], end[0], t)
    cy = lerp(start[1], end[1], t)
    width = lerp(start[2], end[2], t)
    # A tiny breathing zoom makes static sections feel less abrupt.
    width *= 1.0 - 0.012 * np.sin(np.pi * local_t)
    box = clamp_crop(cx, cy, width, poster.width, poster.height)
    frame = crop_frame(poster, box)
    return draw_segment_label(frame, segment["label"], idx, len(SEGMENTS))


def make_video():
    poster = Image.open(POSTER).convert("RGB")
    durations = []
    plan_lines = []
    for idx, segment in enumerate(SEGMENTS, start=1):
        src = AUDIO_DIR / segment["audio"]
        original = audio_duration(src)
        duration = original / SPEED
        durations.append(duration)
        plan_lines.append(f"{idx:02d}. {segment['audio']} | {segment['label']} | original {original:.2f}s | video {duration:.2f}s")
    plan_lines.append(f"Total original audio: {sum(d * SPEED for d in durations):.2f}s")
    plan_lines.append(f"Final sped-up video/audio: {sum(durations):.2f}s")
    SEGMENT_PLAN.write_text("\n".join(plan_lines), encoding="utf-8")

    writer = write_frames(
        str(SILENT_VIDEO),
        OUT_SIZE,
        fps=FPS,
        codec="libx264",
        quality=8,
        output_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    )
    writer.send(None)
    try:
        for idx, (segment, duration) in enumerate(zip(SEGMENTS, durations), start=1):
            frame_count = max(1, int(round(duration * FPS)))
            for frame_index in range(frame_count):
                frame = segment_frame(poster, segment, frame_index, frame_count, idx)
                writer.send(np.asarray(frame))
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
    for segment in SEGMENTS:
        src = AUDIO_DIR / segment["audio"]
        if not src.exists():
            raise FileNotFoundError(src)
    if not POSTER.exists():
        raise FileNotFoundError(POSTER)

    make_audio()
    make_video()
    mux_audio_video()
    print(FINAL_VIDEO)
    print(SEGMENT_PLAN)


if __name__ == "__main__":
    main()
