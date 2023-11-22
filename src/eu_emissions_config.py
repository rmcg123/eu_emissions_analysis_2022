"""Configuration settings for eu emissions analysis."""

import seaborn as sns

DATA_PATH = "data/"
RESULTS_PATH = "results/"

FILE_NAME = "GHG_proxy_2022.xlsx"
SHEET_NAME = "EEA proxy dataset (plus)"

COUNTRY_CODE_MAPPINGS = {
    "EL": "GR",
}

GAS_SCOPE_SUMMARY = "Total"
CRF_CODE_SUMMARY = "Total_net"

COUNTRY_EXCLUDES = ["EU27"]

EMISSIONS_COLUMN = "emissions_-_eea_[kt]"

OVERALL_SECTOR_CODES = ["1", "2", "3", "4", "5", "6"]
ENERGY_SECTOR_CODES = [
    "1.A.1",
    "1.A.2",
    "1.A.3",
    "1.A.4",
    "1.A.5",
    "1.B",
    "1.C",
    "1.D.1.a",
    "1.D.1.b",
]
INDUSTRIAL_SECTOR_CODES = [
    "2.A",
    "2.B",
    "2.C",
    "2.D",
    "2.E",
    "2.F",
    "2.G",
    "2.H",
]
AGRICULTURE_SECTOR_CODES = [
    "3.A",
    "3.B",
    "3.C",
    "3.D",
    "3.E",
    "3.F",
    "3.G",
    "3.H",
    "3.I",
    "3.J",
]
LULUCF_SECTOR_CODES = ["4.A", "4.B", "4.C", "4.D", "4.E", "4.F", "4.G", "4.H"]
WASTE_SECTOR_CODES = ["5.A", "5.B", "5.C", "5.D", "5.E"]

SECTOR_DICTIONARIES = {
    "Overall": dict(
        zip(
            OVERALL_SECTOR_CODES,
            sns.color_palette("Dark2", n_colors=len(OVERALL_SECTOR_CODES)),
        )
    ),
    "Energy": dict(
        zip(
            ENERGY_SECTOR_CODES,
            sns.color_palette("Set1", n_colors=len(ENERGY_SECTOR_CODES)),
        )
    ),
    "Industrial Processes and Product Use": dict(
        zip(
            INDUSTRIAL_SECTOR_CODES,
            sns.color_palette("Set3", n_colors=len(INDUSTRIAL_SECTOR_CODES)),
        )
    ),
    "Agriculture": dict(
        zip(
            AGRICULTURE_SECTOR_CODES,
            sns.color_palette(
                "Paired", n_colors=len(AGRICULTURE_SECTOR_CODES)
            ),
        )
    ),
    "Land Use, Land-Use Change and Forestry": dict(
        zip(
            LULUCF_SECTOR_CODES,
            sns.color_palette("Accent", n_colors=len(LULUCF_SECTOR_CODES)),
        )
    ),
    "Waste": dict(
        zip(
            WASTE_SECTOR_CODES,
            sns.color_palette("Set2", n_colors=len(WASTE_SECTOR_CODES)),
        )
    ),
}
