import matplotlib.pyplot as plt
import numpy as np

bar_width = 0.2
opacity = 0.4
error_config = {'ecolor': '0.3'}

additional_flight_time = 1.0  # hours
hours_day = 24  # hours / day
l_petrol_baril = 159.0  # liters / baril
petrol_price = 53.53 / l_petrol_baril  # $/L
fill_ratio = 0.86
max_planes_display = 7

# Segment market. eco : economical, biz : business, pre : premium
market = ["eco", "biz", "pre"]


class Hub:
    def __init__(self, tax, acquired=True, price=0):
        self.tax = tax
        self.acquire = acquired
        self.price = 0 if acquired else price


class Line:
    def __init__(self, name, demand, ticket_price, distance, tax, hub, price=0.):
        self.name = name
        self.demand = demand  # in pax
        self.distance = distance  # in km
        self.ticket_price = ticket_price  # in $
        self.tax = tax  # in $/flight
        self.hub = hub
        self.price = price  # acquisition price


class Plane:
    def __init__(self, name, pax, speed, cons, max_range=np.infty, price=0., wear_rate=0.):
        self.name = name
        self.pax = pax
        self.speed = speed  # in km/h
        self.cons = cons  # in L/100km/pax
        self.range = max_range
        self.price = price
        self.wear_rate = wear_rate

    def flights_per_day(self, line):
        return int(np.floor(hours_day / (2 * self.flight_time(line))))

    def flight_time(self, line):
        return line.distance / self.speed + additional_flight_time  # in hours

    def flight_time_verbose(self, line):
        flight_time = self.flight_time(line)
        hours = int(np.floor(flight_time))
        minutes = int((flight_time - hours) * 60.0)
        return str.format("{:d}:{:d}", hours, minutes)

    def match_demand(self, line):

        # number of planes too buy to fulfill the demand for each segment
        count_planes = {}
        max_pax = sum(self.pax.values())
        demand_max_pax = sum(line.demand.values())

        for m in market:
            self.pax[m] = max_pax * line.demand[m] / demand_max_pax
            count_planes[m] = int(
                np.round(line.demand[m] / (2 * fill_ratio * self.pax[m] * self.flights_per_day(line))))
        return count_planes

    def pax_capacity_at_matching(self, line):
        count_planes = self.match_demand(line)

        best_pax = {}
        for m in market:
            best_pax[m] = count_planes["eco"] * self.flights_per_day(line) * 2 * self.pax[m]

        return best_pax

    def pax_delta(self, line):
        matching_pax = self.pax_capacity_at_matching(line)
        matching_delta = line.demand.copy()
        for m in market:
            matching_delta[m] -= int(matching_pax[m])

        return matching_delta

    def pax_at_matching(self, line):
        matching_pax = self.pax_capacity_at_matching(line)

        best_pax = {}
        for m in market:
            best_pax[m] = int(min(line.demand[m], matching_pax[m]))

        return best_pax

    def consumption_at_matching(self, line):
        best_pax = self.pax_at_matching(line)
        matching_cons = {}
        for m in market:
            matching_cons[m] = 2 * line.distance * best_pax[m] * self.cons / 100.0

        return matching_cons

    def revenue_at_matching(self, line):
        best_pax = self.pax_at_matching(line)
        best_revenue = {}
        for m in market:
            best_revenue[m] = best_pax[m] * line.ticket_price[m]

        return best_revenue

    def cost_at_matching(self, line):
        matching_cons = self.consumption_at_matching(line)
        matching_cost = matching_cons
        for m in market:
            matching_cost[m] *= petrol_price
            matching_cost[m] += (line.tax + line.hub.tax) * int(self.flights_per_day(line) / len(market))

        return matching_cost

    def profits_at_matching(self, line):
        matching_profits = {}
        matching_cost = self.cost_at_matching(line)
        matching_revenue = self.revenue_at_matching(line)
        for m in market:
            matching_profits[m] = float(matching_revenue[m] - matching_cost[m])

        return matching_profits

    def profitability(self, line):
        matching_monthly_pofits = 30 * sum(self.profits_at_matching(line).values())
        wear_cost = (self.wear_rate / 100. * self.flights_per_day(line) * 2 * self.flight_time(line)) * self.price
        cost = float(self.match_demand(line)["eco"]) * self.price + line.price
        return matching_monthly_pofits / (cost + wear_cost)

    def display_matching_infos(self, line):
        count_planes = self.match_demand(line)
        best_pax = self.pax_at_matching(line)
        matching_delta = self.pax_delta(line)
        best_revenue = self.revenue_at_matching(line)
        matching_cost = self.cost_at_matching(line)
        matching_profits = self.profits_at_matching(line)

        print("{}\tHYD-{}\tFlight time {}".format(self.name, line.name, self.flight_time_verbose(line)))
        print("Market\t|Planes\t|PAX\t|PAXr\t|Revenue(M$)|Cost(M$)\t|Profits(M$)|")
        for m in market:
            best_pax_align = '\t' if best_pax[m] < 100 else ''
            matching_delta_align = '\t' if len(str(int(matching_delta[m]))) < 3 else ''
            matching_profits_align = '\t' if matching_profits[m] > 0 else ''
            print("{}\t\t|{:d}\t\t|{:d}{}\t|{:d}{}\t|{:2.4f}\t\t|{:2.4f}\t\t|{:2.4f}\t{}|".format(m,
                                                                                                  count_planes[m],
                                                                                                  int(best_pax[m]),
                                                                                                  best_pax_align,
                                                                                                  int(matching_delta[
                                                                                                          m]),
                                                                                                  matching_delta_align,
                                                                                                  best_revenue[
                                                                                                      m] / 1.e6,
                                                                                                  matching_cost[
                                                                                                      m] / 1.e6,
                                                                                                  matching_profits[
                                                                                                      m] / 1.e6,
                                                                                                  matching_profits_align
                                                                                                  )
                  )

        print("Flights per day          : {:d}".format(self.flights_per_day(line)))
        print("Total revenue (M$)       : {:2.4f}".format(sum(best_revenue.values()) / 1.e6))
        print("Total cost (M$)          : {:2.4f}".format(sum(matching_cost.values()) / 1.e6))
        print("Total profit (M$)        : {:2.4f}".format(sum(matching_profits.values()) / 1.e6))

        print("Price of airplanes (M$)  : {:4.2f}".format(self.price * count_planes["eco"] / 1.e6))
        print("Price of airport (M$)    : {:2.4f}".format(line.price / 1.e6))
        print("Price of hub (M$)        : {:2.4f}".format(line.hub.price / 1.e6))

        print("Rentability              : {:2.4f}".format(self.profitability(line)))


