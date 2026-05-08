import json
import os
from pathlib import Path
from zipfile import ZipFile

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import umap
from sklearn.cluster import KMeans
from sklearn.cross_decomposition import CCA
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.manifold import TSNE
from sklearn.metrics import (
    accuracy_score,
    adjusted_rand_score,
    auc,
    balanced_accuracy_score,
    f1_score,
    normalized_mutual_info_score,
    roc_auc_score,
    roc_curve,
    silhouette_score,
)
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM


BASE_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = Path(__file__).resolve().parent
FIG_DIR = OUT_DIR / "figures"
TABLE_DIR = OUT_DIR / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    zip_path = BASE_DIR / "HR_data_2.zip"
    if not zip_path.exists():
        zip_path = BASE_DIR / "data" / "HR_data_2.zip"
    with ZipFile(zip_path) as zipf:
        with zipf.open("HR_data_2.csv") as f:
            df = pd.read_csv(f, index_col=0)

    feature_cols = df.columns[:51].tolist()
    return df, feature_cols


def standardize_frame(x_df):
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    x = imputer.fit_transform(x_df)
    return scaler.fit_transform(x)


def subject_z_frame(df, feature_cols):
    def safe_z(col):
        std = col.std(ddof=0)
        if std == 0 or np.isnan(std):
            return col - col.mean()
        return (col - col.mean()) / std

    return df[feature_cols].groupby(df["Individual"]).transform(safe_z)


def delta_phase1_frame(df, feature_cols):
    phase1 = df[df["Phase"].eq("phase1")].set_index(["Individual", "Round"])[feature_cols]
    rows = []
    for _, row in df.iterrows():
        base = phase1.loc[(row["Individual"], row["Round"])]
        rows.append(row[feature_cols].astype(float) - base.astype(float))
    return pd.DataFrame(rows, index=df.index, columns=feature_cols)


def weighted_label_r2(z, labels):
    # R2 from least-squares prediction of PC scores using one categorical label.
    design = pd.get_dummies(labels, drop_first=False).to_numpy(dtype=float)
    if design.shape[1] > 1:
        design = np.c_[np.ones(len(design)), design[:, 1:]]
    else:
        design = np.ones((len(design), 1))
    pred = design @ np.linalg.pinv(design) @ z
    ss_res = ((z - pred) ** 2).sum(axis=0)
    ss_tot = ((z - z.mean(axis=0)) ** 2).sum(axis=0)
    r2 = 1 - ss_res / np.where(ss_tot == 0, np.nan, ss_tot)
    weights = np.nan_to_num(ss_tot / np.nansum(ss_tot))
    return float(np.nansum(r2 * weights))


def plot_pca_comparison(df, raw_scores, subject_scores):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), dpi=180)

    cohorts = sorted(df["Cohort"].unique())
    cmap = plt.get_cmap("tab10")
    for i, cohort in enumerate(cohorts):
        mask = df["Cohort"].eq(cohort).to_numpy()
        axes[0].scatter(
            raw_scores[mask, 0],
            raw_scores[mask, 1],
            s=22,
            alpha=0.78,
            color=cmap(i % 10),
            label=cohort,
            edgecolor="none",
        )
    axes[0].set_title("Raw standardized features")
    axes[0].set_xlabel("PC1")
    axes[0].set_ylabel("PC2")
    axes[0].legend(frameon=False, fontsize=7, ncol=2)

    phase_colors = {"phase1": "#2F6FAD", "phase2": "#C43C39", "phase3": "#4E9F50"}
    phase_labels = {"phase1": "Pre-puzzle rest", "phase2": "Puzzle task", "phase3": "Post-puzzle rest"}
    for phase in ["phase1", "phase2", "phase3"]:
        mask = df["Phase"].eq(phase).to_numpy()
        axes[1].scatter(
            subject_scores[mask, 0],
            subject_scores[mask, 1],
            s=24,
            alpha=0.78,
            color=phase_colors[phase],
            label=phase_labels[phase],
            edgecolor="none",
        )
    axes[1].set_title("Subject-normalized features")
    axes[1].set_xlabel("PC1")
    axes[1].set_ylabel("PC2")
    axes[1].legend(frameon=False, fontsize=8)

    for ax in axes:
        ax.axhline(0, color="#DDDDDD", lw=0.8)
        ax.axvline(0, color="#DDDDDD", lw=0.8)
        ax.grid(alpha=0.18)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "figure1_pca_comparison.png", bbox_inches="tight")
    plt.close(fig)


