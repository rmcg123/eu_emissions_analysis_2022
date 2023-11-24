"""Main script for EU emissions analysis."""
import os

from matplotlib import rcParams
import pandas as pd
import numpy as np
import seaborn as sns
import pypopulation as pyp
from textwrap import wrap

import src.eu_emissions_config as cfg
import src.eu_emissions_functions as euf

rcParams["font.family"] = "Serif"
rcParams["figure.figsize"] = (16, 9)
rcParams["figure.dpi"] = 300
rcParams["axes.titlesize"] = 24
rcParams["axes.labelsize"] = 18
rcParams["font.size"] = 16
rcParams["xtick.labelsize"] = 16
rcParams["ytick.labelsize"] = 14
rcParams["legend.fontsize"] = 12
rcParams["legend.title_fontsize"] = 16


def create_emissions_per_capita(
    emissions_df,
    emissions_col,
    country_code_mappings,
):
    """Create an emissions per capita column using country population data."""

    # Map non alpha-2 country codes to alpha-2.
    emissions_df["country_code"] = (
        emissions_df["country_code"]
        .map(country_code_mappings)
        .fillna(emissions_df["country_code"])
    )

    # Get all unique country codes.
    countries = list(
        emissions_df.loc[
            ~emissions_df["country_code"].isin(cfg.COUNTRY_EXCLUDES),
            "country_code",
        ].unique()
    )

    # Use pypopulation to get populations for each alpha-2 code.
    country_population_dict = {}
    for country in countries:
        country_population_dict[country] = pyp.get_population_a2(country)

    # Create population column.
    emissions_df["population"] = emissions_df["country_code"].map(
        country_population_dict
    )

    # Create emissions per capita column, measured in tonnes CO2.
    emissions_df["emissions_per_capita"] = np.where(
        emissions_df["population"].notnull(),
        1e6 * emissions_df[emissions_col] / emissions_df["population"],
        np.nan,
    )

    return emissions_df


def create_overall_barplot(emissions_df, emissions_col, save_dir):
    """Function to create an overall barplot showing the emissions by
    country."""

    # Select all relevant country summaries.
    country_overall_emissions = emissions_df.loc[
        emissions_df["gas_scope"].eq(cfg.GAS_SCOPE_SUMMARY)
        & emissions_df["crf_code"].eq(cfg.CRF_CODE_SUMMARY)
        & ~emissions_df["country_code"].isin(cfg.COUNTRY_EXCLUDES)
    ]

    # Determine order for plot from most to least.
    country_emissions_order = country_overall_emissions.sort_values(
        by=emissions_col, ascending=False
    )["country_name"].to_list()

    if emissions_col == "emissions_per_capita":
        save_name = "emissions_per_capita_2022.png"
    else:
        save_name = "emissions_2022.png"

    # Create barplot.
    _, _ = euf.plot_basic_barplot(
        emissions_df=country_overall_emissions,
        emissions_col=emissions_col,
        group_col="country_name",
        order=country_emissions_order,
        save_dir=save_dir,
        save_name=save_name,
    )

    return country_emissions_order


