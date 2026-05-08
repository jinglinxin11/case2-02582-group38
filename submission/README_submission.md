# Case 2 Submission Files

This folder contains the prepared Case 2 materials, excluding peer feedback.

## Files to Use

- `case2_report.tex`: full report draft with student ID filled in.
- `case2_report.pdf`: generated 6-page report PDF for review/submission.
- `case2_analysis.py`: reproducible analysis script that reads `../HR_data_2.zip`, regenerates all figures and tables, and prints the numerical summary.
- `case2_video_poster.pdf`: one-page poster PDF to show while recording the video.
- `case2_vertical_poster.pdf`: portrait/vertical poster PDF version.
- `case2_vertical_poster.png`: portrait/vertical poster PNG version.
- `video_poster_script.md`: 3 to 4 minute video/poster script with suggested speaker split.
- `figures/`: figures used in the report and video poster.
- `tables/`: numerical outputs used in the report.

## How to Regenerate Results

Run from the Case 2 directory:

```powershell
python .\submission\case2_analysis.py
```

To regenerate the generated PDFs:

```powershell
python .\submission\build_report_pdf.py
python .\submission\build_poster_pdf.py
```

## What Still Needs Your Input

1. Use `case2_report.pdf` directly, or compile `case2_report.tex` yourself if you prefer the LaTeX version.
2. Record the 2-5 minute video while showing `case2_reference_grade_poster.pdf`, using `video_poster_script_reference_grade.md`.
3. Add a repository link if your teacher expects one.
4. Submit the PDF report and video/poster presentation on Inside.

Peer feedback is intentionally not included here because it must be written after each assigned peer video is unlocked.
