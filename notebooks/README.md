# Jupyter Notebook Reproduction Guide — ISyE 4031 Milestone 2

This folder contains six notebooks for manually reproducing the EPL data collection, preparation, exploratory analysis, and baseline evaluation. No automated pipeline is required.

## Setup

Download the [GitHub repository](https://github.com/MichaelKolby1/epl_results_prediction) (**Code → Download ZIP**), extract it, and install **Python 3.10+** and the notebook packages:

```bash
python -m pip install "numpy>=1.24" "pandas>=2.0" "openpyxl>=3.1" "understatapi>=0.6" "matplotlib>=3.7" "ipython>=8" "ipykernel>=6" "jupyterlab>=4"
```

From the `notebooks/` directory, start Jupyter with `python -m jupyter lab` and run each notebook using **Run → Run All Cells**.

## Notebook workflow

1. **`match_data_download.ipynb`** — Collects EPL match statistics and season results from Understat; creates `epl_match_data.xlsx`.
2. **`transfer_data_download.ipynb`** — Prepares Transfermarkt-derived records; creates `epl_transfer_data.xlsx`.
3. **`file_merge.ipynb`** — Cleans, engineers features, and merges the two workbooks; creates `epl_merged_data.xlsx` (200 club-season rows, 49 columns).
4. **`milestone1_EDA.ipynb`** — Uses `epl_match_data.xlsx` and `epl_transfer_data.xlsx` for preliminary exploration; saves `angelo_figure1.png`.
5. **`milestone2_EDA.ipynb`** — Uses `epl_merged_data.xlsx` to generate the promotion summary and early-performance/spending plots: `table1_promotion_summary.png`, `figure1_early_points.png`, and `figure2_summer_spending.png`.
6. **`baseline_evaluation.ipynb`** — Uses the **Season Results Data** sheet in `epl_match_data.xlsx` to compare previous-season and training-mean forecasts; saves `nicolas_baseline_predictions.png` and displays MSE/MAD results.

## File locations and reproduction notes

The EDA and baseline notebooks read Excel files using **filenames without folder paths**. Before running them, place the required `.xlsx` files in the same working directory as the notebooks (copy them from `data/raw/` or the location where the download/merge notebooks saved them). If the original Excel files are supplied, you can skip the first three notebooks and run the analyses directly.

The final EDA and baseline use **2016/17–2022/23** for training (140 club-seasons); the baseline tests on **2023/24–2025/26** (60 club-seasons). The calculations are deterministic, so no random seed is needed. The version ranges above are installation minimums; record your exact environment with `python -m pip freeze` if required.