def create_emissions_by_gas(emissions_df, emissions_col, statistic, save_dir):
    """Create a stacked barplot of emissions split by country and stacked by
    gas."""

    # Select the emissions for each gas for each country.
    gas_emissions = emissions_df.loc[
        emissions_df["crf_code"].eq(cfg.CRF_CODE_SUMMARY)
        & ~emissions_df["country_code"].isin(cfg.COUNTRY_EXCLUDES)
        & ~emissions_df["gas_scope"].eq(cfg.GAS_SCOPE_SUMMARY)
    ].reset_index(drop=True)

    # Set up labels, titles, save names.
    if emissions_col == "emissions_per_capita":
        ylabel = "Emissions per Capita"
        units = ", tonnes CO\u2082 eq."
        save_name = "emissions_per_capita_by_gas_2022.png"
        title = "Emissions per Capita by Country and Gas (2022)"
    else:
        ylabel = "Emissions"
        units = ", Mt CO\u2082 eq."
        save_name = "emissions_by_gas_2022.png"
        title = "Emissions by Country and Gas (2022)"

    # If percentage share then calculate percentages.
    if statistic == "share":
        # For percentage shares only consider emissions, not any absorption.
        gas_emissions = gas_emissions.loc[
            gas_emissions[emissions_col].gt(0)
        ].reset_index(drop=True)

        # Determine the total emisssions for each country.
        country_totals = gas_emissions.groupby("country_code")[
            emissions_col
        ].sum()

        # Reshape and rename to facilitate concat.
        emissions_country_totals = (
            country_totals.loc[gas_emissions["country_code"].to_list()]
            .rename("country_total_emissions")
            .reset_index()
        )

        # Concatenate country emissions total
        gas_emissions = pd.concat(
            [
                gas_emissions,
                emissions_country_totals["country_total_emissions"],
            ],
            axis=1,
        )

        # Create emissions share columns.
        gas_emissions[emissions_col + "_share"] = (
            100
            * gas_emissions[emissions_col]
            / gas_emissions["country_total_emissions"]
        )

        # Adjust columns, labels, titles, save names.
        emissions_col = emissions_col + "_share"
        ylabel = "% Share of " + ylabel
        title = "% Share of " + title
        save_name = "pct_share_of_" + save_name
    else:
        ylabel = ylabel + units

    # Split long titles into multiple lines.
    title = "\n".join(wrap(title, 60, break_long_words=False))
    # Determine order for plot stacks.
    gas_emissions_order = (
        gas_emissions.groupby("gas_scope")[emissions_col]
        .sum()
        .sort_values(ascending=False)
        .index.to_list()
    )

    # Create stacked barplot.
    _, _ = euf.plot_stacked_barplot(
        emissions_df=gas_emissions,
        emissions_col=emissions_col,
        group_col="country_name",
        hue_col="gas_scope",
        hue_order=gas_emissions_order,
        palette=dict(
            zip(
                gas_emissions_order,
                sns.color_palette("tab10", n_colors=len(gas_emissions_order)),
            )
        ),
        save_dir=save_dir,
        save_name=save_name,
        title=title,
        ylabel=ylabel,
        statistic=statistic,
    )


def create_emissions_by_sector(
    emissions_df,
    emissions_col,
    sector,
    sector_codes,
    palette,
    statistic,
    save_dir,
):
    """Create stacked barplot of countries emissions stacked by sectors."""

    # Select sub-sector emissions for sector.
    sector_overall_emissions = emissions_df.loc[
        ~emissions_df["country_code"].isin(cfg.COUNTRY_EXCLUDES)
        & emissions_df["gas_scope"].eq(cfg.GAS_SCOPE_SUMMARY)
        & emissions_df["sector_code"].isin(sector_codes)
    ]

    # Clean up sector names.
    sector_overall_emissions["sector_name"] = (
        sector_overall_emissions["sector_name"]
        .str.split("-")
        .apply(lambda x: "-".join(x[1:]))
    )

    # Setup labels, titles, save name.
    if emissions_col == "emissions_per_capita":
        ylabel = "Emissions per Capita"
        units = ", tonnes CO\u2082 eq."
        save_name = f"emissions_per_capita_by_sector_{sector}_2022.png"
        title = (f"{sector.title()} Emissions per Capita by Country"
                 f" and Sub-Sector (2022)")
    else:
        ylabel = "Emissions"
        units = ", Mt CO\u2082 eq."
        save_name = f"emissions_by_sector_{sector}_2022.png"
        title = f"{sector.title()} Emissions by Country and Sub-Sector (2022)"

    # Determine ordering of each sector within stacks.
    sector_overall_emissions["abs_emissions"] = sector_overall_emissions[
        emissions_col
    ].apply(np.abs)
    sector_emissions_order = (
        sector_overall_emissions.groupby("sector_name")["abs_emissions"]
        .sum()
        .sort_values(ascending=False)
        .index.to_list()
    )

    # Determine palette colors for each sub-sector.
    palette_mapping = (
        sector_overall_emissions.groupby("sector_code")["sector_name"]
        .first()
        .to_dict()
    )
    palette = {palette_mapping[k]: v for k, v in palette.items()}

    # If percentage share of emissions then calculate shares.
    if statistic == "share":
        # Only consider emissions not absorption.
        sector_overall_emissions = sector_overall_emissions.loc[
            sector_overall_emissions[emissions_col].gt(0)
        ].reset_index(drop=True)

        # Calculate total emissions for each country.
        country_totals = sector_overall_emissions.groupby("country_code")[
            emissions_col
        ].sum()

        # Reshape and rename to facilitate concat.
        emissions_country_totals = (
            country_totals.loc[
                sector_overall_emissions["country_code"].to_list()
            ]
            .rename("country_total_emissions")
            .reset_index()
        )

        # Concatenate and calculate emissions share.
        sector_overall_emissions = pd.concat(
            [
                sector_overall_emissions,
                emissions_country_totals["country_total_emissions"],
            ],
            axis=1,
        )
        sector_overall_emissions[emissions_col + "_share"] = (
            100
            * sector_overall_emissions[emissions_col]
            / sector_overall_emissions["country_total_emissions"]
        )

        # Update emissions column, label, title, save name.
        emissions_col = emissions_col + "_share"
        ylabel = "% Share of " + ylabel
        title = "% Share of " + title
        save_name = "pct_share_of_" + save_name
    else:
        ylabel = ylabel + units

    # Split long titles into multiple lines.
    title = "\n".join(wrap(title, 60, break_long_words=False))

    # Create stacked barplot.
    _, _ = euf.plot_stacked_barplot(
        emissions_df=sector_overall_emissions,
        emissions_col=emissions_col,
        group_col="country_name",
        hue_col="sector_name",
        hue_order=sector_emissions_order,
        palette=palette,
        save_dir=save_dir,
        save_name=save_name,
        title=title,
        ylabel=ylabel,
        statistic=statistic,
    )


