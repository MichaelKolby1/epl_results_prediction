# EPL Results Prediction

**Current project stage:** Data acquisition, preparation, exploratory data analysis, and baseline modeling (Milestone 2). This repository implements a reproducible workflow for integrating Premier League match and transfer data, exploring relationships with final-season points, and evaluating simple baseline predictions. More advanced regression and team-strength modeling are planned for Milestone 3.

## Project overview and goals

The broader project investigates **how accurately a Premier League club's final season points can be predicted from its prior-season characteristics, summer transfer activity, and performance early in the current season**.

Our primary forecasting setup makes predictions **after each club's first 10 league matches**. The planned predictors include performance from the **last 10 matches of the previous season**, performance from the **first 10 matches of the current season**, and activity in the **preceding summer transfer window**. The intended prediction target is the club's **final league points** at the end of the season.

The overall goals are to:

1. Combine match statistics and transfer activity into an analysis-ready team-season dataset.
2. Examine the relationships between historical performance, early-season results, team resources, and final points.
3. Evaluate predictive performance against simple baselines using chronological validation, then investigate whether additional performance and transfer features improve prediction accuracy.

Although the project focuses on the English Premier League (EPL), the data-preparation pipeline accepts configurable seasons, match windows, and compatible input data from other leagues.

## Scope of this repository

The repository covers data collection, cleaning, feature engineering, dataset integration, exploratory analysis, and baseline evaluation. The standard EPL configuration uses data from 2015/16–2025/26, reserving the first season for historical context and producing 200 club-season observations across 2016/17–2025/26, with 49 columns.

Exploratory analysis examines promotion status, early-season points, and transfer spending. Baseline evaluation compares previous-season points with a training-mean reference using chronological testing. Multiple regression and Bradley–Terry modeling remain future work.

## Data sources

