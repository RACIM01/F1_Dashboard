import fastf1
import fastf1.plotting

# import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from openpyxl.styles import PatternFill
from openpyxl import Workbook
from openpyxl import load_workbook
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from matplotlib.pyplot import figure
from matplotlib.collections import LineCollection
from matplotlib import cm
from scipy.interpolate import make_interp_spline
from fastf1 import utils
from statistics import mean
from scipy import stats
import os
import matplotlib.font_manager as fm
import matplotlib as mpl
import warnings

warnings.filterwarnings("ignore")

# fonction pour enregistrer le DataFrame dans un fichier CSV


def save_to_csv(df, csv_laps_path):
    """this function saves the provided DataFrame to a CSV file at the specified path.
    If the file does not exist, it creates a new one with headers. If the file exists,
    it checks for duplicates

    Args:
        df (DataFrame): the data to be saved
        csv_laps_path (Char): the path to the CSV file
    """
    race_id_numeric = df["Race_id"].iloc[0]  # Assuming all rows in

    # creation of the CSV file if it doesn't exist
    if not os.path.exists(csv_laps_path):
        # Si le fichier n'existe pas encore, on le crée de zéro avec les en-têtes
        df.to_csv(csv_laps_path, sep=";", decimal=",", index=False)
        print(
            f"Création du fichier {csv_laps_path} avec succès pour le Race_id : {race_id_numeric}"
        )
    else:
        # if the file exists, we use "pandas.read_csv" with your separators to read the existing
        df_existing_laps = pd.read_csv(csv_laps_path, sep=";", decimal=",")

        # we check if the current race (race_id numeric) is already present
        if race_id_numeric in df_existing_laps["Race_id"].values:
            print(
                f"Les données pour le Race_id {race_id_numeric} sont déjà enregistrées dans {csv_laps_path}. Pas de doublon créé."
            )
        else:
            # security to ensure a proper newline at the end of the file before writing
            with open(csv_laps_path, "r+", encoding="utf-8") as f:
                f.seek(0, os.SEEK_END)
                if f.tell() > 0:
                    f.seek(f.tell() - 1)
                    if f.read(1) != "\n":
                        f.write("\n")

            df.to_csv(
                csv_laps_path, mode="a", header=False, sep=";", decimal=",", index=False
            )
            print(
                f"Nouvelle course ({race_id_numeric}) ajoutée avec succès dans {csv_laps_path} !"
            )


def load_corners(session, race_id_numeric):
    circuit_info = session.get_circuit_info()
    corners_df = circuit_info.corners[["Number", "X", "Y"]].copy()
    corners_df = corners_df.rename(
        columns={"Number": "Corner_Number", "X": "Corner_X", "Y": "Corner_Y"}
    )
    corners_df["Race_id"] = race_id_numeric
    corners_df = corners_df[["Race_id", "Corner_Number", "Corner_X", "Corner_Y"]]
    save_to_csv(corners_df, "Data/F1_Corners.csv")


