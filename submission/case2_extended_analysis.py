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
from sklearn.cross_decomposition import CCA
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.manifold import TSNE
from sklearn.metrics import accuracy_score, silhouette_score
from sklearn.model_selection import GroupKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler


BASE_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = Path(__file__).resolve().parent
FIG_DIR = OUT_DIR / "figures"
TABLE_DIR = OUT_DIR / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    with ZipFile(BASE_DIR / "HR_data_2.zip") as zipf:
        with zipf.open("HR_data_2.csv") as f:
            df = pd.read_csv(f, index_col=0)
    feature_cols = df.columns[:51].tolist()
    affect_cols = [
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
    return df, feature_cols, affect_cols


def safe_subject_z(df, feature_cols):
    def safe_z(col):
        std = col.std(ddof=0)
        if std == 0 or np.isnan(std):
            return col - col.mean()
        return (col - col.mean()) / std

    return df[feature_cols].groupby(df["Individual"]).transform(safe_z)


def fit_xy(df, feature_cols, affect_cols):
    x_df = safe_subject_z(df, feature_cols)
    x = SimpleImputer(strategy="median").fit_transform(x_df)
    x = StandardScaler().fit_transform(x)

    y_df = df[affect_cols].copy()
    y = SimpleImputer(strategy="median").fit_transform(y_df)
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


def cca_analysis(df, feature_cols, affect_cols, n_permutations=200):
    x, y = fit_xy(df, feature_cols, affect_cols)
    groups = df["Individual"].to_numpy()

    pca = PCA(n_components=8, random_state=0)
    x_pca = pca.fit_transform(x)
    cca = CCA(n_components=1, max_iter=1000)
    u, v = cca.fit_transform(x_pca, y)
    in_sample_r = float(abs(np.corrcoef(u[:, 0], v[:, 0])[0, 1]))

    cv_rs = []
    for train_idx, test_idx in GroupKFold(n_splits=5).split(x, groups=groups):
        imp_x = SimpleImputer(strategy="median").fit(safe_subject_z(df.iloc[train_idx], feature_cols))
        sc_x = StandardScaler().fit(imp_x.transform(safe_subject_z(df.iloc[train_idx], feature_cols)))
        x_train = sc_x.transform(imp_x.transform(safe_subject_z(df.iloc[train_idx], feature_cols)))
        x_test = sc_x.transform(imp_x.transform(safe_subject_z(df.iloc[test_idx], feature_cols)))

        imp_y = SimpleImputer(strategy="median").fit(df.iloc[train_idx][affect_cols])
        sc_y = StandardScaler().fit(imp_y.transform(df.iloc[train_idx][affect_cols]))
        y_train = sc_y.transform(imp_y.transform(df.iloc[train_idx][affect_cols]))
        y_test = sc_y.transform(imp_y.transform(df.iloc[test_idx][affect_cols]))

        pca_cv = PCA(n_components=8, random_state=0).fit(x_train)
        x_train_pca = pca_cv.transform(x_train)
        x_test_pca = pca_cv.transform(x_test)
        cca_cv = CCA(n_components=1, max_iter=1000)
        cca_cv.fit(x_train_pca, y_train)
        u_test, v_test = cca_cv.transform(x_test_pca, y_test)
        cv_rs.append(abs(np.corrcoef(u_test[:, 0], v_test[:, 0])[0, 1]))

    # Subject-block permutation: shuffle each participant's questionnaire block as a whole.
    rng = np.random.default_rng(0)
    unique_groups = np.unique(groups)
    perm_rs = []
    group_to_indices = {g: np.where(groups == g)[0] for g in unique_groups}
    for _ in range(n_permutations):
        shuffled_groups = rng.permutation(unique_groups)
        y_perm = np.empty_like(y)
        for src_g, dst_g in zip(unique_groups, shuffled_groups):
            src_idx = group_to_indices[src_g]
            dst_idx = group_to_indices[dst_g]
            y_perm[src_idx] = y[dst_idx]
        cca_perm = CCA(n_components=1, max_iter=1000)
        u_perm, v_perm = cca_perm.fit_transform(x_pca, y_perm)
        perm_rs.append(abs(np.corrcoef(u_perm[:, 0], v_perm[:, 0])[0, 1]))
    p_value = float((np.sum(np.array(perm_rs) >= in_sample_r) + 1) / (n_permutations + 1))

    # Correlation loadings for interpretability.
    x_variate = u[:, 0]
    y_variate = v[:, 0]
    x_corr = []
    for col_i, col in enumerate(feature_cols):
        x_corr.append(np.corrcoef(x[:, col_i], x_variate)[0, 1])
    y_corr = []
    for col_i, col in enumerate(affect_cols):
        y_corr.append(np.corrcoef(y[:, col_i], y_variate)[0, 1])

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

    affect_colors = ["#C85A4A" if v > 0 else "#2F6FAD" for v in affect_df["corr"]]
    axes[1].barh(affect_df["affect"], affect_df["corr"], color=affect_colors)
    axes[1].axvline(0, color="#666666", lw=0.8)
    axes[1].set_title("B. Questionnaire CCA loadings")
    axes[1].set_xlabel("Correlation with affective canonical variate")
    axes[1].tick_params(labelsize=8)

    fig.suptitle(f"CCA: physiology-affect coupling, in-sample r={in_sample_r:.3f}, GroupKFold r={np.mean(cv_rs):.3f} +/- {np.std(cv_rs):.3f}", y=1.03)
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
        "top_affect_features": affect_df.reindex(affect_df["corr"].abs().sort_values(ascending=False).index).head(5)[["affect", "corr"]].to_dict(orient="records"),
    }


def embedding_comparison(df, feature_cols):
    x, _ = fit_xy(df, feature_cols, ["Frustrated", "upset", "hostile", "alert", "ashamed", "inspired", "nervous", "attentive", "afraid", "active", "determined"])
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
    df, feature_cols, affect_cols = load_data()
    cca_summary = cca_analysis(df, feature_cols, affect_cols)
    embedding_metrics = embedding_comparison(df, feature_cols)
    summary = {"cca": cca_summary, "embeddings": embedding_metrics}
    with open(TABLE_DIR / "extended_analysis_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