| Source | Content | Access |
| --- | --- | --- |
| [Understat](https://understat.com/) | Match results and team-match performance statistics, including expected goals and expected points | Existing prepared match workbook or direct download through the `understatapi` Python package |
| [eordo/transfermarkt-data](https://github.com/eordo/transfermarkt-data) | Season-level club/player transfer records derived from Transfermarkt | Existing prepared transfer workbook or manually downloaded season CSVs |

For reproducibility, keep the source files and their provenance (source URLs, season coverage, retrieval date, and ideally source commit) alongside your local run notes. **Fresh upstream downloads may differ from an earlier dataset snapshot.**

## Repository layout

```text
epl_results_prediction/
├── README.md
├── pyproject.toml
├── .gitignore
├── src/
│   └── soccer_data/
│       ├── __init__.py
│       ├── pipeline.py       # Configuration, data inputs, cleaning and merging
│       └── cli.py            # Command-line execution
├── notebooks/                # Supplementary exploration and data inspection
│   ├── match_data_download.ipynb
│   ├── transfer_data_download.ipynb
│   ├── file_merge.ipynb
│   ├── milestone1_EDA.ipynb
│   ├── milestone2_EDA.ipynb
│   └── baseline_evaluation.ipynb
├── data/
│   ├── raw/                  # Included EPL source workbooks
│   │   ├── epl_match_data.xlsx
│   │   ├── epl_transfer_data.xlsx
│   │   └── external/         # Manually downloaded season transfer CSVs
│   ├── reference/            # Reference output for checking reproducibility
│   └── processed/            # Optional processed exports
├── outputs/                  # Pipeline output files
└── tests/
    └── test_reference.py     # Reference comparison and configuration tests
```

**Note:** The EPL source workbooks are included in the repository for Workflow A. Check the upstream data sources’ reuse terms before redistributing third-party data.

## Data pipeline

The pipeline follows the same steps regardless of where the input files originate:

1. **Load match records:** read an existing Excel workbook with `Match Data` and `Season Results Data` worksheets, or retrieve match information from Understat.
2. **Load transfer records:** read an existing prepared transfer workbook, or process locally downloaded annual transfer CSVs from the external repository.
3. **Prepare match features:** aggregate team-match performance over the selected previous-season and current-season match windows.
4. **Prepare transfer features:** summarize transfers by club, season, and window; carry forward the summer-window measures needed for the team-season table.
5. **Standardize and merge:** reconcile club names across sources and join the match, transfer, and final-season results information by team and season.
6. **Export and check:** write the merged `.xlsx` or `.csv` file and optionally run the automated reference tests.

### Installation (both workflows)

From a Windows PowerShell terminal (for example, in VS Code):

```powershell
git clone https://github.com/MichaelKolby1/epl_results_prediction.git
cd epl_results_prediction
python -m venv .venv
python -m pip install -e ".[download,test]"
```

Run commands from the repository root. To see the available pipeline arguments, run `soccer-data-merge --help`.

### Workflow A — Use the existing EPL datasets

1. Confirm the included EPL input files are present:

   ```text
   data/raw/epl_match_data.xlsx
   data/raw/epl_transfer_data.xlsx
   ```

   The files are provided with the repository; no additional download is needed for this workflow.

2. Run:

   ```powershell
   soccer-data-merge --matches data/raw/epl_match_data.xlsx --transfers data/raw/epl_transfer_data.xlsx --league EPL --transfer-league "Premier League" --start-year 2015 --end-year 2025 --previous-matches 10 --current-matches 10 --output outputs/epl_merged_data.xlsx
   ```

3. Find the generated workbook at `outputs/epl_merged_data.xlsx` (**200 rows, 49 columns** for the original data snapshot). To run the tests, ensure the reference workbook is present at `data/reference/epl_merged_data.xlsx`, then run:

   ```powershell
   python -m pytest -q
   ```

To test another EPL time frame without downloading more data, change the start/end years and output filename. For example:

```powershell
soccer-data-merge --matches data/raw/epl_match_data.xlsx --transfers data/raw/epl_transfer_data.xlsx --league EPL --transfer-league "Premier League" --start-year 2018 --end-year 2022 --previous-matches 10 --current-matches 10 --output outputs/epl_2018_2022.xlsx
```

### Workflow B — Use newly collected data

1. Download one `YYYY.csv` transfer file per season from the appropriate league directory in [eordo/transfermarkt-data](https://github.com/eordo/transfermarkt-data). Put the files in `data/raw/external/` (for example, `2020.csv` through `2023.csv` for input seasons 2020–2023). Check the `league` field in the CSVs for the exact label to supply to `--transfer-league`.

2. Download Understat match data *and* merge the transfer CSVs in one command. For example, for La Liga:

   ```powershell
   soccer-data-merge --download-matches --league La_liga --transfer-csv-dir data/raw/external --transfer-league "La Liga" --start-year 2020 --end-year 2023 --previous-matches 10 --current-matches 10 --output outputs/laliga_2020_2023.xlsx
   ```

   Replace the league ID, transfer-league label, and years with those available in your source data. Use `--club-map PATH` if club names differ across sources. The pipeline does **not** download transfer CSVs automatically.

3. Inspect the generated file in `outputs/`, checking seasons, club names, and missing values. Other leagues and fresh downloads have not been fully verified against a reference output.

If you already have a compatible match workbook, use `--matches PATH` instead of `--download-matches`. If you already have a prepared transfer workbook, use `--transfers PATH` instead of `--transfer-csv-dir`.


**Validation status:** the standard EPL reference workflow has been tested. Direct-download behavior and complete cross-league reproduction depend on third-party availability, source schema, and club-name mappings; they have not been fully validated for every alternative league and year range.

## Command-line arguments

| Argument | Description |
| --- | --- |
| `--matches PATH` | Existing match workbook containing `Match Data` and `Season Results Data` |
| `--download-matches` | Download match data directly from Understat instead |
| `--transfers PATH` | Existing prepared transfer Excel workbook |
| `--transfer-csv-dir PATH` | Directory of manually downloaded annual transfer CSVs |
| `--league ID` | Understat league identifier; default `EPL` |
| `--transfer-league NAME` | League label used in the transfer records |
| `--start-year`, `--end-year` | Inclusive starting years of input seasons; require at least two seasons |
| `--previous-matches` | Number of matches summarized from the previous season |
| `--current-matches` | Number of matches summarized from the current season |
| `--club-map PATH` | Optional JSON mapping of transfer-source to match-source club names |
| `--output PATH` | Output `.xlsx` or `.csv` path |

Provide one primary input option per source. If both are supplied, `--download-matches` takes priority over `--matches`, and `--transfer-csv-dir` takes priority over `--transfers`.

## Dataset limitations and considerations

- **League and year availability:** Understat and the transfer-data collection do not necessarily offer the same leagues or years. Missing source seasons can limit the usable period.
- **Transfer-data missingness:** reported transfer fees and player market valuations are sometimes unavailable. In the original EPL collection, approximately **6.77% of transfer fees** and **4.09% of player market values** are missing; these should not automatically be interpreted as zero.
- **Names and identifiers:** club names may differ across Understat and transfer records. Unresolved name differences can result in unmatched transfer features.
- **Promoted clubs:** clubs without Premier League results from the preceding season lack directly comparable previous-season top-flight performance. The standard EPL preparation uses league averages for missing prior-season measures.
- **Official points adjustments:** final standings points can differ from points totaled from match outcomes because of disciplinary deductions or other adjustments. The pipeline uses the provided season-results data for final points.
- **Source updates and coverage quality:** third-party corrections, scraping gaps, incomplete seasons, and changing upstream formats may affect newly retrieved records and reproducibility.

## Next stage: predictive modeling

Milestone 2 established a reproducible dataset, exploratory findings, and preliminary baseline results. Milestone 3 will investigate multiple regression models incorporating early-season performance, promotion status, and potentially transfer activity. We will also explore Bradley–Terry models for estimating relative team strengths from head-to-head results. These approaches will be compared with the existing baseline using chronological evaluation, MSE, MAD, and residual diagnostics, with particular attention to newly promoted teams.
## Attribution

- Match and performance statistics: [Understat](https://understat.com/), accessed through `understatapi` or prepared workbooks.
- Transfers: [eordo/transfermarkt-data](https://github.com/eordo/transfermarkt-data), a Transfermarkt-derived data collection. Consult the upstream source for its methodology, coverage, and reuse terms.
