"""Notebook-faithful ETL; only source/configuration parameters are generalized."""
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class Config:
    start_year: int = 2015  # earliest source season, used as prior-year history
    end_year: int = 2025    # inclusive latest source season
    previous_matches: int = 10
    current_matches: int = 10
    league: str = "EPL"  # Understat league ID
    transfer_league: str | None = "Premier League"  # optional CSV filtering
    club_mapping: dict | None = None  # e.g. custom La Liga mapping

class SourceData:
    """Load the original workbooks or reproduce source notebooks."""
    @staticmethod
    def workbooks(match_file, transfer_file):
        matches = pd.read_excel(match_file, sheet_name="Match Data")
        results = pd.read_excel(match_file, sheet_name="Season Results Data")
        transfers = pd.read_excel(transfer_file)
        return matches, results, transfers

    @staticmethod
    def transfer_csvs(folder, start_year, end_year, league=None):
        """Equivalent to transfer_data_download.ipynb; folder contains YYYY.csv."""
        data = pd.concat([pd.read_csv(Path(folder) / f"{yr}.csv")
                          for yr in range(start_year, end_year + 1)], ignore_index=True)
        if league is not None and 'league' in data.columns:
            data = data.loc[data['league'] == league].copy()
        data['Fee_Missing'] = data['fee'].isna().astype(int)
        data['Market_Value_Missing'] = data['market_value'].isna().astype(int)
        data['dealing_country'] = data['dealing_country'].fillna('None')
        return data

    @staticmethod
    def understat(league, start_year, end_year):
        """Reproduce match_data_download.ipynb, using its match-level source fields."""
        from understatapi import UnderstatClient
        match_rows = []

        with UnderstatClient() as understat:
            for year in range(start_year, end_year + 1):
                match_info_cache = {}
                season_match_lookup = {}
                season_team_data = understat.league(league=league).get_team_data(season=f"{year}")
                season_match_data = understat.league(league=league).get_match_data(season=f"{year}")

                for game in season_match_data:
                    season_match_lookup[(game["h"]["id"], game["datetime"])] = game["id"]
                    season_match_lookup[(game["a"]["id"], game["datetime"])] = game["id"]

                for club, data in season_team_data.items():
                    club_name = data["title"]
                    club_ID = data["id"]
                    history = data["history"]
                    total_points = 0
                    for match in history:
                        home_or_away = match["h_a"]
                        match_date = match["date"]
                        match_id = season_match_lookup[(club_ID, match_date)]
                        if match_id not in match_info_cache:
                            match_info_cache[match_id] = understat.match(match=match_id).get_match_info()
                        match_info = match_info_cache[match_id]
                        opponent = (
                            match_info[f"team_a"]
                            if home_or_away == "h"
                            else match_info[f"team_h"]
                        )
                        opponent_goals = (
                            match_info[f"a_goals"]
                            if home_or_away == "h"
                            else match_info[f"h_goals"]
                        )
                        opponent_shots = (
                            match_info[f"a_shot"]
                            if home_or_away == "h"
                            else match_info[f"h_shot"]
                        )
                        opponent_SOT = (
                            match_info[f"a_shotOnTarget"]
                            if home_or_away == "h"
                            else match_info[f"h_shotOnTarget"]
                        )
                        win_odds = (
                            match_info["h_w"] if home_or_away == "h" else match_info["h_l"]
                        )
                        lose_odds = (
                            match_info["h_l"] if home_or_away == "h" else match_info["h_w"]
                        )
                        draw_odds = match_info["h_d"]
                        total_points += match["pts"]
                        match_rows.append(
                            {
                                "Team": club_name,
                                "Team_ID": club_ID,
                                "Match_ID": match_id,
                                "Opponent": opponent,
                                "Home_or_Away": home_or_away,
                                "Season": year,
                                "Date": match_date,
                                "Win_Percentage": float(win_odds),
                                "Loss_Percentage": float(lose_odds),
                                "Draw_Percentage": float(draw_odds),
                                "Goals": int(match["scored"]),
                                "Shots": int(match_info[f"{home_or_away}_shot"]),
                                "Shots_on_Target": int(match_info[f"{home_or_away}_shotOnTarget"]),
                                "Opp_Goals": int(opponent_goals),
                                "Opp_Shots": int(opponent_shots),
                                "Opp_Shots_on_Target": int(opponent_SOT),
                                "xG": float(match["xG"]),
                                "xGA": float(match["xGA"]),
                                "npxG": float(match["npxG"]),
                                "npxGA": float(match["npxGA"]),
                                "npxGD": float(match["npxGD"]),
                                "Deep": float(match["deep"]),
                                "Deep_Allowed": float(match["deep_allowed"]),
                                "Expected_Points": float(match["xpts"]),
                                "Points": match["pts"],
                                "Total_Points": total_points,
                            }
                        )
        match_data = pd.DataFrame(match_rows)
        match_data['Result'] = np.select([match_data['Goals'] > match_data['Opp_Goals'],
            match_data['Goals'] < match_data['Opp_Goals'], match_data['Goals'] == match_data['Opp_Goals']],
            ['Win', 'Loss', 'Draw'], default='Unkown')
        first_cols = ['Team', 'Team_ID', 'Match_ID', 'Opponent', 'Home_or_Away',
                      'Season', 'Date', 'Result', 'Win_Percentage', 'Loss_Percentage', 'Draw_Percentage']
        match_data = match_data[first_cols + [c for c in match_data if c not in first_cols]]
        season_results = (match_data.groupby(['Season', 'Team'])['Total_Points']
                          .max().reset_index().sort_values(['Season', 'Total_Points'], ascending=[True,False]))
        return match_data, season_results

