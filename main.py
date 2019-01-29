import matplotlib.pyplot as plt
import numpy as np

from scrap import get_lines_attributes
from scrap import get_planes_attributes
from scrap import get_newline_attributes

bar_width = 0.2
opacity = 0.4
error_config = {'ecolor': '0.3'}
max_planes_display = 7
plot_old_lines = False
plot_new_lines = True


planes = get_planes_attributes()
lines = get_lines_attributes()
newlines = get_newline_attributes(lines)

if plot_old_lines and plot_new_lines:
    lines = np.concatenate([lines, newlines])
elif plot_new_lines:
    lines = newlines

for l in lines:
    sorted_planes = sorted(planes, key=lambda x: x.profitability(l), reverse=True)[:max_planes_display]
    sorted_planes = list(filter(lambda x: True if x.range > l.distance else False, sorted_planes))

    n_planes = len(sorted_planes)

    profits = tuple(map(lambda x: sum(x.profits_at_matching(l).values()) / 1.e6, sorted_planes))
    initial_costs = tuple(map(lambda x: x.price * x.match_demand(l)["eco"] / 100.e6, sorted_planes))
    profitability = tuple(map(lambda x: x.profitability(l), sorted_planes))
    names = tuple(map(lambda x: x.name, sorted_planes))

    fig, ax = plt.subplots()

    index = np.arange(n_planes)

    rects1 = plt.bar(index, profits, bar_width,
                     alpha=opacity,
                     color='b',
                     label='Profits (Millions $)')

    rects2 = plt.bar(index + bar_width, initial_costs, bar_width,
                     alpha=opacity,
                     color='r',
                     label='Initial cost (100M$)')

    rects3 = plt.bar(index + 2 * bar_width, profitability, bar_width,
                     alpha=opacity,
                     color='g',
                     label='Profitability')

    plt.xlabel('Planes')
    plt.title('Repartition profits/initial cost HYD->' + l.name)
    plt.xticks(index + bar_width / 3, names)
    plt.legend()

    plt.tight_layout()

    sorted_planes[0].display_matching_infos(l)

plt.show()