def plot_r2_bars(r2_rows):
    r2_df = pd.DataFrame(r2_rows)
    labels = ["Phase", "Individual", "Cohort", "Puzzler"]
    versions = ["raw_scaled", "subject_z", "delta_phase1"]
    colors = ["#B55B45", "#436B95", "#5F8D5A"]
    x = np.arange(len(labels))
    width = 0.24

    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=180)
    for i, version in enumerate(versions):
        vals = [float(r2_df[(r2_df.version == version) & (r2_df.label == label)]["weighted_r2"].iloc[0]) for label in labels]
        ax.bar(x + (i - 1) * width, vals, width, label=version.replace("_", " "), color=colors[i])

    ax.set_ylabel("Weighted R2 on PC1-PC5")
    ax.set_title("Which metadata explain the low-dimensional representation?")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 0.72)
    ax.grid(axis="y", alpha=0.2)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "figure2_metadata_r2.png", bbox_inches="tight")
    plt.close(fig)
    r2_df.to_csv(TABLE_DIR / "metadata_r2.csv", index=False)


def plot_cluster_heatmap(cluster_table):
    phases = ["phase1", "phase2", "phase3"]
    values = cluster_table[phases].to_numpy()
    fig, ax = plt.subplots(figsize=(6, 4.6), dpi=180)
    im = ax.imshow(values, vmin=0, vmax=1, cmap="YlOrRd")
    ax.set_title("KMeans clusters vs experimental phases")
    ax.set_xlabel("Experimental phase")
    ax.set_ylabel("Cluster")
    ax.set_xticks(np.arange(len(phases)))
    ax.set_xticklabels(["Pre-rest", "Puzzle", "Post-rest"])
    ax.set_yticks(np.arange(len(cluster_table.index)))
    ax.set_yticklabels([str(i) for i in cluster_table.index])
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            ax.text(j, i, f"{values[i, j]:.2f}", ha="center", va="center", color="#222222", fontsize=9)
    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.set_label("Within-cluster phase proportion")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "figure3_cluster_phase_heatmap.png", bbox_inches="tight")
    plt.close(fig)
    cluster_table.to_csv(TABLE_DIR / "cluster_phase_table.csv")


def supervised_sanity_check(df, feature_cols):
    # This is not the main method. It checks whether any phase1/phase2 signal exists
    # under leave-one-subject-out generalization.
    d2 = df[df["Phase"].isin(["phase1", "phase2"])].reset_index(drop=True)
    true = []
    pred = []
    prob = []

    for train_idx, test_idx in LeaveOneGroupOut().split(d2, groups=d2["Individual"]):
        x_train_df = d2.loc[train_idx, feature_cols]
        x_test_df = d2.loc[test_idx, feature_cols]
        y_train = d2.loc[train_idx, "Phase"].eq("phase2").astype(int)
        y_test = d2.loc[test_idx, "Phase"].eq("phase2").astype(int)

        imputer = SimpleImputer(strategy="median").fit(x_train_df)
        scaler = StandardScaler().fit(imputer.transform(x_train_df))
        x_train = scaler.transform(imputer.transform(x_train_df))
        x_test = scaler.transform(imputer.transform(x_test_df))

        clf = LogisticRegression(max_iter=2000, C=0.2, class_weight="balanced", solver="liblinear")
        clf.fit(x_train, y_train)
        prob.extend(clf.predict_proba(x_test)[:, 1].tolist())
        pred.extend(clf.predict(x_test).tolist())
        true.extend(y_test.tolist())

    fpr, tpr, _ = roc_curve(true, prob)
    roc_auc = auc(fpr, tpr)

    fig, ax = plt.subplots(figsize=(5.5, 4.6), dpi=180)
    ax.plot(fpr, tpr, color="#1F5A99", lw=2, label=f"LOSO logistic AUC = {roc_auc:.3f}")
    ax.plot([0, 1], [0, 1], "--", color="#999999", lw=1)
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("Supervised sanity check: phase2 vs phase1")
    ax.legend(frameon=False)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "figure4_supervised_sanity_roc.png", bbox_inches="tight")
    plt.close(fig)

    return {
        "auc": float(roc_auc_score(true, prob)),
        "balanced_accuracy": float(balanced_accuracy_score(true, pred)),
        "f1": float(f1_score(true, pred)),
    }