def load_race(race, ses, year):

    session = fastf1.get_session(year, race, ses)
    session.load()
    fastf1.Cache.enable_cache("cache")

    laps = session.laps
    df = laps.copy()
    df["LapTimeSec"] = df["LapTime"].dt.total_seconds()
    df["Sector1TimeSec"] = df["Sector1Time"].dt.total_seconds()
    df["Sector2TimeSec"] = df["Sector2Time"].dt.total_seconds()
    df["Sector3TimeSec"] = df["Sector3Time"].dt.total_seconds()
    df.drop(
        ["LapTime", "Sector1Time", "Sector2Time", "Sector3Time"], axis=1, inplace=True
    )
    df.replace(np.nan, 0, inplace=True)
    df["LapStartTimeS"] = df["LapStartTime"].dt.total_seconds().astype(float)

    # Identifying the winner of the race
    winner_search = df.loc[
        (df["LapNumber"] == max(df["LapNumber"])) & (df["Position"] == 1),
        "DriverNumber",
    ]
    winner = (
        winner_search.values[0]
        if not winner_search.empty
        else df["DriverNumber"].unique()[0]
    )

    drivers = df["DriverNumber"].unique()

    df["GapToLeader"] = np.nan

    # calculate the gap to the leader for each driver and each lap
    for driver_num in drivers:
        # On extrait les temps de passage du pilote en cours et du vainqueur
        driver_laps = df[df["DriverNumber"] == driver_num].sort_values("LapNumber")
        winner_laps = df[df["DriverNumber"] == winner].sort_values("LapNumber")

        # On aligne les index par le numéro de tour (LapNumber) pour éviter les décalages
        driver_laps = driver_laps.set_index("LapNumber")
        winner_laps = winner_laps.set_index("LapNumber")

        # Calcul de la différence sur le temps de passage cumulé (en secondes)
        gap_series = driver_laps["LapStartTimeS"] - winner_laps["LapStartTimeS"]

        # On réinjecte les valeurs calculées dans le DataFrame principal 'df'
        for lap, gap_value in gap_series.items():
            if not pd.isna(gap_value):
                # Sécurité : évite les valeurs négatives (-0.001s) dues aux arrondis pour le vainqueur lui-même
                df.loc[
                    (df["DriverNumber"] == driver_num) & (df["LapNumber"] == lap),
                    "GapToLeader",
                ] = max(0.0, gap_value)

    # replace NaN values in the "GapToLeader" column with 0 for drivers who didn't complete any laps
    df["GapToLeader"] = df["GapToLeader"].fillna(0)

    df["V_max"] = np.nan
    max_lap_race = int(df["LapNumber"].max())

    # loop through each driver and each lap to calculate the maximum speed
    for i in drivers:
        # On vérifie si le pilote a des tours enregistrés
        if df.loc[df["DriverNumber"] == i].empty:
            continue

        # On filtre les pilotes DNF (qui ont fait moins de 75% de la course)
        elif df.loc[df["DriverNumber"] == i, "LapNumber"].max() < max_lap_race * 0.75:
            continue

        else:
            for j in range(0, max_lap_race + 1):
                # Cibler le tour j pour le pilote i
                mask_lap = (df["LapNumber"] == j) & (df["DriverNumber"] == i)
                lap_i = df.loc[mask_lap]

                if not lap_i.empty:
                    try:
                        # Récupération de la télémétrie du tour
                        car_data = lap_i.get_car_data()
                        if not car_data.empty:
                            max_speed = car_data["Speed"].max()

                            # Injection de la vitesse max directement dans la bonne ligne du df
                            df.loc[mask_lap, "V_max"] = max_speed
                    except Exception as e:
                        # Gestion des lignes/tours sans télémétrie
                        print(f"Pas de télémétrie pour le pilote {i} au tour {j}: {e}")

    # removing NaN values in the "V_max" column and replacing them with 0
    df["V_max"] = df["V_max"].fillna(0)

    event = session.event
    round_str = f"{race:02d}"
    session_name = session.session_info[
        "Name"
    ]  # Renvoie 'FP1', 'Qualifying', 'Race', etc.
    race_id_numeric = int(f"{year}{round_str}{ses}")
    df["Race_id"] = race_id_numeric
    df = df[
        [
            "Time",
            "Race_id",
            "Driver",
            "DriverNumber",
            "LapNumber",
            "Stint",
            "IsPersonalBest",
            "Compound",
            "TyreLife",
            "FreshTyre",
            "Team",
            "LapStartTime",
            "Position",
            "Deleted",
            "IsAccurate",
            "LapTimeSec",
            "Sector1TimeSec",
            "Sector2TimeSec",
            "Sector3TimeSec",
            "GapToLeader",
            "V_max",
        ]
    ]

    # add the new race to the table Races.csv
    new_race_data = {
        "Race_id": [race_id_numeric],
        "Year": [int(year)],
        "Round": [race],
        "RaceName": [event["EventName"]],
        "Country": [event["Country"]],
        "Session": [session_name],
    }
    df_new_race = pd.DataFrame(new_race_data)

    # getting the weather data for the session and adding it to the DataFrame
    weather = session.weather_data
    race_id_numeric = int(f"{year}{round_str}{ses}")
    weather["Race_id"] = race_id_numeric
    weather = weather[
        [
            "Race_id",
            "Time",
            "AirTemp",
            "Humidity",
            "Pressure",
            "Rainfall",
            "TrackTemp",
            "WindDirection",
            "WindSpeed",
        ]
    ]

    save_to_csv(df, "Data/Race.csv")
    save_to_csv(df_new_race, "Data/Races.csv")
    save_to_csv(weather, "Data/Weather.csv")
    load_corners(session, race_id_numeric)


