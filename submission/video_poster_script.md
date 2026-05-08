# Case 2 Video Poster Script

Target length: 3 to 4 minutes.

Suggested title:
Can wearable biosignals reveal subject-invariant stress states?

## Poster Layout

Use one landscape poster or 4 slide-style panels:

1. Problem and data
2. Pipeline
3. Results
4. Interpretation and limitations

Recommended figures:

- `figures/figure1_pca_comparison.png`
- `figures/figure2_metadata_r2.png`
- `figures/figure3_cluster_phase_heatmap.png`
- `figures/figure4_supervised_sanity_roc.png`

## Speaker 1: Aim and Data

Hi, this project investigates whether wearable biosignals can reveal latent emotional or stress-related states in the EmoPairCompete dataset.

The experiment has three phases repeated over four rounds: phase1 is pre-puzzle rest, phase2 is the puzzle competition, and phase3 is post-puzzle rest. We used the updated `HR_data_2.csv` file. It contains 312 observations from 26 individuals and 51 physiological features extracted from heart rate, temperature, and electrodermal activity.

Our main research question is whether a low-dimensional representation of these biosignals captures the experimental phase, or whether it is mostly driven by individual baselines and cohort effects.

## Speaker 2: Method

Our pipeline has three preprocessing variants. First, we used raw standardized features. Second, we used subject-wise z-score normalization, which removes each participant's personal baseline. Third, we subtracted the phase1 value within each individual and round, so phase2 and phase3 are represented as deviations from resting baseline.

We then applied PCA to obtain a low-dimensional representation. To interpret what the PCs capture, we measured how much of the first five PC scores can be explained by phase, individual, cohort, and puzzler role. Finally, we used KMeans clustering with `k=3` on the first five PCs and compared the clusters to the known phases using ARI, NMI, silhouette score, and a cluster-by-phase heatmap.

We also ran two sanity checks: a one-class SVM trained only on phase1 resting data, and a supervised leave-one-subject-out logistic regression classifier for phase2 versus phase1.

## Speaker 3: Results

The main result is that raw biosignal features are dominated by subject and cohort effects. In the raw PCA representation, the first five PCs explain about 58 percent of feature variance, but individual identity explains about 65 percent of the PC1-PC5 representation and cohort explains about 33 percent. Experimental phase explains only about 3 percent.

After subject-wise normalization, the phase-related structure improves: phase explains about 10 percent of the first five PCs. However, the PCA scatter plot still shows strong overlap between pre-rest, puzzle, and post-rest phases.

KMeans clustering confirms this. For raw features, ARI with phase labels is approximately zero. With subject normalization, ARI increases to about 0.075, but this is still weak. The cluster heatmap shows that clusters are mixtures of all three phases rather than clean latent emotional states.

The one-class SVM also performs poorly, with phase2-versus-phase1 AUC around 0.40. However, the supervised LOSO logistic regression sanity check reaches AUC around 0.779, so the dataset is not completely uninformative. The stress signal exists, but it is weak and not the dominant source of variance.

## Speaker 4: Interpretation and Conclusion

Our conclusion is that simple unsupervised latent state discovery is not reliable on this feature set. The physiological signals are heavily baseline-dependent, and raw PCA mostly captures who was measured and which cohort they came from, not the emotional state.

The most important methodological point is that subject-wise normalization is necessary before interpreting wearable biosignals. Even after normalization, the phase signal remains weak, so it would be misleading to claim that PCA plus KMeans discovers clean emotional states.

This is still a useful result. It shows that a rigorous pipeline can diagnose when a null or weak result is caused by noisy real-world biosignals rather than by a modeling failure. Future work should use temporal features, self-supervised representations, or models explicitly designed for subject-level generalization.

## Short Closing Sentence

Overall, we found weak but nonzero stress-related signal, but no robust unsupervised separation of emotional states. The case highlights why baseline-aware preprocessing and subject-level validation are essential for wearable biosignal analysis.

## Recording Checklist

- Keep the video between 2 and 5 minutes.
- Make sure each group member presents one part.
- Show the figures while speaking, especially the PCA plot, metadata R2 bar chart, and cluster heatmap.
- Do not overclaim the result. The strongest conclusion is methodological: the signal is weak and baseline-dependent.
- Mention that code and report are reproducible from `submission/case2_analysis.py`.