def one_class_svm_loso(df, feature_cols, nu=0.10):
    scores = []
    preds = []
    phases = []

    for train_idx, test_idx in LeaveOneGroupOut().split(df, groups=df["Individual"]):
        train_rest_idx = train_idx[df.iloc[train_idx]["Phase"].eq("phase1").to_numpy()]
        imputer = SimpleImputer(strategy="median").fit(df.iloc[train_rest_idx][feature_cols])
        scaler = StandardScaler().fit(imputer.transform(df.iloc[train_rest_idx][feature_cols]))
        x_train = scaler.transform(imputer.transform(df.iloc[train_rest_idx][feature_cols]))
        x_test = scaler.transform(imputer.transform(df.iloc[test_idx][feature_cols]))

        model = OneClassSVM(kernel="rbf", gamma="scale", nu=nu)
        model.fit(x_train)
        scores.extend((-model.decision_function(x_test)).tolist())
        preds.extend((model.predict(x_test) == -1).astype(int).tolist())
        phases.extend(df.iloc[test_idx]["Phase"].tolist())

    res = pd.DataFrame({"phase": phases, "score": scores, "pred": preds})
    metrics = {}
    for positive_phase in ["phase2", "phase3"]:
        sub = res[res["phase"].isin(["phase1", positive_phase])]
        y = sub["phase"].eq(positive_phase).astype(int).to_numpy()
        metrics[positive_phase] = {
            "auc": float(roc_auc_score(y, sub["score"].to_numpy())),
            "balanced_accuracy": float(balanced_accuracy_score(y, sub["pred"].to_numpy())),
            "phase1_anomaly_rate": float(sub[sub["phase"].eq("phase1")]["pred"].mean()),
            f"{positive_phase}_anomaly_rate": float(sub[sub["phase"].eq(positive_phase)]["pred"].mean()),
        }
    return metrics


def affect_columns():
    return [
        "Frustrated",
        "upset",
        "hostile",
        "alert",
        "ashamed",
        "inspired",
        "nervous",
        "attentive",
        "afraid",
        "active",
        "determined",
    ]


def fit_physiology_affect(df, feature_cols, affect_cols):
    x_df = subject_z_frame(df, feature_cols)
    x = SimpleImputer(strategy="median").fit_transform(x_df)
    x = StandardScaler().fit_transform(x)

    y = SimpleImputer(strategy="median").fit_transform(df[affect_cols])
    y = StandardScaler().fit_transform(y)
    return x, y


def group_knn_accuracy(z, labels, groups, n_neighbors=7):
    preds = []
    true = []
    for train_idx, test_idx in GroupKFold(n_splits=5).split(z, labels, groups):
        clf = KNeighborsClassifier(n_neighbors=n_neighbors)
        clf.fit(z[train_idx], labels[train_idx])
        preds.extend(clf.predict(z[test_idx]).tolist())
        true.extend(labels[test_idx].tolist())
    return float(accuracy_score(true, preds))


