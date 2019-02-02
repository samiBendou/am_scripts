import matplotlib.pyplot as plt
import numpy as np

class Data:

    def __init__(self, plane, line):
        self.plane = plane
        self.line = line

    def sort(self):
        excluded_planes = ["F-100", "DC8-73", "DC8-55", "DC-3"]
        sorted_planes = {}
        for l in self.line:
            sorted_planes[l.name] = list(
                filter(lambda x: True if x.range > l.distance and x.name not in excluded_planes else False, self.plane))
            sorted_planes[l.name] = sorted(sorted_planes[l.name], key=lambda x: x.profitability(l), reverse=True)

        return sorted_planes


class Plot:
    bar_width = 0.2
    opacity = 0.4
    error_config = {'ecolor': '0.3'}
    max = 7

    @classmethod
    def sort(cls, data):
        sorted_planes = data.sort()

        for l in data.line:
            profits = tuple(
                map(lambda x: sum(x.profits_at_matching(l).values()) / 1.e6, sorted_planes[l.name][:Plot.max]))
            initial_costs = tuple(
                map(lambda x: x.price * x.match_demand(l)["eco"] / 100.e6, sorted_planes[l.name][:Plot.max]))
            profitability = tuple(
                map(lambda x: x.profitability(l), sorted_planes[l.name][:Plot.max]))
            names = tuple(
                map(lambda x: x.name, sorted_planes[l.name]))

            fig, ax = plt.subplots()

            index = np.arange(Plot.max)

            rects1 = plt.bar(index, profits, Plot.bar_width,
                             alpha=Plot.opacity,
                             color='b',
                             label='Profits (Millions $)')

            rects2 = plt.bar(index + Plot.bar_width, initial_costs, Plot.bar_width,
                             alpha=Plot.opacity,
                             color='r',
                             label='Initial cost (100M$)')

            rects3 = plt.bar(index + 2 * Plot.bar_width, profitability, Plot.bar_width,
                             alpha=Plot.opacity,
                             color='g',
                             label='Profitability')

            plt.xlabel('Planes')
            plt.title('Repartition profits/initial cost HYD->' + l.name)
            plt.xticks(index + Plot.bar_width / 3, names)
            plt.legend()

            plt.tight_layout()

            sorted_planes[l.name][0].display_matching_infos(l)

        plt.show()

