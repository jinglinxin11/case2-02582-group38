from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


OUT_DIR = Path(__file__).resolve().parent
FIG_DIR = OUT_DIR / "figures"
PDF_PATH = OUT_DIR / "case2_report.pdf"


def p(text, style):
    return Paragraph(text, style)


def img(path, width_cm):
    image = Image(str(path))
    ratio = image.imageHeight / image.imageWidth
    image.drawWidth = width_cm * cm
    image.drawHeight = width_cm * cm * ratio
    return image


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build():
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        rightMargin=2.1 * cm,
        leftMargin=2.1 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleCenter",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=21,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Subtitle",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            fontSize=10,
            textColor=colors.HexColor("#555555"),
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            spaceBefore=8,
            spaceAfter=5,
            textColor=colors.HexColor("#243B53"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            alignment=TA_JUSTIFY,
            fontSize=9.4,
            leading=12.2,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Caption",
            parent=styles["BodyText"],
            alignment=TA_LEFT,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#444444"),
            spaceBefore=2,
            spaceAfter=7,
        )
    )

    story = []

    story.append(p("Case 2: Low-Dimensional Representation and Latent State Discovery in Wearable Biosignals", styles["TitleCenter"]))
    story.append(p("02582 Computational Data Analysis<br/>s252646", styles["Subtitle"]))
    story.append(p("Abstract", styles["Heading"]))
    story.append(
        p(
            "This report investigates whether physiological features from the EmoPairCompete dataset reveal "
            "subject-invariant emotional or stress-related states. We use the provided heart rate, skin "
            "temperature, and electrodermal activity features and evaluate three preprocessing choices: global "
            "standardization, subject-wise normalization, and subtraction of the pre-puzzle resting baseline. "
            "PCA is used to derive low-dimensional representations, and KMeans clustering tests whether latent "
            "clusters align with the three experimental phases. The main finding is a negative but informative "
            "result: the raw representation is dominated by individual and cohort effects, while phase explains "
            "only a small part of the variance. Subject-wise normalization increases phase-related structure, "
            "but unsupervised clustering still does not reliably recover the experimental phases.",
            styles["Body"],
        )
    )
    story.append(p("Research Questions", styles["Heading"]))
    story.append(
        p(
            "We ask whether the dominant directions of variation in the biosignal features are related to "
            "experimental phase or mainly driven by individual and cohort effects; whether subject-wise "
            "normalization or baseline subtraction improves the phase-related structure; and whether unsupervised "
            "clusters in a low-dimensional space correspond to pre-puzzle rest, puzzle task, and post-puzzle rest.",
            styles["Body"],
        )
    )
    story.append(p("Data", styles["Heading"]))
    story.append(
        p(
            "We used the updated feature file HR_data_2.csv. It contains 312 observations, corresponding to 26 "
            "individuals, four rounds, and three phases per round. The input feature set contains 51 physiological "
            "features from HR, TEMP, and EDA. Metadata and questionnaire variables such as Phase, Individual, "
            "Cohort, Puzzler, and Frustrated were not used as model inputs; they were used only for interpretation "
            "and validation. The feature matrix contained only two missing values, which were median-imputed.",
            styles["Body"],
        )
    )
    story.append(PageBreak())

    story.append(p("Method", styles["Heading"]))
    story.append(
        p(
            "Let X be the 312 by 51 physiological feature matrix. We compared three preprocessing pipelines. "
            "Raw scaled features use median imputation followed by global standardization. Subject-wise "
            "normalization centers and scales each feature within each participant, removing static physiological "
            "baselines. Phase1 baseline subtraction represents each observation as a deviation from the corresponding "
            "pre-puzzle resting observation within the same individual and round.",
            styles["Body"],
        )
    )
    story.append(
        p(
            "PCA was used to obtain a low-dimensional representation. The first five principal components were used "
            "for downstream evaluation. To diagnose what drives the representation, we computed a weighted R2 between "
            "the PC1-PC5 scores and four metadata variables: phase, individual, cohort, and puzzler role. KMeans with "
            "k=3 was then applied to PC1-PC5, and cluster agreement with the known phases was measured using adjusted "
            "Rand index, normalized mutual information, silhouette score, and a cluster-by-phase heatmap.",
            styles["Body"],
        )
    )
    story.append(
        p(
            "As sanity checks, we also tested a one-class SVM trained only on phase1 resting data under "
            "leave-one-subject-out validation, and a supervised logistic regression classifier for phase2 versus "
            "phase1 under the same validation design. These checks were not the main unsupervised solution; they "
            "were used to assess whether any generalizable phase signal exists.",
            styles["Body"],
        )
    )
    story.append(p("Results: PCA Structure", styles["Heading"]))
    story.append(
        img(FIG_DIR / "figure1_pca_comparison.png", 16.2)
    )
    story.append(
        p(
            "Figure 1. Left: PCA on raw standardized features, colored by cohort. Right: PCA on subject-normalized "
            "features, colored by phase. Raw features show clear cohort structure, while subject normalization "
            "reduces this baseline effect but does not produce clean phase separation.",
            styles["Caption"],
        )
    )
    story.append(PageBreak())

    story.append(p("Results: What Explains the Representation?", styles["Heading"]))
    story.append(
        p(
            "The raw scaled PCA representation showed that the first five PCs explained 58.4 percent of total feature "
            "variance. However, the dominant structure was not phase-related. Individual identity explained 64.5 "
            "percent of the weighted variance in PC1-PC5, and cohort explained 32.8 percent. Experimental phase "
            "explained only 3.0 percent, and puzzler role explained 0.5 percent.",
            styles["Body"],
        )
    )
    story.append(img(FIG_DIR / "figure2_metadata_r2.png", 14.5))
    story.append(
        p(
            "Figure 2. Weighted R2 of metadata variables for PC1-PC5. Subject normalization removes static individual "
            "and cohort effects and increases the relative contribution of phase, but the phase signal remains weak.",
            styles["Caption"],
        )
    )
    table_data = [
        ["Pipeline", "PC1", "PC2", "PC1-PC5", "Silhouette", "ARI", "NMI"],
        ["Raw scaled", "0.278", "0.100", "0.584", "0.320", "-0.003", "0.004"],
        ["Subject-wise z", "0.203", "0.091", "0.514", "0.162", "0.075", "0.079"],
        ["Phase1 delta", "0.163", "0.097", "0.493", "0.442", "0.051", "0.129"],
    ]
    table = Table(table_data, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243B53")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CCCCCC")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6F8FA")]),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    story.append(p("Table 1. PCA and KMeans summary for the three preprocessing pipelines.", styles["Caption"]))
    story.append(PageBreak())

    story.append(p("Results: Latent State Discovery", styles["Heading"]))
    story.append(
        p(
            "KMeans clustering on the first five PCs did not recover the three phases reliably. For raw scaled "
            "features, the ARI was approximately zero (-0.003), indicating no meaningful agreement with phase labels. "
            "Subject-wise normalization improved ARI to 0.075, and phase1 baseline subtraction gave ARI 0.051. "
            "These values are still low and indicate weak alignment.",
            styles["Body"],
        )
    )
    story.append(img(FIG_DIR / "figure3_cluster_phase_heatmap.png", 10.0))
    story.append(
        p(
            "Figure 3. KMeans clusters from the subject-normalized PCA representation. The clusters contain mixtures "
            "of phases rather than one cluster per experimental phase.",
            styles["Caption"],
        )
    )
    story.append(p("Sanity Checks", styles["Heading"]))
    story.append(
        p(
            "The one-class SVM trained on phase1 resting data did not successfully flag phase2 as anomalous under "
            "leave-one-subject-out validation. With nu=0.10, phase2-versus-phase1 AUC was 0.402 and balanced accuracy "
            "was 0.404. In contrast, the supervised logistic regression sanity check for phase2 versus phase1 achieved "
            "AUC 0.779, balanced accuracy 0.692, and F1 score 0.701. This means the data are not completely "
            "uninformative, but the signal is subtle and not the dominant source of variance.",
            styles["Body"],
        )
    )
    story.append(img(FIG_DIR / "figure4_supervised_sanity_roc.png", 9.5))
    story.append(
        p(
            "Figure 4. Supervised sanity check for phase2 versus phase1 using leave-one-subject-out logistic regression.",
            styles["Caption"],
        )
    )
    story.append(PageBreak())

    story.append(p("Discussion", styles["Heading"]))
    story.append(
        p(
            "The main conclusion is that individual baselines are the dominant source of variation in the raw wearable "
            "biosignal features. This is expected for HR, TEMP, and EDA because absolute levels differ substantially "
            "across people and recording sessions. Without normalization, a latent representation mostly captures who "
            "was measured and when the data were collected, not what experimental state the person was in.",
            styles["Body"],
        )
    )
    story.append(
        p(
            "Subject-wise normalization is therefore not an optional preprocessing detail; it changes the scientific "
            "interpretation of the representation. It removes static individual and cohort effects and increases the "
            "amount of phase-related structure. However, the improvement is limited. The phases still overlap in PCA "
            "space, and KMeans clusters remain mixtures of pre-rest, puzzle, and post-rest observations.",
            styles["Body"],
        )
    )
    story.append(
        p(
            "The supervised sanity check prevents over-interpreting the negative clustering result. If even a supervised "
            "LOSO classifier failed, we might conclude that the feature set contains almost no phase information. "
            "Instead, logistic regression achieved AUC 0.779, suggesting that phase information exists but is subtle "
            "and distributed across features. PCA may fail because the stress signal is not the largest source of "
            "variance, while PCA explicitly prioritizes high-variance directions.",
            styles["Body"],
        )
    )
    story.append(p("Limitations", styles["Heading"]))
    story.append(
        p(
            "The sample size is small, with 26 individuals and only 12 observations per individual. The feature matrix "
            "uses summary statistics over phases and may discard important temporal dynamics. Cohort effects are strong, "
            "and the cohorts were collected at different times and contexts. Self-reported frustration is subjective and "
            "does not necessarily align one-to-one with physiological arousal. Finally, KMeans assumes roughly spherical "
            "clusters and may be poorly matched to biosignal manifolds.",
            styles["Body"],
        )
    )
    story.append(p("Conclusion", styles["Heading"]))
    story.append(
        p(
            "The EmoPairCompete biosignals contain weak but nonzero phase-related information, but the dominant structure "
            "in the raw data is individual and cohort variability. Subject-wise normalization improves the representation, "
            "yet unsupervised PCA plus KMeans does not reliably discover latent states corresponding to pre-puzzle rest, "
            "puzzle stress, and post-puzzle recovery. Wearable biosignal analysis therefore requires baseline-aware "
            "preprocessing and subject-level validation before latent emotional clusters can be interpreted as meaningful "
            "stress states.",
            styles["Body"],
        )
    )
    story.append(PageBreak())

    story.append(p("Reproducibility", styles["Heading"]))
    story.append(
        p(
            "The analysis was implemented in Python using median imputation, standardization, PCA, KMeans, one-class "
            "SVM, logistic regression, and leave-one-subject-out validation. The script submission/case2_analysis.py "
            "reads HR_data_2.zip, generates all figures, and exports the numerical result tables used in this report.",
            styles["Body"],
        )
    )
    story.append(p("GenAI Acknowledgement", styles["Heading"]))
    story.append(
        p(
            "Generative AI was used to help structure the report, draft explanatory text, and organize the computational "
            "pipeline. All reported numerical results were produced by running the accompanying analysis script on the "
            "provided dataset, and the final interpretation was checked against those outputs.",
            styles["Body"],
        )
    )
    story.append(p("References", styles["Heading"]))
    story.append(
        p(
            "[1] Das, S., Lund, N. L., Gonzalez, C. R., Lonfeldt, N. N., and Clemmensen, L. H. EmoPairCompete - "
            "physiological signals dataset for emotion and frustration assessment under team and competitive behaviors. "
            "ICLR Workshop on Learning from Time Series for Health, 2024.",
            styles["Body"],
        )
    )
    story.append(
        p(
            "[2] Thompson, E. R. Development and validation of an internationally reliable short-form of the Positive "
            "and Negative Affect Schedule (PANAS). Journal of Cross-Cultural Psychology, 38(2), 227-242, 2007.",
            styles["Body"],
        )
    )

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)


if __name__ == "__main__":
    build()
    print(PDF_PATH)