def cca_poster_analysis(df, feature_cols, affect_cols, n_permutations=200):
    x, y = fit_physiology_affect(df, feature_cols, affect_cols)
    groups = df["Individual"].to_numpy()

    pca = PCA(n_components=8, random_state=0)
    x_pca = pca.fit_transform(x)
    cca = CCA(n_components=1, max_iter=1000)
    u, v = cca.fit_transform(x_pca, y)
    in_sample_r = float(abs(np.corrcoef(u[:, 0], v[:, 0])[0, 1]))

    cv_rs = []
    for train_idx, test_idx in GroupKFold(n_splits=5).split(x, groups=groups):
        train_df = df.iloc[train_idx]
        test_df = df.iloc[test_idx]

        train_x_df = subject_z_frame(train_df, feature_cols)
        test_x_df = subject_z_frame(test_df, feature_cols)
        imp_x = SimpleImputer(strategy="median").fit(train_x_df)
        sc_x = StandardScaler().fit(imp_x.transform(train_x_df))
        x_train = sc_x.transform(imp_x.transform(train_x_df))
        x_test = sc_x.transform(imp_x.transform(test_x_df))

        imp_y = SimpleImputer(strategy="median").fit(train_df[affect_cols])
        sc_y = StandardScaler().fit(imp_y.transform(train_df[affect_cols]))
        y_train = sc_y.transform(imp_y.transform(train_df[affect_cols]))
        y_test = sc_y.transform(imp_y.transform(test_df[affect_cols]))

        pca_cv = PCA(n_components=8, random_state=0).fit(x_train)
        cca_cv = CCA(n_components=1, max_iter=1000)
        cca_cv.fit(pca_cv.transform(x_train), y_train)
        u_test, v_test = cca_cv.transform(pca_cv.transform(x_test), y_test)
        cv_rs.append(abs(np.corrcoef(u_test[:, 0], v_test[:, 0])[0, 1]))

    rng = np.random.default_rng(0)
    unique_groups = np.unique(groups)
    group_to_indices = {g: np.where(groups == g)[0] for g in unique_groups}
    perm_rs = []
    for _ in range(n_permutations):
        shuffled_groups = rng.permutation(unique_groups)
        y_perm = np.empty_like(y)
        for src_g, dst_g in zip(unique_groups, shuffled_groups):
            y_perm[group_to_indices[src_g]] = y[group_to_indices[dst_g]]
        u_perm, v_perm = CCA(n_components=1, max_iter=1000).fit_transform(x_pca, y_perm)
        perm_rs.append(abs(np.corrcoef(u_perm[:, 0], v_perm[:, 0])[0, 1]))
    p_value = float((np.sum(np.array(perm_rs) >= in_sample_r) + 1) / (n_permutations + 1))

    x_variate = u[:, 0]
    y_variate = v[:, 0]
    x_corr = [np.corrcoef(x[:, col_i], x_variate)[0, 1] for col_i, _ in enumerate(feature_cols)]
    y_corr = [np.corrcoef(y[:, col_i], y_variate)[0, 1] for col_i, _ in enumerate(affect_cols)]

    loading_df = pd.DataFrame({"feature": feature_cols, "corr": x_corr})
    loading_df["group"] = loading_df["feature"].str.extract(r"^(HR|TEMP|EDA)", expand=False).fillna("Other")
    loading_df["abs_corr"] = loading_df["corr"].abs()
    loading_df = loading_df.sort_values("abs_corr", ascending=False)
    affect_df = pd.DataFrame({"affect": affect_cols, "corr": y_corr}).sort_values("corr")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), dpi=180)
    top = loading_df.head(12).iloc[::-1]
    color_map = {"HR": "#2F6FAD", "TEMP": "#D59A2E", "EDA": "#2B8C8C", "Other": "#888888"}
    axes[0].barh(top["feature"], top["corr"], color=[color_map[g] for g in top["group"]])
    axes[0].axvline(0, color="#666666", lw=0.8)
    axes[0].set_title("A. Physiological CCA loadings")
    axes[0].set_xlabel("Correlation with physiological canonical variate")
    axes[0].tick_params(labelsize=7)

    affect_colors = ["#C85A4A" if value > 0 else "#2F6FAD" for value in affect_df["corr"]]
    axes[1].barh(affect_df["affect"], affect_df["corr"], color=affect_colors)
    axes[1].axvline(0, color="#666666", lw=0.8)
    axes[1].set_title("B. Questionnaire CCA loadings")
    axes[1].set_xlabel("Correlation with affective canonical variate")
    axes[1].tick_params(labelsize=8)

    fig.suptitle(
        f"CCA: physiology-affect coupling, in-sample r={in_sample_r:.3f}, "
        f"GroupKFold r={np.mean(cv_rs):.3f} +/- {np.std(cv_rs):.3f}",
        y=1.03,
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / "figure5_cca_loadings.png", bbox_inches="tight")
    plt.close(fig)

    loading_df.to_csv(TABLE_DIR / "cca_physiology_loadings.csv", index=False)
    affect_df.to_csv(TABLE_DIR / "cca_affect_loadings.csv", index=False)

    return {
        "cca_in_sample_abs_r": in_sample_r,
        "cca_groupkfold_abs_r_mean": float(np.mean(cv_rs)),
        "cca_groupkfold_abs_r_sd": float(np.std(cv_rs)),
        "cca_subject_block_permutation_p": p_value,
        "top_physiology_features": loading_df.head(5)[["feature", "corr"]].to_dict(orient="records"),
        "top_affect_features": affect_df.reindex(affect_df["corr"].abs().sort_values(ascending=False).index)
        .head(5)[["affect", "corr"]]
        .to_dict(orient="records"),
    }


def embedding_poster_comparison(df, feature_cols):
    x, _ = fit_physiology_affect(df, feature_cols, affect_columns())
    labels = df["Phase"].eq("phase2").astype(int).to_numpy()
    groups = df["Individual"].to_numpy()

    embeddings = {
        "PCA": PCA(n_components=2, random_state=0).fit_transform(x),
        "UMAP": umap.UMAP(n_components=2, n_neighbors=18, min_dist=0.15, random_state=0).fit_transform(x),
        "t-SNE": TSNE(n_components=2, perplexity=25, init="pca", learning_rate="auto", random_state=0).fit_transform(x),
    }
    metrics = []
    for name, z in embeddings.items():
        metrics.append(
            {
                "method": name,
                "silhouette_puzzle_vs_rest": float(silhouette_score(z, labels)),
                "groupkfold_knn_accuracy": group_knn_accuracy(z, labels, groups),
            }
        )

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), dpi=180)
    colors = np.where(labels == 1, "#C85A4A", "#2F6FAD")
    for ax, (name, z) in zip(axes, embeddings.items()):
        ax.scatter(z[:, 0], z[:, 1], c=colors, s=18, alpha=0.75, edgecolor="none")
        ax.set_title(name)
        ax.set_xlabel("Dim 1")
        ax.set_ylabel("Dim 2")
        ax.grid(alpha=0.18)
    handles = [
        plt.Line2D([0], [0], marker="o", color="w", label="rest", markerfacecolor="#2F6FAD", markersize=7),
        plt.Line2D([0], [0], marker="o", color="w", label="puzzle", markerfacecolor="#C85A4A", markersize=7),
    ]
    axes[-1].legend(handles=handles, frameon=False)
    fig.suptitle("Non-linear embedding comparison: puzzle vs rest")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "figure6_embedding_comparison.png", bbox_inches="tight")
    plt.close(fig)

    pd.DataFrame(metrics).to_csv(TABLE_DIR / "embedding_comparison.csv", index=False)
    return metrics