def main():
    """Main emissions analysis function."""

    # Read in emissions data.
    emissions_df = pd.read_excel(
        cfg.DATA_PATH + cfg.FILE_NAME, sheet_name=cfg.SHEET_NAME
    )

    # Convert column names to snake case.
    emissions_df.columns = (
        emissions_df.columns.str.lower()
        .str.replace(" ", "_")
        .str.replace("/", "_")
    )

    # Convert kilo tonnes to mega tonnes.
    emissions_df[cfg.EMISSIONS_COLUMN] = (
        pd.to_numeric(emissions_df[cfg.EMISSIONS_COLUMN], errors="coerce")
        / 1000
    )

    # Create emissions per capita using country population data.
    emissions_df = create_emissions_per_capita(
        emissions_df=emissions_df,
        emissions_col=cfg.EMISSIONS_COLUMN,
        country_code_mappings=cfg.COUNTRY_CODE_MAPPINGS,
    )

    # For total emissions and emissions per capita...
    for emissions_col in [cfg.EMISSIONS_COLUMN, "emissions_per_capita"]:
        if emissions_col == "emissions_per_capita":
            save_dir = cfg.RESULTS_PATH + "emissions_per_capita/"
        else:
            save_dir = cfg.RESULTS_PATH + "emissions/"

        os.makedirs(save_dir, exist_ok=True)

        # Create a simple emissions by country baplot.
        create_overall_barplot(
            emissions_df=emissions_df,
            emissions_col=emissions_col,
            save_dir=save_dir,
        )

        # For either absolute emissions or share of emissions...
        for statistic in ["total", "share"]:
            if (
                statistic == "share"
                and emissions_col == "emissions_per_capita"
            ):
                continue

            # Create stacked barplot of emissions by country split by gas.
            create_emissions_by_gas(
                emissions_df=emissions_df,
                emissions_col=emissions_col,
                statistic=statistic,
                save_dir=save_dir,
            )

            # For each sector within specified dictionary...
            for (
                sector,
                sector_codes_palettes,
            ) in cfg.SECTOR_DICTIONARIES.items():
                # Create stacked barplot of emissions by country stacked by
                # sector.
                create_emissions_by_sector(
                    emissions_df=emissions_df,
                    emissions_col=emissions_col,
                    sector=sector,
                    sector_codes=list(sector_codes_palettes.keys()),
                    palette=sector_codes_palettes,
                    statistic=statistic,
                    save_dir=save_dir,
                )


if __name__ == "__main__":
    main()
