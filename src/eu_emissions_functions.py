"""Function to facilitate the EU emissions analysis."""

import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd


def plot_basic_barplot(
    emissions_df,
    emissions_col,
    group_col,
    order,
    save_dir,
    save_name,
    hue_col=None,
    hue_order=None,
    palette=None,
):
    """Function to create a basic barplot."""

    fig, ax = plt.subplots()

    # Create barplot.
    sns.barplot(
        data=emissions_df,
        x=group_col,
        y=emissions_col,
        order=order,
        hue=hue_col,
        hue_order=hue_order,
        palette=palette,
    )

    # Set labels and titles.
    ax.set_xlabel(group_col.replace("_", " ").replace(" name", "").title())
    if emissions_col == "emissions_per_capita":
        ax.set_ylabel("Emissions, tonnes CO\u2082 eq.")
        ax.set_title("Emissions per Capita by Country")
    else:
        ax.set_ylabel("Emissions, Mt CO\u2082 eq.")
        ax.set_title("Emissions by Country")

    # Rotate xlabels.
    xticklabels = ax.get_xticklabels()
    ax.set_xticklabels(xticklabels, rotation=75)

    # Save figure.
    fig.savefig(save_dir + save_name, bbox_inches="tight")

    plt.close()

    return fig, ax


def plot_stacked_barplot(
    emissions_df,
    emissions_col,
    group_col,
    hue_col,
    hue_order,
    palette,
    save_dir,
    save_name,
    title,
    ylabel,
    statistic,
):
    """Create stacked bar plot, split by group col and stacked by hue_col."""

    fig, ax = plt.subplots()

    # Determine order of groups along x-axis.
    if statistic != "share":
        group_sums_sorted = (
            emissions_df.groupby(group_col)[emissions_col]
            .sum()
            .sort_values(ascending=False)
        )
    else:
        group_sums_sorted = (
            emissions_df.groupby(group_col)[
                emissions_col.removesuffix("_share")
            ]
            .sum()
            .sort_values(ascending=False)
        )
    group_order = group_sums_sorted.index.to_list()

    # Determine maximum positive and negative extent of bars.
    group_pos_max = (
        emissions_df.loc[emissions_df[emissions_col].gt(0)]
        .groupby(group_col)[emissions_col]
        .sum()
        .max()
    )

    group_neg_max = (
        emissions_df.loc[emissions_df[emissions_col].lt(0)]
        .groupby(group_col)[emissions_col]
        .sum()
        .min()
    )

    # Loop over groups creating stacked bars for each.
    group_loc = -0.5
    group_locs = []
    net_patches_to_add = []
    for idx, group in enumerate(group_order):
        # Select emissions for group.
        group_df = emissions_df.loc[emissions_df[group_col].eq(group), :]

        # Loop over each hue for group stacking up the emisssions.
        bottom_above = 0
        bottom_below = 0
        for hue in hue_order:
            # Select emissions from group for this hue.
            emissions = group_df.loc[
                group_df[hue_col].eq(hue), emissions_col
            ].squeeze()

            # If no emissions for this hue group pair then continue,
            if isinstance(emissions, pd.Series):
                continue

            # If negative emissions then stack below zero, otherwise stack
            # above.
            if emissions < 0:
                tmp_bottom = bottom_below + emissions
                height = -1 * emissions
            else:
                tmp_bottom = bottom_above
                height = emissions

            # Create bar for hue level, increment starting point for next bar.
            if pd.notna(emissions):
                plt.bar(
                    x=group_loc,
                    height=height,
                    width=0.8,
                    bottom=tmp_bottom,
                    color=palette[hue],
                    zorder=1,
                )
                if emissions < 0:
                    bottom_below = bottom_below + emissions
                else:
                    bottom_above = bottom_above + emissions

            else:
                continue

        # When any of the emissions are negative for group add a record to
        # produce a net emissions rectangle patch later.
        if bottom_below != 0:
            net_patches_to_add.append(group)

        # Record location for group, and increment position of next group.
        group_locs.append(group_loc)
        group_loc = group_loc + 1

    # Set xticks, rotate labels.
    ax.set_xticks(ticks=group_locs, labels=group_order)
    xticklabels = ax.get_xticklabels()
    ax.set_xticklabels(xticklabels, rotation=75)

    # Create legend handles.
    handles = [
        mpatches.Rectangle((0, 0), 0.1, 0.1, color=palette[x])
        for x in hue_order
    ]

    # Determine positioning of legend, based on whether absolute or share of
    # emissions is being plotted.
    if statistic == "share":
        loc = "upper center"
        bbox_to_anchor = (0.5, -0.26)
        ncols = 3
    else:
        loc = "upper right"
        bbox_to_anchor = (1.0, 1.0)
        ncols = 1

    # Create legend.
    leg1 = ax.legend(
        handles=handles,
        labels=hue_order,
        title=hue_col.replace("_", " ").title(),
        loc=loc,
        bbox_to_anchor=bbox_to_anchor,
        ncol=ncols,
    )

    # Draw to establish legend extents.
    fig.canvas.draw()

    # Get legend bbox, convert to axes coordinates.
    bbox = leg1.get_frame().get_bbox()
    transformed = bbox.transformed(ax.transAxes.inverted())
    yloc= transformed.bounds[1]

    # Add legend.
    plt.gcf().add_artist(leg1)

    # Set labels and title.
    ax.set_xlabel(group_col.replace("_", " ").replace(" name", "").title())
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    # Set axis limits.
    ax.set_xlim((group_locs[0] - 0.5, group_locs[-1] + 0.5))
    if pd.isna(group_neg_max):
        ax.set_ylim((-0.005 * group_pos_max, 1.02 * group_pos_max))
    else:
        plot_range = group_pos_max - group_neg_max
        ax.set_ylim(
            (
                group_neg_max - 0.01 * plot_range,
                group_pos_max + 0.01 * plot_range,
            )
        )

    # If there are any net emissions patches to add...
    if len(net_patches_to_add) > 0:
        # Add them one by one.
        for net_patch in net_patches_to_add:
            net_emissions = mpatches.Rectangle(
                xy=(
                    -0.5 + group_order.index(net_patch) - 0.1,
                    group_sums_sorted.loc[net_patch]
                    - 0.005 * (ax.get_ylim()[1] - ax.get_ylim()[0]),
                ),
                width=0.2,
                height=0.01 * (ax.get_ylim()[1] - ax.get_ylim()[0]),
                edgecolor="black",
                facecolor="none",
                zorder=4,
            )
            ax.add_patch(net_emissions)

        leg2 = ax.legend(
            handles=[net_emissions],
            labels=["Net Emissions"],
            loc="upper right",
            bbox_to_anchor=(1.0, yloc - 0.01)
        )
        plt.gca().add_artist(leg2)

    # Save plot.
    fig.savefig(save_dir + save_name, bbox_inches="tight")

    plt.close()

    return fig, ax
