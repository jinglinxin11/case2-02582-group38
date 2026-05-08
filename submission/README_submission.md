# Case 2 Submission Files

This folder contains the final Case 2 submission results, excluding raw data and temporary generation files.

## Files to Use

- `case2_report.pdf`: final 7-page report PDF for submission.
- `case2_poster.png`: final poster image used for the presentation.
- `case2_analysis.py`: core reproducible analysis script that reads `../HR_data_2.zip`, regenerates report/poster figures and tables, and prints the numerical summary.
- `figures/`: figures used in the report and final poster.
- `tables/`: numerical outputs used in the report and final poster.

## How to Regenerate Analysis Results

Run from the Case 2 directory:

```powershell
python .\submission\case2_analysis.py
```
