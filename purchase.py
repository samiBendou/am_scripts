from GenericPlot import GenericPlot

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


class Data:

    def __init__(self, planes, lines):
        self.planes = planes
        self.lines = lines

    """
    @brief Sort planes by lines and profitability
    @details Returns a dictionary which contains planes sorted by lines. For each line the corresponding planes are the
    planes which have sufficient range to flight to destination. The planes are sorted by decreasing profitability.
    """

    def sort(self, included_planes=None, excluded_planes=None):
        planes_names = self._filter_planes(included_planes, excluded_planes)

        planes = {}
        for l in self.lines:
            planes[l.name] = list(
                filter(lambda x: True if x.range > l.distance and x.name in planes_names else False, self.planes))
            planes[l.name] = sorted(planes[l.name], key=lambda x: x.profitability(l), reverse=True)

        return planes

    def heatmap(self, included_planes=None, excluded_planes=None):
        planes_names = self._filter_planes(included_planes, excluded_planes)

        planes = {}
        for l in self.lines:
            planes[l.name] = list(filter(lambda x: True if x.name in planes_names else False, self.planes))

        return planes

    def _filter_planes(self, included_planes, excluded_planes):
        inc = [x.name for x in self.planes] if included_planes is None else included_planes
        exc = [] if excluded_planes is None else excluded_planes
        inc = filter(lambda x: False if x in exc else True, inc)

        return list(inc)


class Plot(GenericPlot):
    RENDER_ROOT = GenericPlot.RENDER_ROOT + "purchase/"

    @classmethod
    def sort(cls, data, included_planes=None, excluded_planes=None, max_planes=7):
        sorted_planes = data.sort(included_planes, excluded_planes)

        bar_width = 0.2
        opacity = 0.4

        for l in data.lines:
            profits = tuple(
                map(lambda x: sum(x.profits_at_matching(l).values()) / 1.e6, sorted_planes[l.name][:max_planes]))
            initial_costs = tuple(
                map(lambda x: x.price * x.match_demand(l)["eco"] / 100.e6, sorted_planes[l.name][:max_planes]))
            profitability = tuple(
                map(lambda x: x.profitability(l), sorted_planes[l.name][:max_planes]))
            names = tuple(
                map(lambda x: x.name, sorted_planes[l.name][:max_planes]))

            if names == ():
                continue

            index = np.arange(min(max_planes, len(names)))

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
            cls.render(xl="Planes", title="Profits vs initial cost HYD-" + l.name)

            sorted_planes[l.name][0].display_matching_infos(l)
            sorted_planes[l.name][1].display_matching_infos(l)

    @classmethod
    def heatmap(cls, data, included_planes=None, excluded_planes=None):
        heatmap_planes = data.heatmap(included_planes, excluded_planes)

        lines_ticks = [l.hub.name + "-" + l.name for l in data.lines]
        planes_ticks = list(filter(lambda s: True if s in included_planes else False, [x.name for x in data.planes]))
        values = []
        for i in range(0, len(data.lines)):
            values.append([])
            for j in range(0, len(planes_ticks)):
                if heatmap_planes[data.lines[i].name][j].range > data.lines[i].distance:
                    values[i].append(heatmap_planes[data.lines[i].name][j].profitability(data.lines[i]))
                else:
                    values[i].append(0)

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
                ax.text(j + 0.5, i + 0.5, "{:d} %".format(int(100 * values[i, j])), ha="center", va="center", color="w")

        cls.render(title="Profitability comparison", legend=False)
