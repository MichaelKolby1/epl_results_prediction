# EPL Results Prediction

**Current project stage: Data acquisition, exploratory analysis, preparation, and integration.** This repository currently implements the data pipeline needed for the broader EPL results prediction project. It produces a structured team-season dataset for subsequent statistical analysis and modeling; **it does not yet train, tune, or evaluate prediction models**.

## Project overview and goals

The broader project investigates **how accurately a Premier League club's final season points can be predicted from its prior-season characteristics, summer transfer activity, and performance early in the current season**.

Our primary forecasting setup makes predictions **after each club's first 10 league matches**. The planned predictors include performance from the **last 10 matches of the previous season**, performance from the **first 10 matches of the current season**, and activity in the **preceding summer transfer window**. The intended prediction target is the club's **final league points** at the end of the season.

The overall goals are to:

1. Combine match statistics and transfer activity into an analysis-ready team-season dataset.
2. Examine the relationships between historical performance, early-season results, team resources, and final points.
3. In a subsequent stage, evaluate whether these characteristics improve predictions of final points compared with simple baselines, using chronological validation to avoid future-information leakage.

Although the project focuses on the English Premier League (EPL), the data-preparation pipeline accepts configurable seasons, match windows, and compatible input data from other leagues.

## Scope of this repository

The **current stage** covers sourcing the data, checking and cleaning input fields, constructing team-level summaries, joining the datasets, and producing a consistent final table for analysis. Model selection, training, cross-validation, predictions, and model comparisons are **future work** during the semester.

The standard EPL run covers input seasons **2015/16–2025/26**, using 2015/16 for prior-season context and generating **200 team-season observations across 2016/17–2025/26**. The output contains **49 columns** in the reference configuration. The 2025/26 final-points field comes from the supplied historical data snapshot; verify the completeness of any source season before using it as a model target.

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
│   ├── __init__.py
│   ├── pipeline.py           # Configuration, data inputs, cleaning and merging
│   └── cli.py                # Command-line execution
├── notebooks/                # Supplementary exploration and data inspection
├── data/
│   ├── raw/                  # Local source workbooks
│   │   └── external/         # Manually downloaded season transfer CSVs
│   ├── reference/            # Reference output for checking reproducibility
│   └── processed/            # Optional processed exports
├── outputs/                  # Pipeline output files
└── tests/
    └── test_reference.py     # Reference comparison and configuration tests
```

**Note:** The downloadable review package contains local EPL data files. Raw third-party data are ignored by Git; they will not automatically appear in a GitHub clone. Check permissions before redistributing original files or merged data that include third-party records.

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
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[download,test]"
```

Run commands from the repository root. The installed `soccer-data-merge` command requires the package layout and entry point in `pyproject.toml` to agree; the configuration in this README assumes `src/soccer_data/`. To see the available arguments, run `soccer-data-merge --help`.

### Workflow A — Use the existing EPL datasets

1. Place the prepared files in `data/raw/`:

   ```text
   data/raw/epl_match_data.xlsx
   data/raw/epl_transfer_data.xlsx
   ```

   These files may not be included in a GitHub clone; copy them from the project data shared with your team. The match workbook must contain `Match Data` and `Season Results Data` sheets.

2. Run:

   ```powershell
   soccer-data-merge --matches data/raw/epl_match_data.xlsx --transfers data/raw/epl_transfer_data.xlsx --league EPL --transfer-league "Premier League" --start-year 2015 --end-year 2025 --previous-matches 10 --current-matches 10 --output outputs/epl_merged_data.xlsx
   ```

3. Find the resulting workbook at `outputs/epl_merged_data.xlsx` (**200 rows, 49 columns** for the original data snapshot). To run the reference tests, also place the original merged workbook at `data/reference/epl_merged_data.xlsx`, then run:

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

- **Small analytical sample:** each team-season is one observation. EPL coverage provides 20 clubs per season; repeated clubs across seasons are not statistically independent.
- **League and year availability:** Understat and the transfer-data collection do not necessarily offer the same leagues or years. Missing source seasons can limit the usable period.
- **Transfer-data missingness:** reported transfer fees and player market valuations are sometimes unavailable. In the original EPL collection, approximately **6.77% of transfer fees** and **4.09% of player market values** are missing; these should not automatically be interpreted as zero.
- **Names and identifiers:** club names may differ across Understat and transfer records. Unresolved name differences can result in unmatched transfer features.
- **Timing of information:** final points are included as an outcome for historical analysis. Future modeling must restrict features to information observable by the prediction point (after Match 10) to avoid leakage.
- **Promoted clubs:** clubs without Premier League results from the preceding season lack directly comparable previous-season top-flight performance. The standard EPL preparation uses league averages for missing prior-season measures.
- **Match sequence:** early/late match-window statistics depend on the chronological ordering of team-match records, which should be checked for each new source.
- **Official points adjustments:** final standings points can differ from points totaled from match outcomes because of disciplinary deductions or other adjustments. The pipeline uses the provided season-results data for final points.
- **Source updates and coverage quality:** third-party corrections, scraping gaps, incomplete seasons, and changing upstream formats may affect newly retrieved records and reproducibility.

## Next stage: predictive modeling

Once the combined dataset is finalized and checked, the broader project will develop and compare models to predict final EPL points. Planned evaluation will use time-ordered training and testing, a baseline predictor, and error measures such as mean squared error (MSE). The present repository is deliberately limited to the data preparation and analysis stage.

## Attribution

- Match and performance statistics: [Understat](https://understat.com/), accessed through `understatapi` or prepared workbooks.
- Transfers: [eordo/transfermarkt-data](https://github.com/eordo/transfermarkt-data), a Transfermarkt-derived data collection. Consult the upstream source for its methodology, coverage, and reuse terms.
