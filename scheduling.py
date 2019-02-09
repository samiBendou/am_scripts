from model import *
import scrap
import copy

hours_day = 24
liters_barrel = 159.0
petrol_price = 53.53 / liters_barrel  # $/L


class Planning:
    def __init__(self, lines, planes, schedule=None, fill=0.86, add_time=1.):
        self.lines = lines
        self.planes = planes
        self.schedule = {} if schedule is None else schedule
        self.fill = fill
        self.add_time = add_time

        self.generate_schedule()

    def total_planes_cost(self):
        cost = 0.
        for plane in self.planes.values():
            cost += plane.price

        return cost

    def total_acq_cost(self):
        cost = 0.
        for hub_iata, lines in self.lines.items():
            for line in lines.values():
                cost += line.hub.price + line.dst.price

        return cost

    def flights(self, day):
        count = {}
        for hub_iata, lines in self.lines.items():
            count[hub_iata] = {}
            for dst_iata, line in lines.items():
                count[hub_iata][dst_iata] = {}
                for plane_id, week_schedule in self.schedule.items():
                    count[hub_iata][dst_iata][plane_id] = week_schedule[day].count(hub_iata + "-" + dst_iata)

        return count

    def pax(self, day):
        flights = self.flights(day)

        pax = {}
        for hub_iata, lines in self.lines.items():
            pax[hub_iata] = {}
            for dst_iata, line in lines.items():
                pax[hub_iata][dst_iata] = {}
                for plane_id in self.planes.keys():
                    pax[hub_iata][dst_iata][plane_id] = {}
                    flights_count = flights[hub_iata][dst_iata][plane_id]
                    for m in Market:
                        plane_fill = self.fill * self.planes[plane_id].pax[m.name]
                        pax[hub_iata][dst_iata][plane_id][m.name] = 2 * plane_fill * flights_count

        return pax

    def pax_delta(self, day):
        pax = self.pax(day)

        delta = {}
        for hub_iata, lines in self.lines.items():
            delta[hub_iata] = {}
            for dst_iata, line in lines.items():
                delta[hub_iata][dst_iata] = {}
                for m in Market:
                    delta[hub_iata][dst_iata][m.name] = line.demand[m.name]
                    for plane_id in self.planes.keys():
                        delta[hub_iata][dst_iata][m.name] -= pax[hub_iata][dst_iata][plane_id][m.name]

        return delta

    def flight_time(self, day):
        flights = self.flights(day)

        time = {}
        for hub_iata, lines in self.lines.items():
            time[hub_iata] = {}
            for dst_iata, line in lines.items():
                time[hub_iata][dst_iata] = {}
                for plane_id in self.planes.keys():
                    flight_time = self.planes[plane_id].flight_time(line.distance, self.add_time)
                    time[hub_iata][dst_iata][plane_id] = 2 * flight_time * flights[hub_iata][dst_iata][plane_id]

        return time

    def fuel_cons(self, day):
        pax = self.pax(day)

        fuel = {}
        for hub_iata, lines in self.lines.items():
            fuel[hub_iata] = {}
            for dst_iata, line in lines.items():
                fuel[hub_iata][dst_iata] = {}
                for plane_id in self.planes.keys():
                    total_pax = sum(pax[hub_iata][dst_iata][plane_id].values())
                    cons_per_pax = 0.01 * line.distance * self.planes[plane_id].cons
                    fuel[hub_iata][dst_iata][plane_id] = total_pax * cons_per_pax

        return fuel

    def turnovers(self, day):
        pax = self.pax(day)

        cash = {}
        for hub_iata, lines in self.lines.items():
            cash[hub_iata] = {}
            for dst_iata, line in lines.items():
                cash[hub_iata][dst_iata] = {}
                for plane_id in self.planes.keys():
                    cash[hub_iata][dst_iata][plane_id] = {}
                    for m in Market:
                        plane_pax = pax[hub_iata][dst_iata][plane_id][m.name]
                        cash[hub_iata][dst_iata][plane_id][m.name] = line.ticket_price[m.name] * plane_pax

        return cash

    def costs(self, day):
        fuel = self.fuel_cons(day)
        flights = self.flights(day)

        cash = {}
        for hub_iata, lines in self.lines.items():
            cash[hub_iata] = {}
            for dst_iata, line in lines.items():
                cash[hub_iata][dst_iata] = {}
                for plane_id in self.planes.keys():
                    cash[hub_iata][dst_iata][plane_id] = {}
                    fuel_cons = fuel[hub_iata][dst_iata][plane_id]
                    tax = flights[hub_iata][dst_iata][plane_id] * line.tax
                    pax = sum(self.planes[plane_id].pax.values())
                    for m in Market:
                        pax_ratio = self.planes[plane_id].pax[m.name] / float(pax)
                        cash[hub_iata][dst_iata][plane_id][m.name] = (fuel_cons * petrol_price + tax) * pax_ratio

        return cash

    def profits(self, day):
        turnover = self.turnovers(day)
        cost = self.costs(day)

        cash = {}
        for hub_iata, lines in self.lines.items():
            cash[hub_iata] = {}
            for dst_iata, line in lines.items():
                cash[hub_iata][dst_iata] = {}
                for plane_id in self.planes.keys():
                    cash[hub_iata][dst_iata][plane_id] = {}
                    for m in Market:
                        credit = turnover[hub_iata][dst_iata][plane_id][m.name]
                        debit = cost[hub_iata][dst_iata][plane_id][m.name]
                        cash[hub_iata][dst_iata][plane_id][m.name] = credit - debit

        return cash

    def profitability(self, day, loan_rate=0.01):
        flight_time = self.flight_time(day)
        profits = self.profits(day)
        planes_cost = self.total_planes_cost() * (1. + loan_rate)
        acq_cost = self.total_acq_cost() * (1. + loan_rate)

        percent = {}
        for hub_iata, lines in self.lines.items():
            percent[hub_iata] = {}
            for dst_iata, line in lines.items():
                percent[hub_iata][dst_iata] = {}
                for plane_id in self.planes.keys():
                    percent[hub_iata][dst_iata][plane_id] = {}
                    wear_ratio = self.planes[plane_id].wear_rate * flight_time[hub_iata][dst_iata][plane_id] / 100.
                    plane_eff_cost = self.planes[plane_id].price * wear_ratio + planes_cost
                    pax = sum(self.planes[plane_id].pax.values())
                    for m in Market:
                        pax_ratio = self.planes[plane_id].pax[m.name] / float(pax)
                        cash = 30 * profits[hub_iata][dst_iata][plane_id][m.name]
                        cost = pax_ratio * (plane_eff_cost + acq_cost)
                        try:
                            percent[hub_iata][dst_iata][plane_id][m.name] = cash / cost
                        except ZeroDivisionError:
                            percent[hub_iata][dst_iata][plane_id][m.name] = 0.

        return percent

    def margin(self, day, loan_rate=0.01, loan_period=30):
        flight_time = self.flight_time(day)
        profits = self.profits(day)
        costs = self.costs(day)

        percent = {}
        for hub_iata, lines in self.lines.items():
            percent[hub_iata] = {}
            count = len(self.planes) * len(self.lines) * len(lines)
            for dst_iata, line in lines.items():
                percent[hub_iata][dst_iata] = {}
                for plane_id in self.planes.keys():
                    percent[hub_iata][dst_iata][plane_id] = {}
                    wear_ratio = self.planes[plane_id].wear_rate * flight_time[hub_iata][dst_iata][plane_id] / 100.
                    plane_cost = self.planes[plane_id].price * (1. + wear_ratio + loan_rate) / (loan_period * 7)
                    acq_cost = (line.dst.price + line.hub.price) * (1 + loan_rate) / (loan_period * 7)
                    pax = sum(self.planes[plane_id].pax.values())
                    for m in Market:
                        pax_ratio = self.planes[plane_id].pax[m.name] / float(pax)
                        op_cost = costs[hub_iata][dst_iata][plane_id][m.name]
                        cash = profits[hub_iata][dst_iata][plane_id][m.name] - pax_ratio * (plane_cost + acq_cost)
                        cost = pax_ratio * (plane_cost + acq_cost + op_cost)
                        try:
                            percent[hub_iata][dst_iata][plane_id][m.name] = cash / cost / count
                        except ZeroDivisionError:
                            percent[hub_iata][dst_iata][plane_id][m.name] = 0.

        return percent

    def use_rate(self, day):
        flight_time = self.flight_time(day)

        percent = {}
        for hub_iata, lines in self.lines.items():
            percent[hub_iata] = {}
            for dst_iata, line in lines.items():
                percent[hub_iata][dst_iata] = {}
                for plane_id in self.planes.keys():
                    percent[hub_iata][dst_iata][plane_id] = flight_time[hub_iata][dst_iata][plane_id] / 24.

        return percent

    def reduce_by_plane_id(self, data, by_market=False):
        plane_data = self.by_plane_id(data, by_market)
        new_data = {}
        for plane_id in self.planes.keys():
            for hub_iata, lines in self.lines.items():
                for dst_iata, line, in lines.items():
                    if not by_market:
                        data_by_line = plane_data[hub_iata][dst_iata][plane_id]
                        try:
                            new_data[plane_id] += data_by_line
                        except KeyError:
                            new_data[plane_id] = data_by_line
                        continue

                    new_data[plane_id] = {}
                    for m in Market:
                        data_by_class = plane_data[hub_iata][dst_iata][plane_id][m.name]
                        try:
                            new_data[plane_id][m.name] += data_by_class
                        except KeyError:
                            new_data[plane_id][m.name] = data_by_class

        return new_data

    def by_hubs(self, data, by_market=False):
        line_data = self.by_lines(data, by_market)

        new_data = {}
        for hub_iata, lines in self.lines.items():
            if not by_market:
                new_data[hub_iata] = sum(line_data[hub_iata].values())
                continue

            new_data[hub_iata] = {}
            for dst_iata, line in lines.items():
                for m in Market:
                    data_by_class = line_data[hub_iata][dst_iata][m.name]
                    try:
                        new_data[hub_iata][m.name] += data_by_class
                    except KeyError:
                        new_data[hub_iata][m.name] = data_by_class

        return new_data

    def by_lines(self, data, by_market=False):
        plane_data = self.by_plane_id(data, by_market)

        new_data = {}
        for hub_iata, lines in self.lines.items():
            new_data[hub_iata] = {}
            for dst_iata, line in lines.items():
                if not by_market:
                    new_data[hub_iata][dst_iata] = sum(plane_data[hub_iata][dst_iata].values())
                    continue

                new_data[hub_iata][dst_iata] = {}
                for plane_id in self.planes.keys():
                    for m in Market:
                        data_by_class = plane_data[hub_iata][dst_iata][plane_id][m.name]
                        try:
                            new_data[hub_iata][dst_iata][m.name] += data_by_class
                        except KeyError:
                            new_data[hub_iata][dst_iata][m.name] = data_by_class

        return new_data

    def by_plane(self, data, by_market=False):
        plane_data = self.by_plane_id(data, by_market)

        new_data = {}
        for hub_iata, lines in self.lines.items():
            new_data[hub_iata] = {}
            for dst_iata, line in lines.items():
                new_data[hub_iata][dst_iata] = {}
                for plane_id, plane in self.planes.items():
                    if not by_market:
                        data_by_plane = plane_data[hub_iata][dst_iata][plane_id]
                        try:
                            new_data[hub_iata][dst_iata][plane.name] += data_by_plane
                        except KeyError:
                            new_data[hub_iata][dst_iata][plane.name] = data_by_plane
                        continue

                    new_data[hub_iata][dst_iata][plane.name] = {}
                    for m in Market:
                        data_by_class = plane_data[hub_iata][dst_iata][plane_id][m.name]
                        try:
                            new_data[hub_iata][dst_iata][plane.name][m.name] += data_by_class
                        except KeyError:
                            new_data[hub_iata][dst_iata][plane.name][m.name] = data_by_class

        return new_data

    def by_plane_id(self, data, by_market=False):
        new_data = {}
        for hub_iata, lines in self.lines.items():
            new_data[hub_iata] = {}
            for dst_iata, line in lines.items():
                new_data[hub_iata][dst_iata] = {}
                for plane_id in self.planes.keys():
                    if not by_market:
                        try:
                            new_data[hub_iata][dst_iata][plane_id] = sum(data[hub_iata][dst_iata][plane_id].values())
                        except AttributeError:
                            new_data[hub_iata][dst_iata][plane_id] = data[hub_iata][dst_iata][plane_id]
                        continue

                    try:
                        new_data[hub_iata][dst_iata][plane_id] = data[hub_iata][dst_iata][plane_id].copy()
                    except AttributeError:
                        new_data[hub_iata][dst_iata][plane_id] = {}
                        for m in Market:
                            new_data[hub_iata][dst_iata][plane_id][m.name] = data[hub_iata][dst_iata][plane_id] / 3.

        return new_data

    def generate_schedule(self):
        if self.schedule is None:
            raise NotImplementedError

        assert self.schedule_is_valid()

    def schedule_is_valid(self):
        if self.schedule == {}:
            return False

        for day in range(0, 7):
            use_rate = self.reduce_by_plane_id(self.use_rate(day))
            for plane_id in self.planes.keys():
                if use_rate[plane_id] > 1.:
                    return False

        return True


