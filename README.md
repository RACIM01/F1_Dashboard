#F1-Dashboard

Built an F1 Performance Dashboard using FastF1 to collect and process race data. Designed a structured data model and exported datasets into CSV files. Developed an interactive Power BI dashboard to visualize driver performance, lap times, race results, and key Formula 1 insights.



# 🏎️ F1 Performance Dashboard

## Overview

The F1 Performance Dashboard is a data analytics project that transforms Formula 1 data into interactive and actionable insights.

Using the FastF1 Python library, race, qualifying, and lap-by-lap data are collected, processed, and exported into structured CSV files. These datasets are then integrated into Power BI to build an interactive dashboard that enables performance analysis across drivers, teams, races, and seasons.

The project demonstrates the complete analytics workflow, from data extraction and modeling to business intelligence reporting and visualization.

---

## Project Objectives

- Collect Formula 1 data using FastF1.
- Process and clean raw datasets.
- Design a structured analytical data model.
- Export datasets into CSV files.
- Build an interactive Power BI dashboard.
- Analyze driver, team, and race performance.

---

## Tech Stack

| Technology | Purpose |
|------------|----------|
| Python | Data extraction and transformation |
| FastF1 | Formula 1 data collection |
| Pandas | Data cleaning and processing |
| CSV Files | Data storage |
| Power BI | Data visualization and reporting |

---

## Data Pipeline

### Data Extraction

Formula 1 data is collected using the FastF1 library through Python scripts and Jupyter notebooks.

### Data Transformation

The extracted data is cleaned, transformed, and exported into CSV files:

- F1_Corners.csv
- Qualifying_telemetry.csv
- Qualifying.csv
- Race.csv
- Races.csv
- Team.csv
- weather.csv

### Data Visualization

The CSV datasets are imported into Power BI to create an interactive dashboard that provides insights into:

- Driver performance
- Team performance
- Qualifying sessions
- Race results
- Telemetry analysis
- Weather conditions

## Data Model

A relational data model was designed to support efficient reporting and analysis.

The model connects key Formula 1 entities such as drivers, teams, races, sessions, results, and lap data, allowing users to explore performance metrics from multiple perspectives.

### Data Model Schema

<img width="771" height="861" alt="F1_Dashboard_data_schema" src="https://github.com/user-attachments/assets/213802c2-27a1-4e3c-b476-648fb158dc47" />


---

## Dashboard Features

### Driver Performance Analysis

- Driver standings
- Wins and podiums
- Points evolution
- Average finishing position
- Performance trends

### Team Performance Analysis

- Constructor standings
- Team points comparison
- Driver contribution analysis
- Season performance tracking

### Qualifying Analysis

- Pole positions
- Grid position analysis
- Q1, Q2, and Q3 performance
- Qualifying trends

### Race Analysis

- Race results
- Position changes
- Fastest laps
- Event comparisons

### Lap Time Analysis

- Best lap times
- Average race pace
- Sector performance
- Lap-by-lap comparisons

---

## Dashboard Screenshots

### Overview Dashboard


<img width="1419" height="798" alt="image" src="https://github.com/user-attachments/assets/a9c4b922-e969-4241-96b3-b54e773088ac" />


### Race Analysis Dashboard


<img width="1426" height="800" alt="image" src="https://github.com/user-attachments/assets/a1693448-9696-4cf1-b47a-e16b715cfd80" />


### Qualifying Analysis Dashboard

<img width="1425" height="801" alt="image" src="https://github.com/user-attachments/assets/5b95a731-3262-43f4-b28c-51adbc045d06" />


### Team Performance Dashboard

<img width="1421" height="801" alt="image" src="https://github.com/user-attachments/assets/3700679f-c521-4e98-8732-b36e0d4959d8" />




---

## Key Insights

This dashboard enables users to:

- Compare drivers across multiple seasons.
- Evaluate team performance trends.
- Analyze race and qualifying results.
- Identify top-performing drivers and teams.
- Explore detailed lap-by-lap performance metrics.

---

## Project Structure

```text
F1-Dashboard
│
├── Data
│   ├── F1_Corners.csv
│   ├── Qualifying_telemetry.csv
│   ├── Qualifying.csv
│   ├── Race.csv
│   ├── Races.csv
│   ├── Team.csv
│   └── weather.csv
│
├── PowerBI DashBoard
│   ├── F1_Dashboard.pbix
│   ├── 2529971.png
│   ├── 3089050.png
│   ├── 6393411.png
│   ├── Sky.jpg
│   └── weather-icon.webp
│
├── DataLoad.py
├── main.ipynb
├── .gitignore
└── README.md
```
---

## Future Improvements

- Real-time data refresh
- Advanced telemetry analysis
- Tire strategy analysis
- Pit stop performance analysis
- Driver head-to-head comparisons
- Predictive analytics and machine learning models

---

## Author

**Racim Chaibi**

Data Analytics Project using FastF1, Python, and Power BI.