class DatasetMerge:
    """Minimal notebook-faithful merge: one public method."""
    def __init__(self, config: Config):
        self.config = config

    def merge(self, match_data, season_results, transfer_data):
        match_data = match_data.copy()
        season_results = season_results.copy()
        transfer_data = transfer_data.copy()
        if self.config.transfer_league is not None and 'league' in transfer_data:
            transfer_data = transfer_data.loc[
                transfer_data['league'] == self.config.transfer_league].copy()
        STARTING_YR = self.config.start_year
        ENDING_YR = self.config.end_year + 1
        PREV_MATCHES = self.config.previous_matches
        CURR_MATCHES = self.config.current_matches
        club_name_map = {
            "AFC Bournemouth": "Bournemouth",
            "Arsenal FC": "Arsenal",
            "Brentford FC": "Brentford",
            "Brighton & Hove Albion": "Brighton",
            "Burnley FC": "Burnley",
            "Cardiff City": "Cardiff",
            "Chelsea FC": "Chelsea",
            "Everton FC": "Everton",
            "Fulham FC": "Fulham",
            "Huddersfield Town": "Huddersfield",
            "Hull City": "Hull",
            "Ipswich Town": "Ipswich",
            "Leeds United": "Leeds",
            "Leicester City": "Leicester",
            "Liverpool FC": "Liverpool",
            "Luton Town": "Luton",
            "Middlesbrough FC": "Middlesbrough",
            "Norwich City": "Norwich",
            "Southampton FC": "Southampton",
            "Stoke City": "Stoke",
            "Sunderland AFC": "Sunderland",
            "Swansea City": "Swansea",
            "Tottenham Hotspur": "Tottenham",
            "Watford FC": "Watford",
            "West Ham United": "West Ham"
        }

        transfer_data["club"] = transfer_data["club"].replace({**club_name_map, **(self.config.club_mapping or {})}) # Standardize club names in transfer_data using the mapping

        transfer_data["season"] = transfer_data["season"].astype(int) # Convert the "season" column in transfer_data to integer type
        match_data["Season"] = match_data["Season"].astype(int) # Convert the "Season" column in match_data to integer type

        window_spending = transfer_data[transfer_data["movement"] == "in"].groupby(["season", "club", "window"]).agg({"fee": "sum"}).reset_index() # Calculate the total transfer fees for incoming transfers by season, club, and window
        window_earnings = transfer_data[(transfer_data["movement"] == "out")].groupby(["season", "club", "window"]).agg({"fee": "sum"}).reset_index() # Calculate the total estimated transfer earnings for outgoing transfers by season, club, and window

        net_spending = pd.merge(window_spending, window_earnings, on = ["season", "club", "window"],  how = "outer", suffixes = ("_spending", "_earnings")) # Merge spending and earnings data
        net_spending["net_spending"] = net_spending["fee_spending"].fillna(0) - net_spending["fee_earnings"].fillna(0) # Calculate net spending by subtracting earnings from spending, filling NaN values with 0

        permanent_in = transfer_data[(transfer_data["movement"] == "in") & (transfer_data["is_loan"] == False)].groupby(["season", "club", "window"]).agg({"player_name": "count"}).reset_index() # Count the number of incoming transfers by season, club, and window
        permanent_out = transfer_data[(transfer_data["movement"] == "out") & (transfer_data["is_loan"] == False)].groupby(["season", "club", "window"]).agg({"player_name": "count"}).reset_index() # Count the number of outgoing transfers by season, club, and window
        permanent_in.rename(columns={"player_name": "permanent_in_count"}, inplace=True) # Rename the column for incoming transfers count
        permanent_out.rename(columns={"player_name": "permanent_out_count"}, inplace=True) # Rename the column for outgoing transfers count

        loan_in = transfer_data[(transfer_data["movement"] == "in") & (transfer_data["is_loan"] == True)].groupby(["season", "club", "window"]).agg({"player_name": "count"}).reset_index() # Count the number of incoming loans by season, club, and window
        loan_out = transfer_data[(transfer_data["movement"] == "out") & (transfer_data["is_loan"] == True)].groupby(["season", "club", "window"]).agg({"player_name": "count"}).reset_index() # Count the number of outgoing loans by season, club, and window
        loan_in.rename(columns={"player_name": "loan_in_count"}, inplace=True) # Rename the column for incoming loans count
        loan_out.rename(columns={"player_name": "loan_out_count"}, inplace=True) # Rename the column for outgoing loans count

        average_age_in = transfer_data[transfer_data["movement"] == "in"].groupby(["season", "club", "window"]).agg({"age": "mean"}).reset_index() # Calculate the average age of incoming transfers by season, club, and window
        average_age_in.rename(columns = {"age": "average_age_in"}, inplace = True) # Rename the column for average age of incoming transfers

        in_missing_fees = transfer_data[(transfer_data["movement"] == "in") & (transfer_data["fee"].isnull())].groupby(["season", "club", "window"]).size().reset_index(name="missing_in_fees_count") # Count the number of incoming transfers with missing fee information by season, club, and window
        out_missing_fees = transfer_data[(transfer_data["movement"] == "out") & (transfer_data["fee"].isnull())].groupby(["season", "club", "window"]).size().reset_index(name="missing_out_fees_count") # Count the number of outgoing transfers with missing fee information by season, club, and window

        # Merging all the transfer-related data into a single DataFrame
        transfer_stats = net_spending.copy() # Start with net spending data
        for df in [permanent_in, permanent_out, loan_in, loan_out, average_age_in, in_missing_fees, out_missing_fees]:
            transfer_stats = pd.merge(transfer_stats, df, on=["season", "club", "window"], how="outer", suffixes=('', '_x')) # Merge each DataFrame into transfer_stats on season, club, and window
        transfer_stats = transfer_stats.fillna(0) # Fill NaN values in the merged transfer statistics DataFrame with 0 

        transfer_stats = transfer_stats[transfer_stats["season"].between(STARTING_YR, ENDING_YR-1)]

        # Merge all the transfer-related results into a single DataFrame with the match_data
        merged_matches_data = pd.DataFrame() # Initialize an empty DataFrame to hold the merged data
        for year in range(STARTING_YR, ENDING_YR):
            match_data_year = match_data[match_data["Season"] == year] # Filter match_data for the current year
            transfer_stats_year = transfer_stats[transfer_stats["season"] == year] # Filter transfer_stats for the current year

            # Filter match_data for matches before winter and after winter, merging the corresponding transfer stats for each half of a season then merging with the running merged_matches_data DataFrame
            matches_before_winter = match_data_year[pd.to_datetime(match_data_year["Date"]) < pd.Timestamp(year = year  + 1, month = 1, day = 1)] # Filter match_data for matches before January 1st of the current year
            summer_stats = transfer_stats_year[transfer_stats_year["window"] == "summer"] # Get summer transfer stats for the current year
            matches_before_winter = pd.merge(matches_before_winter, summer_stats, left_on=["Season", "Team"], right_on=["season", "club"], how="left") # Merge match_before_winter with summer_stats on season and club
    
            matches_after_winter = match_data_year[pd.to_datetime(match_data_year["Date"]) >= pd.Timestamp(year = year + 1, month = 1, day = 1)] # Filter match_data for matches on or after January 1st of the current year
            winter_stats = transfer_stats_year[transfer_stats_year["window"] == "winter"] # Get winter transfer stats for the current year
            matches_after_winter = pd.merge(matches_after_winter, winter_stats, left_on=["Season", "Team"], right_on=["season", "club"], how="left") # Merge match_after_winter with winter_stats on season and club

            merged_data_year = pd.concat([matches_before_winter, matches_after_winter], ignore_index=True)
            merged_matches_data = pd.concat([merged_matches_data, merged_data_year], ignore_index=True)
        merged_matches_data.drop(columns = ["season", "club", "window"], inplace = True)

        # Define helper function to aggregate match performance results over a specified time frame (e.g., 10 matches at the end of the previous season, 10 matches at beginning of current season)
        def agg_match_features(data, prefix):
            return (
                data.groupby(["Season", "Team"])
                .agg(
                    **{
                        f"{prefix}_Avg_Win_Percentage": ("Win_Percentage", "mean"),
                        f"{prefix}_Avg_Draw_Percentage": ("Draw_Percentage", "mean"),
                        f"{prefix}_Avg_Loss_Percentage": ("Loss_Percentage", "mean"),
                        f"{prefix}_Avg_Goals": ("Goals", "mean"),
                        f"{prefix}_Avg_Shots": ("Shots", "mean"),
                        f"{prefix}_Avg_SOT": ("Shots_on_Target", "mean"),
                        f"{prefix}_Avg_Opp_Goals": ("Opp_Goals", "mean"),
                        f"{prefix}_Avg_Opp_Shots": ("Opp_Shots", "mean"),
                        f"{prefix}_Avg_Opp_SOT": ("Opp_Shots_on_Target", "mean"),
                        f"{prefix}_Avg_xG": ("xG", "mean"),
                        f"{prefix}_Avg_xGA": ("xGA", "mean"),
                        f"{prefix}_Avg_npxG": ("npxG", "mean"),
                        f"{prefix}_Avg_npxGA": ("npxGA", "mean"),
                        f"{prefix}_Avg_Deep": ("Deep", "mean"),
                        f"{prefix}_Avg_Deep_Allowed": ("Deep_Allowed", "mean"),
                        f"{prefix}_Expected_Points": ("Expected_Points", "sum"),
                        f"{prefix}_Points": ("Points", "sum"),
                    }
                )
                .reset_index()
            )

        matches = merged_matches_data.copy() # Crate copy of merged matches with transfer data for manipulation
        previous_matches = matches.groupby(["Season", "Team"]).tail(PREV_MATCHES)  # Last 10 matches of every club-season
        current_matches = matches[matches["Season"] >= STARTING_YR + 1].groupby(["Season", "Team"]).head(CURR_MATCHES)  # First 10 matches of every club-season

        # Generate match performance results for each match window from agg_match_features helper 
        prev_prefix = "Prev"
        curr_prefix = "Curr"
        prev_match_features = agg_match_features(previous_matches, prev_prefix)
        curr_match_features = agg_match_features(current_matches, curr_prefix)

        # Create a column that represents each team's total points from the previous season
        points_lookup = season_results.set_index(["Season", "Team"])["Total_Points"]
        curr_match_features["Prev_Total_Points"] = curr_match_features.apply(
            lambda x: points_lookup.get((x["Season"] - 1, x["Team"]), np.nan), axis=1
        )

        # Create a column that represents each team's total points during the current season, this will represent our repsonse variable for predicting end of season point results for teams based on our predictors
        curr_match_features["EOS_Total_Points"] = curr_match_features.apply(
            lambda x: points_lookup.get((x["Season"], x["Team"]), np.nan), axis=1
        )

        prev_match_features["Merge_Season"] = prev_match_features["Season"] + 1 # Create label to support proper merging of match performance across the prior and current seasons of each observation
        season_avg_pts = season_results.groupby("Season")["Total_Points"].mean().reset_index()

        match_cols = ['Prev_Avg_Win_Percentage', 'Prev_Avg_Draw_Percentage',
               'Prev_Avg_Loss_Percentage', 'Prev_Avg_Goals', 'Prev_Avg_Shots',
               'Prev_Avg_SOT', 'Prev_Avg_Opp_Goals', 'Prev_Avg_Opp_Shots',
               'Prev_Avg_Opp_SOT', 'Prev_Avg_xG', 'Prev_Avg_xGA', 'Prev_Avg_npxG',
               'Prev_Avg_npxGA', 'Prev_Avg_Deep', 'Prev_Avg_Deep_Allowed',
               'Prev_Expected_Points', 'Prev_Points']
        prev_match_avg_performance = prev_match_features.groupby("Season")[match_cols].mean() # Compute the average match performance in terms of the specified columns to use a replacements for recently promoted teams who will have no previous season match data

        # Merge the current season aggregated match performance with the previous season aggregated match performance, both in terms of 10 matches (adjust constants at top of notebook to modify)
        merged_season_data = pd.merge(
            curr_match_features,
            prev_match_features,
            left_on=["Season", "Team"],
            right_on=["Merge_Season", "Team"],
            how="left",
        )

        # Fill empty entries for recently promoted team's previous season match performance with mean results computed as prev_match_avg_performance
        merged_season_data["Promoted"] = np.where(merged_season_data["Prev_Points"].isna(), 1, 0) # Assign promoted label for sides promoted to the EPL for that season
        for col in match_cols:
            merged_season_data[col] = merged_season_data[col].fillna(
                (merged_season_data["Season_x"] - 1).map(
                    prev_match_avg_performance[col]
                )
            )
        merged_season_data["Prev_Total_Points"] = merged_season_data["Prev_Total_Points"].fillna(
            (merged_season_data["Season_x"] - 1).map(
                season_avg_pts.set_index("Season")["Total_Points"]
            )
        )

        transfers = transfer_stats.copy()
        transfers = transfers[transfers["window"] == "summer"]  # Isolate transfer results for each summer transfer window for proper merging
        transfers.drop(columns="window", inplace=True)

        # Merge transfer data for each summer transfer window with the merged match performance data, resulting in observations that each represent 
        # a team's average performance across the last 10 matches of the previous season, their average performance across the first 10 matches of the 
        # current season, and their transfer window activity during the summer window in between the last season and current season. 
        final_merged_data = pd.merge(merged_season_data, transfers, left_on = ["Season_x", "Team"], right_on = ["season", "club"], how = "left")

        removed_cols = ["season", "club", "Merge_Season", "Season_y"]
        final_merged_data.drop(columns = removed_cols, inplace = True)
        final_merged_data.rename(columns={"Season_x": "Season"}, inplace = True)
        final_merged_data.columns = list(final_merged_data.columns[:len(merged_season_data.columns) - len(removed_cols)]) + list(final_merged_data.columns[(len(merged_season_data.columns) - len(removed_cols)):].str.title())
        return final_merged_data
