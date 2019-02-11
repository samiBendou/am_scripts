"""
Tools for purchase strategy analysis.
Purchase module offers many features to compare Planning objects. It allows to visualize financial results of different
fleets and plannings over a set of lines and hubs.
"""

from utilities import GenericPlot

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


class Data:
    """
    Data class represents a list of plannings and provides comparisons operations.
    Attributes:
        plannings (list): Planning objects to compare. Theses must have been generated of the same hubs and lines.
        The lines are not necessarily the ones you purchased in AM2 but also new ones you have audited.
    """

    def __init__(self, plannings):
        self.plannings = plannings
        for plan in self.plannings:
            assert plan.lines == self.plannings[0].lines

    def sorted(self):
        """Returns sorted plannings by profitability. Returns a list of plans sorted by decreasing profitability"""
        plan_profitability = []
        for plan in self.plannings:
            plan_profitability.append(0)
            plan_profitability[-1] += sum(plan.by_hubs(plan.profitability()).values())

        zip_to_sort = zip(plan_profitability, self.plannings)
        sorted_plans = [x for _, x in sorted(zip_to_sort, reverse=True)]
        return sorted_plans

    def heatmap(self):
        """Returns a list profitability over the week for each planning. Profitability is indexed by hubs and lines"""
        plan_profitability = []
        for plan in self.plannings:
            plan_profitability.append(plan.by_lines(plan.profitability()))

        return plan_profitability


class Plot(GenericPlot):
    """
    Plotting static interface class. Used as interface with matplotlib for every result that can be computed with
    Data objects.
    """

    RENDER_ROOT = GenericPlot.RENDER_ROOT + "purchase/"

    @classmethod
    def sorted(cls, data, max_plans=7):
        """Plots sorted comparison data obtained using data.sorted(). Only displays max_plans planning data per plot."""
        sorted_plans = data.sorted()
        size = min(max_plans, len(sorted_plans))

        bar_width = 0.2
        opacity = 0.4

        profits_by_line = []
        profitability_by_line = []
        price_by_lines = []

        for plan in sorted_plans:
            profits_by_line.append(plan.by_lines(plan.profits()))
            profitability_by_line.append(plan.by_lines(plan.profitability()))
            price_by_lines.append(plan.price_by_lines())

        for hub_iata, lines in data.plannings[0].lines.items():
            for dst_iata, line in lines.items():
                profits, initial_costs, profitability, names = [], [], [], []

                for k in range(0, size):
                    profits.append(profits_by_line[k][hub_iata][dst_iata] / 1.e6 / 7)
                    initial_costs.append(sum(price_by_lines[k][hub_iata][dst_iata].values()) / 1.e8)
                    profitability.append(profitability_by_line[k][hub_iata][dst_iata])
                    names.append("Planning {:d}".format(k + 1))

                index = np.arange(size)

                plt.bar(index, profits, bar_width,
                        alpha=opacity,
                        color="b",
                        label="Profits (Millions $)")

                plt.bar(index + bar_width, initial_costs, bar_width,
                        alpha=opacity,
                        color="r",
                        label="Initial cost (100M$)")

                plt.bar(index + 2 * bar_width, profitability, bar_width,
                        alpha=opacity,
                        color="g",
                        label="Profitability")

                plt.xticks(index + bar_width / 3, names)
                cls.render(xl="Planes", title="Profits vs initial cost " + hub_iata + "-" + dst_iata)

    @classmethod
    def heatmap(cls, data):
        """Plots a heatmap of profitability over the lines covered and the plannings contained in data"""
        heatmap_planes = data.heatmap()
        size = len(data.plannings)

        plannings_ticks = ["Planning {:d}".format(k + 1) for k in range(0, size)]

        lines_ticks = []
        for hub_iata, lines in data.plannings[0].lines.items():
            for dst_iata, line in lines.items():
                lines_ticks.append(hub_iata + "-" + dst_iata)

        values = []
        for i in range(0, len(lines_ticks)):
            hub_iata, dst_iata = lines_ticks[i].split("-")
            values.append([])
            for j in range(0, len(plannings_ticks)):
                values[i].append(heatmap_planes[j][hub_iata][dst_iata])

        values = np.array(values)

        # get the tick label font size
        dpi = 72.27

        # compute the matrix height in points and inches
        matrix_height_pt = 40 * values.shape[0]
        matrix_height_in = matrix_height_pt / dpi

        # compute the required figure height
        top_margin = 0.07  # in percentage of the figure height
        bottom_margin = 0.07  # in percentage of the figure height
        figure_height = matrix_height_in / (1 - top_margin - bottom_margin)

        # build the figure instance with the desired height
        fig, ax = plt.subplots(
            figsize=(7, figure_height),
            gridspec_kw=dict(top=1 - top_margin, bottom=bottom_margin))

        ax = sns.heatmap(values, ax=ax, cbar=False, cmap="winter")

        # We want to show all ticks...
        ax.set_xticks(np.arange(len(plannings_ticks)))
        ax.set_yticks(np.arange(len(lines_ticks)))
        # ... and label them with the respective list entries
        ax.set_xticklabels(plannings_ticks)
        ax.set_yticklabels(lines_ticks)

        # Rotate the tick labels and set their alignment.
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

        plt.setp(ax.get_yticklabels(), rotation=45, ha="right", rotation_mode="anchor")

        # Loop over data dimensions and create text annotations.
        for i in range(len(lines_ticks)):
            for j in range(len(plannings_ticks)):
                ax.text(j + 0.5, i + 0.5, "{:d} %".format(int(100 * values[i, j])), ha="center", va="center",
                        color="w")

        cls.render(title="Profitability comparison", legend=False)
