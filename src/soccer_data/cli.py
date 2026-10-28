"""Command-line runner for notebook-equivalent data construction."""
import argparse
import json
from pathlib import Path
from .pipeline import Config, SourceData, DatasetMerge


def main():
    p = argparse.ArgumentParser(description='Reproduce soccer team-season data merging, no modeling')
    p.add_argument('--matches', help='Match workbook with Match Data and Season Results Data sheets')
    p.add_argument('--transfers', help='Preprocessed transfer Excel workbook')
    p.add_argument('--transfer-csv-dir', help='Directory containing YYYY.csv source transfer files')
    p.add_argument('--download-matches', action='store_true', help='Download Understat instead of match workbook')
    p.add_argument('--league', default='EPL', help='Understat league identifier')
    p.add_argument('--transfer-league', default='Premier League', help='League label in transfer data')
    p.add_argument('--club-map', help='Optional JSON object mapping transfer team names to Understat names')
    p.add_argument('--start-year', type=int, default=2015)
    p.add_argument('--end-year', type=int, default=2025)
    p.add_argument('--previous-matches', type=int, default=10)
    p.add_argument('--current-matches', type=int, default=10)
    p.add_argument('--output', default='outputs/merged_team_seasons.xlsx')
    args = p.parse_args()
    if args.start_year >= args.end_year: p.error('At least two seasons are required for prior-season features')
    if args.previous_matches < 1 or args.current_matches < 1: p.error('Match windows must be positive')
    if not args.download_matches and not args.matches: p.error('Supply --matches or --download-matches')
    if not args.transfers and not args.transfer_csv_dir: p.error('Supply --transfers or --transfer-csv-dir')
    mapping = json.loads(Path(args.club_map).read_text()) if args.club_map else None
    config = Config(args.start_year, args.end_year, args.previous_matches,
                    args.current_matches, args.league, args.transfer_league, mapping)
    if args.download_matches:
        matches, results = SourceData.understat(args.league, args.start_year, args.end_year)
    else:
        import pandas as pd
        matches = pd.read_excel(args.matches, sheet_name='Match Data')
        results = pd.read_excel(args.matches, sheet_name='Season Results Data')
    if args.transfer_csv_dir:
        transfers = SourceData.transfer_csvs(args.transfer_csv_dir, args.start_year,
                                             args.end_year, args.transfer_league)
    else:
        import pandas as pd
        transfers = pd.read_excel(args.transfers)
    merged = DatasetMerge(config).merge(matches, results, transfers)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.suffix.lower() == '.csv': merged.to_csv(target, index=False)
    elif target.suffix.lower() == '.xlsx': merged.to_excel(target, index=False)
    else: p.error('--output must end in .xlsx or .csv')
    print(f'Wrote {len(merged)} team-seasons, {len(merged.columns)} columns to {target}')

if __name__ == '__main__':
    main()