# function to safely extract speeds from a lap object, handling potential errors and ensuring compatibility with FastF1's data structures
def get_speeds(lap_obj):
    try:
        # Comme votre code utilise parfois .T, on s'assure de récupérer le tour au bon format pour FastF1
        if isinstance(lap_obj, pd.DataFrame):
            lap_obj = lap_obj.iloc[:, 0] if lap_obj.shape[1] > 0 else lap_obj.iloc[0]

        car_data = lap_obj.get_car_data()
        if not car_data.empty and "Speed" in car_data.columns:
            return (
                round(car_data["Speed"].min(), 1),
                round(car_data["Speed"].mean(), 1),
                round(car_data["Speed"].max(), 1),
            )
    except:
        pass
    return np.nan, np.nan, np.nan


couleurs_pneus = {
    "SOFT": "#E10600",  # Rouge
    "MEDIUM": "#FFF200",  # Jaune
    "HARD": "#CCCCCC",  # Gris/Blanc
    "INTERMEDIATE": "#39B54A",  # Vert
    "WET": "#00AEEF",  # Bleu
}


def load_qualifying(race, ses, year):

    session = fastf1.get_session(year, race, ses)
    session.load()

    laps = session.laps
    qualifying = laps.copy()

    qualifying["LapTimeSec"] = qualifying["LapTime"].dt.total_seconds()
    qualifying["Sector1TimeSec"] = qualifying["Sector1Time"].dt.total_seconds()
    qualifying["Sector2TimeSec"] = qualifying["Sector2Time"].dt.total_seconds()
    qualifying["Sector3TimeSec"] = qualifying["Sector3Time"].dt.total_seconds()
    qualifying.sort_values("LapTimeSec", inplace=True)

    q1, q2, q3 = qualifying.split_qualifying_sessions()
    q1_results = qualifying.iloc[0:0].copy()
    q2_results = qualifying.iloc[0:0].copy()
    q3_results = qualifying.iloc[0:0].copy()
    y = 0
    if year == 2026:
        elim_q = 17
    else:
        elim_q = 16

    for i in q1["DriverNumber"].unique():
        y += 1

        # SÉQUENCE Q1
        if q1.pick_driver(i).empty == False:  # & (y > elim_q1)
            if (
                q1.pick_driver(i).pick_fastest() is None
            ):  # q1.pick_driver(i).pick_fastest().isna().all()
                lap_df = q1.pick_driver(i).pick_lap(
                    q1.pick_driver(i)["LapNumber"].min()
                )
            else:
                lap = q1.pick_driver(i).pick_fastest()
                lap_df = q1.loc[q1["Time"] == lap[0]]

            # --- AJOUT DES 3 COLONNES ---

            lap_df["Speed_MIN"], lap_df["Speed_AVG"], lap_df["Speed_MAX"] = get_speeds(
                lap
            )
            q1_results = pd.concat([q1_results, lap_df], ignore_index=True)
            # ----------------------------

        # SÉQUENCE Q2
        if q2.pick_driver(i).empty == False:
            if q2.pick_driver(i).pick_fastest() is None:
                lap_df = q2.pick_driver(i).pick_lap(
                    q2.pick_driver(i)["LapNumber"].min()
                )
            else:
                lap = q2.pick_driver(i).pick_fastest()
                lap_df = q2.loc[q2["Time"] == lap[0]]

            lap_df["Speed_MIN"], lap_df["Speed_AVG"], lap_df["Speed_MAX"] = get_speeds(
                lap
            )
            q2_results = pd.concat([q2_results, lap_df], ignore_index=True)
            # ----------------------------

        # SÉQUENCE Q3
        if q3.pick_driver(i).empty == False:
            if q3.pick_driver(i).pick_fastest() is None:
                lap_df = q3.pick_driver(i).pick_lap(
                    q3.pick_driver(i)["LapNumber"].min()
                )
            else:
                lap = q3.pick_driver(i).pick_fastest()
                lap_df = q3.loc[q3["Time"] == lap[0]]

            lap_df["Speed_MIN"], lap_df["Speed_AVG"], lap_df["Speed_MAX"] = get_speeds(
                lap
            )
            q3_results = pd.concat([q3_results, lap_df], ignore_index=True)
            # ----------------------------

    q1_results.sort_values(by=["LapTimeSec"], inplace=True)
    q1_results.reset_index(drop=True, inplace=True)
    q2_results.sort_values(by=["LapTimeSec"], inplace=True)
    q2_results.reset_index(drop=True, inplace=True)
    q3_results.sort_values(by=["LapTimeSec"], inplace=True)
    q3_results.reset_index(drop=True, inplace=True)

    results_qualifying = pd.concat(
        [
            q3_results,
            q2_results.iloc[10 : elim_q - 1, :],
            q1_results.iloc[elim_q - 1 : 23, :],
        ],
        ignore_index=True,
    ).reset_index(drop=True)

    # # calculate gap to P1
    # results_qualifying['LapTimeSec'] = results_qualifying['LapTimeSec'].fillna((results_qualifying["LapTimeSec"].min()+40))
    # results_qualifying['LapTimeSec']
    results_qualifying["DeltaTime"] = (
        results_qualifying["LapTimeSec"] - results_qualifying["LapTimeSec"][0]
    )
    diff = (
        results_qualifying.loc[results_qualifying["DeltaTime"] > 7, ["LapTimeSec"]]
        - results_qualifying.loc[
            results_qualifying["DeltaTime"] > 7, ["DeltaTime"]
        ].values
    )
    results_qualifying.loc[results_qualifying["DeltaTime"] > 7, ["LapTimeSec"]] = diff

    results_qualifying["LapTimeSec"] = results_qualifying["LapTimeSec"] - 60

    results_qualifying["Compound_c"] = (
        results_qualifying["Compound"]
        .astype(str)
        .str.upper()
        .map(couleurs_pneus)
        .fillna("#808080")
    )
    results_qualifying.replace(np.nan, 0, inplace=True)
    # results_qualifying.sort_values(by=['LapTime'], inplace=True)
    results_qualifying = results_qualifying.loc[
        results_qualifying["IsAccurate"] == True
    ]
    results_qualifying["Position"] = results_qualifying.index + 1

    event = session.event
    round_str = f"{race:02d}"
    session_name = session.session_info["Name"]
    current_year = year
    race_id_numeric = int(f"{current_year}{round_str}{4}")
    results_qualifying["Race_id"] = race_id_numeric
    results_qualifying = results_qualifying[
        [
            "Time",
            "Race_id",
            "Driver",
            "DriverNumber",
            "LapTime",
            "LapNumber",
            "Stint",
            "IsPersonalBest",
            "Compound",
            "TyreLife",
            "FreshTyre",
            "Team",
            "LapStartTime",
            "LapStartDate",
            "Position",
            "Deleted",
            "IsAccurate",
            "LapTimeSec",
            "Sector1TimeSec",
            "Sector2TimeSec",
            "Sector3TimeSec",
            "Speed_MIN",
            "Speed_AVG",
            "Speed_MAX",
            "DeltaTime",
            "Compound_c",
        ]
    ]

    new_race_data = {
        "Race_id": [race_id_numeric],
        "Year": [year],
        "Round": [race],
        "RaceName": [event["EventName"]],
        "Country": [event["Country"]],
        "Session": [session_name],
    }
    df_new_race = pd.DataFrame(new_race_data)

    ### loading telemetry data for each driver and each lap
    driverss = results_qualifying["DriverNumber"].head(3).astype(int).to_list()

    laps_driver1 = laps.pick_drivers(driverss[0]).copy()
    laps_driver2 = laps.pick_drivers(driverss[1]).copy()
    laps_driver3 = laps.pick_drivers(driverss[2]).copy()

    # Get the telemetry data from their fastest lap
    fastest_driver1 = laps_driver1.pick_fastest().get_telemetry()
    fastest_driver2 = laps_driver2.pick_fastest().get_telemetry()
    fastest_driver3 = laps_driver3.pick_fastest().get_telemetry()

    # Since the telemetry data does not have a variable that indicates the driver,
    # we need to create that column
    fastest_driver1["Driver"] = session.get_driver(str(driverss[0]))["Abbreviation"]
    fastest_driver2["Driver"] = session.get_driver(str(driverss[1]))["Abbreviation"]
    fastest_driver3["Driver"] = session.get_driver(str(driverss[2]))["Abbreviation"]

    # Merge both lap telemetries so we have everything in one DataFrame
    telemetry = pd.concat([fastest_driver1, fastest_driver2, fastest_driver3])
    # telemetry = fastest_driver1.append(fastest_driver2)
    # telemetry = telemetry.append(fastest_driver3)

    # We want 25 mini-sectors (this can be adjusted up and down)
    num_minisectors = 25

    # Grab the maximum value of distance that is known in the telemetry
    total_distance = telemetry["Distance"].max()

    # Generate equally sized mini-sectors
    minisector_length = total_distance / num_minisectors
    # Initiate minisector variable, with 0 (meters) as a starting point.
    minisectors = [0]

    # Add multiples of minisector_length to the minisectors
    for i in range(0, (num_minisectors - 1)):
        minisectors.append(minisector_length * (i + 1))

    telemetry["Minisector"] = telemetry["Distance"].apply(
        lambda dist: (int((dist // minisector_length) + 1))
    )

    # Calculate avg. speed per driver per mini sector
    average_speed = (
        telemetry.groupby(["Minisector", "Driver"])["Speed"].mean().reset_index()
    )
    # Select the driver with the highest average speed
    fastest_driver = average_speed.loc[
        average_speed.groupby(["Minisector"])["Speed"].idxmax()
    ]

    # Get rid of the speed column and rename the driver column
    fastest_driver = fastest_driver[["Minisector", "Driver"]].rename(
        columns={"Driver": "Fastest_driver"}
    )

    # Join the fastest driver per minisector with the full telemetry
    telemetry = telemetry.merge(fastest_driver, on=["Minisector"])

    # Order the data by distance to make matploblib does not get confused
    telemetry = telemetry.sort_values(by=["Distance"])

    # Convert driver name to integer
    telemetry.loc[
        telemetry["Fastest_driver"]
        == session.get_driver(str(driverss[0]))["Abbreviation"],
        "Fastest_driver_int",
    ] = 1
    telemetry.loc[
        telemetry["Fastest_driver"]
        == session.get_driver(str(driverss[1]))["Abbreviation"],
        "Fastest_driver_int",
    ] = 2
    telemetry.loc[
        telemetry["Fastest_driver"]
        == session.get_driver(str(driverss[2]))["Abbreviation"],
        "Fastest_driver_int",
    ] = 3

    custom_colors = [
        fastf1.plotting.get_team_color(
            session.get_driver(str(driverss[0]))["TeamName"], session
        ),
        fastf1.plotting.get_team_color(
            session.get_driver(str(driverss[1]))["TeamName"], session
        ),
        fastf1.plotting.get_team_color(
            session.get_driver(str(driverss[2]))["TeamName"], session
        ),
    ]

    telemetry["Driver_color"] = telemetry["Fastest_driver_int"].apply(
        lambda x: custom_colors[int(x) - 1]
    )
    telemetry["Race_id"] = race_id_numeric
    telemetry = telemetry[
        [
            "Date",
            "Race_id",
            "Time",
            "Distance",
            "RelativeDistance",
            "X",
            "Y",
            "Z",
            "Driver",
            "Minisector",
            "Fastest_driver",
            "Fastest_driver_int",
            "Driver_color",
        ]
    ]

    save_to_csv(results_qualifying, "Data/Qualifying.csv")
    save_to_csv(df_new_race, "Data/Races.csv")
    save_to_csv(telemetry, "Data/Qualifying_telemetry.csv")


## start code execution


for race in range(1, 8):
    load_qualifying(race, 4, 2026)