planes = [
    Plane("B737-6", {"eco": 119, "biz": 8, "pre": 0}, speed=834.0, cons=3.3, price=64.e6, max_range=5976.,
          wear_rate=0.02),
    Plane("Q400", {"eco": 80.0, "biz": 0.0, "pre": 0.0}, speed=666.7, cons=3.4, price=26.5e6, max_range=2400.,
          wear_rate=0.02),
    Plane("CRJ700", {"eco": 78.0, "biz": 0.0, "pre": 0.0}, speed=834., cons=3.75, price=33.2e6, max_range=3699.,
          wear_rate=0.019),
    Plane("CRJ900", {"eco": 90.0, "biz": 0.0, "pre": 0.0}, speed=850., cons=3.58, price=38.2e6, max_range=3407.,
          wear_rate=0.019),
    Plane("CRJ1000", {"eco": 104.0, "biz": 0.0, "pre": 0.0}, speed=850., cons=3.22, price=43.2e6, max_range=3129.,
          wear_rate=0.015),
    Plane("ERJ140", {"eco": 44.0, "biz": 0.0, "pre": 0.0}, speed=828., cons=4.76, price=21.5e6, max_range=3057.,
          wear_rate=0.02),
    Plane("ERJ145", {"eco": 50.0, "biz": 0.0, "pre": 0.0}, speed=828., cons=4.46, price=24.0e6, max_range=2872.,
          wear_rate=0.022),
    Plane("ERJ170", {"eco": 80.0, "biz": 0.0, "pre": 0.0}, speed=828., cons=3.74, price=33.5e6, max_range=3891.,
          wear_rate=0.018),
    Plane("ERJ175", {"eco": 88.0, "biz": 0.0, "pre": 0.0}, speed=828., cons=3.57, price=37.0e6, max_range=3706.,
          wear_rate=0.018),
    Plane("ATR42-5C", {"eco": 50.0, "biz": 0.0, "pre": 0.0}, speed=540., cons=4.37, price=16.0e6, max_range=1555.,
          wear_rate=0.023),
    Plane("ATR42-6", {"eco": 50.0, "biz": 0.0, "pre": 0.0}, speed=540., cons=4.18, price=16.4e6, max_range=1629.,
          wear_rate=0.017),
    Plane("ATR72-5", {"eco": 74.0, "biz": 0.0, "pre": 0.0}, speed=500., cons=4.1, price=22.6e6, max_range=1648.,
          wear_rate=0.022),
    Plane("ATR72-6", {"eco": 74.0, "biz": 0.0, "pre": 0.0}, speed=500., cons=3.91, price=23.0e6, max_range=1731.,
          wear_rate=0.017),
]