def main():
    df, feature_cols = load_data()
    y_phase = df["Phase"].map({"phase1": 0, "phase2": 1, "phase3": 2}).to_numpy()

    raw_df = df[feature_cols].copy()
    subject_df = subject_z_frame(df, feature_cols)
    delta_df = delta_phase1_frame(df, feature_cols)
    versions = {
        "raw_scaled": raw_df,
        "subject_z": subject_df,
        "delta_phase1": delta_df,
    }

    summary = {
        "n_rows": int(len(df)),
        "n_individuals": int(df["Individual"].nunique()),
        "n_features": int(len(feature_cols)),
        "feature_missing_total": int(df[feature_cols].isna().sum().sum()),
        "total_missing": int(df.isna().sum().sum()),
        "phase_counts": df["Phase"].value_counts().sort_index().to_dict(),
        "cohort_counts": df["Cohort"].value_counts().sort_index().to_dict(),
        "frustration_counts": df["Frustrated"].value_counts().sort_index().astype(int).to_dict(),
    }

    pca_scores = {}
    r2_rows = []
    model_rows = []
    for name, x_df in versions.items():
        x = standardize_frame(x_df)
        pca = PCA(n_components=8, random_state=0).fit(x)
        scores = pca.transform(x)
        pca_scores[name] = scores
        evr = pca.explained_variance_ratio_

        for label_name, labels in [
            ("Phase", df["Phase"]),
            ("Individual", df["Individual"].astype(str)),
            ("Cohort", df["Cohort"]),
            ("Puzzler", df["Puzzler"].astype(str)),
        ]:
            r2_rows.append(
                {
                    "version": name,
                    "label": label_name,
                    "weighted_r2": weighted_label_r2(scores[:, :5], labels),
                }
            )

        kmeans = KMeans(n_clusters=3, n_init=20, random_state=0)
        clusters = kmeans.fit_predict(scores[:, :5])
        model_rows.append(
            {
                "version": name,
                "pc1_evr": float(evr[0]),
                "pc2_evr": float(evr[1]),
                "pc5_cumulative_evr": float(evr[:5].sum()),
                "kmeans_silhouette": float(silhouette_score(scores[:, :5], clusters)),
                "kmeans_ari_phase": float(adjusted_rand_score(y_phase, clusters)),
                "kmeans_nmi_phase": float(normalized_mutual_info_score(y_phase, clusters)),
            }
        )

        if name == "subject_z":
            cluster_table = pd.crosstab(
                pd.Series(clusters, name="cluster"),
                df["Phase"],
                normalize="index",
            ).round(3)
            plot_cluster_heatmap(cluster_table)

    plot_pca_comparison(df, pca_scores["raw_scaled"], pca_scores["subject_z"])
    plot_r2_bars(r2_rows)

    model_df = pd.DataFrame(model_rows)
    model_df.to_csv(TABLE_DIR / "model_summary.csv", index=False)

    supervised_metrics = supervised_sanity_check(df, feature_cols)
    ocs_metrics = one_class_svm_loso(df, feature_cols, nu=0.10)
    cca_summary = cca_poster_analysis(df, feature_cols, affect_columns())
    embedding_metrics = embedding_poster_comparison(df, feature_cols)
    summary["supervised_sanity_loso_logistic"] = supervised_metrics
    summary["one_class_svm_loso_nu_0_10"] = ocs_metrics
    summary["poster_figure_analysis"] = {
        "cca": cca_summary,
        "embeddings": embedding_metrics,
    }

    with open(TABLE_DIR / "analysis_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))
    print(model_df.to_string(index=False))
    print(pd.DataFrame(r2_rows).to_string(index=False))


if __name__ == "__main__":
    main()
