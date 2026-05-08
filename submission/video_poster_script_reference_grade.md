# Case 2 Video Script for Reference-Grade Poster

Target length: 3 to 4 minutes.

Poster file:
`case2_reference_grade_poster.pdf`

## Speaker 1: Objective, Data, and Pipeline

Our project asks whether HR, temperature, and EDA features contain a stress-related structure after removing subject baselines, and whether that structure relates to self-reported affect.

We use the EmoPairCompete dataset. The feature file contains 312 observations from 26 individuals, with four rounds and three phases per round. The input physiological features are extracted from heart rate, skin temperature, and electrodermal activity. We also use 11 self-report variables, including frustration and PANAS-style affect items, but only for evaluation and CCA, not as unsupervised clustering inputs.

The pipeline is baseline-aware. We use median imputation, subject-wise z-score normalization, PCA and KMeans for latent state discovery, CCA for physiology-affect coupling, and PCA, UMAP, and t-SNE for a non-linear embedding comparison. Validation is grouped by individual to reduce subject leakage.

## Speaker 2: PCA and Latent State Discovery

The PCA results show why baseline correction is necessary. In the raw physiological representation, the first five PCs are dominated by individual identity and cohort effects. Individual identity explains about 64.5 percent of PC1 to PC5 variance, cohort explains about 32.8 percent, while experimental phase explains only about 3.0 percent.

After subject-wise normalization, phase-related structure increases to about 9.9 percent, but the phases still overlap strongly. This means the signal is weak relative to between-subject variability.

We then tested whether KMeans with three clusters recovers the three experimental phases. It does not. The best ARI is only about 0.075 after subject normalization. Therefore, we should not claim that simple PCA plus KMeans discovers clean emotional states.

## Speaker 3: CCA Cross-Modal Coupling

To test whether the physiological representation aligns with subjective affect, we applied canonical correlation analysis between physiological features and questionnaire variables.

The first canonical axis has an in-sample correlation of 0.477. Under GroupKFold validation across held-out subjects, the correlation is about 0.362 with standard deviation 0.128. A subject-block permutation test gives p approximately 0.005, so this cross-modal association is unlikely to be random.

The physiological side is mainly driven by EDA phasic features, including EDA peaks, median, AUC, skewness, and kurtosis. On the questionnaire side, the strongest loadings are active, alert, attentive, frustrated, and determined. We interpret this as an arousal-like axis rather than a pure positive-versus-negative valence axis.

## Speaker 4: Non-linear Embeddings and Takeaways

We also compared PCA, UMAP, and t-SNE for puzzle-versus-rest separation. UMAP gives slightly higher kNN accuracy, around 0.769, but lower silhouette than PCA. t-SNE is also visually mixed. This suggests that non-linear embeddings do not fundamentally solve the separation problem in this dataset.

The main takeaways are: first, individual and cohort baselines dominate raw wearable features. Second, EDA phasic activity is the strongest cross-modal signal carrier. Third, CCA finds a moderate arousal-like physiology-affect coupling. Finally, there is no robust unsupervised separation of emotional states.

Our conclusion is therefore cautious. The data contain weak but nonzero stress-related and affect-related signal, but claims about latent emotional states require baseline-aware preprocessing and subject-level validation.
