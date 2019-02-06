from Market import Market
import numpy as np

additional_flight_time = 1.0  # hours
hours_day = 24  # hours / day
l_petrol_bar = 159.0  # L / barrel
petrol_price = 53.53 / l_petrol_bar  # $/L
fill_ratio = 0.86  # expected aircraft filling ratio


class Plane:
    def __init__(self, name, pax, speed, cons, year, max_range=np.infty, price=0., wear_rate=0.):
        self.name = name
        self.pax = pax
        self.speed = speed  # in km/h
        self.cons = cons  # in L/100km/pax
        self.range = max_range
        self.price = price
        self.wear_rate = wear_rate
        self.year = year

    @classmethod
    def from_dict(cls, plane):
        return Plane(name=plane["name"],
                     pax=plane["pax"],
                     speed=plane["speed"],
                     cons=plane["cons"],
                     max_range=plane["range"],
                     price=plane["price"],
                     wear_rate=plane["wear_rate"],
                     year=plane["year"])

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
        # max_pax = sum(self.pax.values())
        # demand_max = sum(line.demand.values())
        flight_per_day = self.flights_per_day(line)

        for m in Market:
            try:
                count_planes[m.name] = int(
                    np.round(line.demand[m.name] / (2 * fill_ratio * self.pax[m.name] * flight_per_day)))
            except ZeroDivisionError:
                count_planes[m.name] = 0
                continue

        return count_planes

    def pax_capacity_at_matching(self, line):
        count_planes = self.match_demand(line)

        best_pax = {}
        for m in Market:
            best_pax[m.name] = count_planes[Market.eco.name] * self.flights_per_day(line) * 2 * self.pax[m.name]

        return best_pax

    def pax_delta(self, line):
        matching_pax = self.pax_capacity_at_matching(line)
        matching_delta = line.demand.copy()
        for m in Market:
            matching_delta[m.name] -= int(matching_pax[m.name])

        return matching_delta

    def pax_at_matching(self, line):
        matching_pax = self.pax_capacity_at_matching(line)

        best_pax = {}
        for m in Market:
            best_pax[m.name] = int(min(line.demand[m.name], matching_pax[m.name]))

        return best_pax

    def consumption_at_matching(self, line):
        best_pax = self.pax_at_matching(line)
        matching_cons = {}
        for m in Market:
            matching_cons[m.name] = 2 * line.distance * best_pax[m.name] * self.cons / 100.0

        return matching_cons

    def revenue_at_matching(self, line):
        best_pax = self.pax_at_matching(line)
        best_revenue = {}
        for m in Market:
            best_revenue[m.name] = best_pax[m.name] * line.ticket_price[m.name]

        return best_revenue

    def cost_at_matching(self, line):
        matching_cons = self.consumption_at_matching(line)
        matching_cost = matching_cons
        for m in Market:
            matching_cost[m.name] *= petrol_price
            matching_cost[m.name] += (line.tax + line.hub.tax) * int(self.flights_per_day(line) / 3.)

        return matching_cost

    def profits_at_matching(self, line):
        matching_profits = {}
        matching_cost = self.cost_at_matching(line)
        matching_revenue = self.revenue_at_matching(line)
        for m in Market:
            matching_profits[m.name] = float(matching_revenue[m.name] - matching_cost[m.name])

        return matching_profits

    def profitability(self, line):
        count_planes = self.match_demand(line)
        matching_monthly_profits = 30 * sum(self.profits_at_matching(line).values())
        wear_cost = (self.wear_rate / 100. * self.flights_per_day(line) * 2 * self.flight_time(line)) * self.price
        cost = float(count_planes[Market.eco.name]) * self.price + line.dst.price + line.hub.price

        if cost == 0 and wear_cost == 0:
            return 0.0
        return matching_monthly_profits / (cost + wear_cost)

    def display_matching_infos(self, line):
        count_planes = self.match_demand(line)
        best_pax = self.pax_at_matching(line)
        matching_delta = self.pax_delta(line)
        best_revenue = self.revenue_at_matching(line)
        matching_cost = self.cost_at_matching(line)
        matching_profits = self.profits_at_matching(line)

        print("{}\t" + line.hub.iata + "-{}\tFlight time {}".format(self.name, line.dst.iata,
                                                                    self.flight_time_verbose(line)))
        print("Market\t|Planes\t|PAX\t|PAXr\t|Revenue(M$)|Cost(M$)\t|Profits(M$)|")
        for m in Market:
            best_pax_align = '\t' if best_pax[m.name] < 100 else ''
            matching_delta_align = '\t' if len(str(int(matching_delta[m.name]))) < 3 else ''
            matching_profits_align = '\t' if matching_profits[m.name] > 0 else ''
            format_line = "{}\t\t|{:d}\t\t|{:d}{}\t|{:d}{}\t|{:2.4f}\t\t|{:2.4f}\t\t|{:2.4f}\t{}|"
            format_line.format(m,
                               count_planes[m.name],
                               int(best_pax[m.name]),
                               best_pax_align,
                               int(matching_delta[m.name]),
                               matching_delta_align,
                               best_revenue[m.name] / 1.e6,
                               matching_cost[m.name] / 1.e6,
                               matching_profits[m.name] / 1.e6,
                               matching_profits_align
                               )
            print(format_line)

        print("Flights per day          : {:d}".format(self.flights_per_day(line)))
        print("Total revenue (M$)       : {:2.4f}".format(sum(best_revenue.values()) / 1.e6))
        print("Total cost (M$)          : {:2.4f}".format(sum(matching_cost.values()) / 1.e6))
        print("Total profit (M$)        : {:2.4f}".format(sum(matching_profits.values()) / 1.e6))

        print("Price of airplanes (M$)  : {:4.2f}".format(self.price * count_planes[Market.eco.name] / 1.e6))
        print("Price of airport (M$)    : {:2.4f}".format(line.dst.price / 1.e6))
        print("Price of hub (M$)        : {:2.4f}".format(line.hub.price / 1.e6))

        print("Rentability              : {:2.4f}".format(self.profitability(line)))
