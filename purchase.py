from utilities import GenericPlot
from model import Market

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


class Data:

    def __init__(self, plannings):
        self.plannings = plannings
        for plan in self.plannings:
            assert plan.lines == self.plannings[0].lines

    """
    @brief Sort plannings by profitability
    @details Returns a dictionary which contains planes sorted by lines. For each line the corresponding planes are the
    planes which have sufficient range to flight to destination. The planes are sorted by decreasing profitability.
    """

    def sorted(self, day=0):
        return sorted(self.plannings, key=lambda x: sum(x.by_hubs(x.profitability(day)).values()), reverse=True)

    def heatmap(self, included_planes=None, excluded_planes=None):
        planes_names = self._filter_planes(included_planes, excluded_planes)

        planes = {}
        for iata, h in self.lines.items():
            planes[iata] = {}
            for l in h.values():
                planes[iata][l.dst.iata] = list(
                    filter(lambda x: True if x.name in planes_names else False, self.planes.values()))

        return planes

    def _filter_planes(self, included_planes, excluded_planes):
        inc = [x.name for x in self.planes] if included_planes is None else included_planes
        exc = [] if excluded_planes is None else excluded_planes
        inc = filter(lambda x: False if x in exc else True, inc)

        return list(inc)


class Plot(GenericPlot):
    RENDER_ROOT = GenericPlot.RENDER_ROOT + "purchase/"

    @classmethod
    def sort(cls, data, day=0, max_plans=7):
        sorted_plans = data.sorted()
        size = min(max_plans, len(sorted_plans))

        bar_width = 0.2
        opacity = 0.4

        profits_by_line = []
        profitability_by_line = []

        for plan in sorted_plans:
            profits_by_line.append(plan.by_lines(plan.profits(day)))
            profitability_by_line.append(plan.by_lines(plan.profitability(day)))

        for hub_iata, lines in data.plannings[0].lines.items():
            for dst_iata, line in lines.items():
                profits, initial_costs, profitability, names = [], [], [], []

                for k in range(0, size):
                    count = len(lines) * len(sorted_plans[k].lines)
                    cost = sorted_plans[k].total_planes_cost() + sorted_plans[k].total_acq_cost()
                    profits.append(profits_by_line[k][hub_iata][dst_iata] / 1.e6)
                    initial_costs.append(cost / count / 1.e8)
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
    def heatmap(cls, data, included_planes=None, excluded_planes=None):
        heatmap_planes = data.heatmap(included_planes, excluded_planes)

        planes_names = [x.name for x in list(data.planes.values())]
        planes_ticks = list(filter(lambda s: True if s in included_planes else False, planes_names))
        for iata, h in data.lines.items():
            lines_ticks = [iata + "-" + l.dst.iata for l in h.values()]
            values = []
            dst_iata = list(h.keys())
            for i in range(0, len(h)):
                values.append([])
                for j in range(0, len(planes_ticks)):
                    plane = heatmap_planes[iata][h[dst_iata[i]].dst.iata][j]
                    values[i].append(
                        plane.profitability(h[dst_iata[i]]) if plane.range > h[dst_iata[i]].distance else 0)

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
            ax.set_xticks(np.arange(len(planes_ticks)))
            ax.set_yticks(np.arange(len(lines_ticks)))
            # ... and label them with the respective list entries
            ax.set_xticklabels(planes_ticks)
            ax.set_yticklabels(lines_ticks)

            # Rotate the tick labels and set their alignment.
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

            plt.setp(ax.get_yticklabels(), rotation=45, ha="right", rotation_mode="anchor")

            # Loop over data dimensions and create text annotations.
            for i in range(len(lines_ticks)):
                for j in range(len(included_planes)):
                    ax.text(j + 0.5, i + 0.5, "{:d} %".format(int(100 * values[i, j])), ha="center", va="center",
                            color="w")

            cls.render(title="Profitability comparison", legend=False)
