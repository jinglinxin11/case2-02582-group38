# 02582 Computational Data Analysis - Case 2

This repository contains the final Case 2 submission materials for the EmoPairCompete wearable biosignal dataset.

## Contents

- `submission/case2_report.pdf`: final written report.
- `submission/case2_poster.png`: final poster image used for the presentation.
- `submission/case2_analysis.py`: core reproducible analysis script for the report and poster figures.
- `submission/figures/`: figures used in the report and final poster.
- `submission/tables/`: numerical result summaries used in the report and final poster.

## Data

The raw dataset is not included in this repository because the course data are governed by licensing restrictions.
To reproduce the analysis, place the provided `HR_data_2.zip` file in the repository root.

## Reproduce Analysis

Install the Python dependencies if needed:

```powershell
pip install -r requirements.txt
```

Run from the repository root:

```powershell
python .\submission\case2_analysis.py
```

This regenerates `figure1`-`figure6` and the corresponding result tables used by the report and poster.