class FlatPlanning(Planning):
    def __init__(self, lines, planes, fill=0.86, add_time=1., target=Market.eco):
        self.target = target
        super().__init__(lines, planes, fill, add_time)

    def generate_schedule(self):
        self.schedule = {}
        excluded_planes = []
        for hub_iata, lines in self.lines.items():
            for dst_iata, line in lines.items():
                pax_rem = line.demand.copy()
                while pax_rem[self.target.name] > 0:
                    planes = list(filter(lambda x: True if x.range > line.distance else False, self.planes.values()))
                    planes = list(filter(lambda x: True if x.id not in excluded_planes else False, planes))
                    planes = sorted(planes, key=lambda x: x.price * x.match_demand(line)[self.target.name])

                    if len(planes) == 0:
                        break

                    flights = planes[0].flights_per_day(line.distance, self.add_time)
                    self.schedule[planes[0].id] = [[hub_iata + "-" + dst_iata] * flights] * 7
                    excluded_planes.append(planes[0].id)
                    for m in Market:
                        pax_rem[m.name] -= 2 * flights * planes[0].pax[m.name]

        super().generate_schedule()

    @classmethod
    def match(cls, target_lines, included_planes, fill=0.86, add_time=1., target=Market.eco):

        planes = {}
        for hub_iata, lines in target_lines.items():
            for dst_iata, line in lines.items():
                bench_plan = []
                for plane in included_planes:
                    planes_list = [copy.copy(plane) for _ in range(0, plane.match_demand(line, add_time)[target.name])]
                    planes_dict = Plane.id_with(hub_iata + "-" + dst_iata, planes_list)
                    bench_plan.append(FlatPlanning({hub_iata: {dst_iata: line}}, planes_dict, fill, add_time, target))

                bench_plan = sorted(bench_plan,
                                    key=lambda x: x.by_lines(x.profitability(0))[hub_iata][dst_iata],
                                    reverse=True)

                for plane in bench_plan[0].planes.values():
                    planes[plane.id] = plane

        return FlatPlanning(target_lines, planes, fill, add_time, target)


test_lines = {"HYD": {"ISB": scrap.JSON.lines["HYD"]["ISB"]}}
test_planes = [scrap.JSON.planes["Q-400"], scrap.JSON.planes["ERJ-190"]]

plan = FlatPlanning.match(test_lines, test_planes)

flights_data = plan.margin(0)
new_flights_data = plan.by_plane(flights_data, by_market=False)

print(new_flights_data)