hubs = [
    Hub(tax=4497.0)
]

lines = [
    Line("HKT",
         demand={"eco": 2382.0, "biz": 130.0, "pre": 21.0},
         ticket_price={"eco": 0.0, "biz": 0.0, "pre": 0.0},
         distance=2382, tax=4941.0,
         hub=hubs[0]),
    Line("DMK",
         demand={"eco": 3152.0, "biz": 165.0, "pre": 28.0},
         ticket_price={"eco": 0.0, "biz": 0.0, "pre": 0.0},
         distance=2403, tax=10034.0,
         hub=hubs[0]),

    Line("ISB",
         demand={"eco": 2817.0, "biz": 99.0, "pre": 10.0},
         ticket_price={"eco": 669.0, "biz": 889.0, "pre": 1538.0},
         distance=1897.0, tax=5153.0,
         hub=hubs[0]),
    Line("KHI",
         demand={"eco": 2699.0, "biz": 95.0, "pre": 9.0},
         ticket_price={"eco": 533.0, "biz": 708.0, "pre": 1225.0},
         distance=1446.0, tax=5658.0,
         hub=hubs[0]),
    Line("GOI",
         demand={"eco": 2580.0, "biz": 106.0, "pre": 14.0},
         ticket_price={"eco": 259.0, "biz": 344.0, "pre": 595.0},
         distance=532.0, tax=5198.0,
         hub=hubs[0]),
    Line("CCU",
         demand={"eco": 2732.0, "biz": 112.0, "pre": 15.0},
         ticket_price={"eco": 462.0, "biz": 614.0, "pre": 1062.0},
         distance=1207.0, tax=4866.0,
         hub=hubs[0]),
    Line("BLR",
         demand={"eco": 3031.0, "biz": 125.0, "pre": 17.0},
         ticket_price={"eco": 236.0, "biz": 313.0, "pre": 542.0},
         distance=456.0, tax=5776.0,
         hub=hubs[0]),
    Line("MAA",
         demand={"eco": 3033.0, "biz": 125.0, "pre": 17.0},
         ticket_price={"eco": 252.0, "biz": 335.0, "pre": 579.0},
         distance=508.0, tax=5420.0,
         hub=hubs[0]),
    Line("DEL",
         demand={"eco": 3155.0, "biz": 130.0, "pre": 18.0},
         ticket_price={"eco": 480.0, "biz": 638.0, "pre": 1104.0},
         distance=1897.0, tax=5153.0,
         hub=hubs[0]),
    Line("BOM",
         demand={"eco": 3158.0, "biz": 130.0, "pre": 16.0},
         ticket_price={"eco": 286.0, "biz": 380.0, "pre": 657.0},
         distance=622.0, tax=6688.0,
         hub=hubs[0])
]

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
                     label='Profits (M$)')

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
