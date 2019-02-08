from model import *
import scrap


class Planning:
    def __init__(self, lines, planes, schedule=None, fill=0.86):
        self.lines = lines
        self.planes = planes
        self.schedule = {} if schedule is None else schedule
        self.fill = fill

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
                    flight_time = self.planes[plane_id].flight_time(line) + add_time
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

    def turnover(self, day):
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

    def cost(self, day):
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
                    tax = flights[hub_iata][dst_iata][plane_id] * (line.tax + line.hub.tax)
                    pax = sum(self.planes[plane_id].pax.values())
                    for m in Market:
                        pax_ratio = self.planes[plane_id].pax[m.name] / float(pax)
                        cash[hub_iata][dst_iata][plane_id][m.name] = (fuel_cons * petrol_price + tax) * pax_ratio

        return cash

    def profits(self, day):
        turnover = self.turnover(day)
        cost = self.cost(day)

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

        percent = {}
        for hub_iata, lines in self.lines.items():
            percent[hub_iata] = {}
            for dst_iata, line in lines.items():
                percent[hub_iata][dst_iata] = {}
                for plane_id in self.planes.keys():
                    percent[hub_iata][dst_iata][plane_id] = {}
                    wear_ratio = self.planes[plane_id].wear_rate * flight_time[hub_iata][dst_iata][plane_id]
                    plane_cost = self.planes[plane_id].price * (1. + wear_ratio + loan_rate)
                    acq_cost = line.tax + line.hub.tax
                    for m in Market:
                        cash = profits[hub_iata][dst_iata][plane_id][m.name]
                        percent[hub_iata][dst_iata][plane_id][m.name] = cash / (plane_cost + acq_cost)

        return percent

    def margin(self, day, loan_rate=0.01, loan_period=30):
        flight_time = self.flight_time(day)
        profits = self.profits(day)
        costs = self.cost(day)

        percent = {}
        for hub_iata, lines in self.lines.items():
            percent[hub_iata] = {}
            for dst_iata, line in lines.items():
                percent[hub_iata][dst_iata] = {}
                for plane_id in self.planes.keys():
                    percent[hub_iata][dst_iata][plane_id] = {}
                    wear_ratio = self.planes[plane_id].wear_rate * flight_time[hub_iata][dst_iata][plane_id]
                    plane_cost = self.planes[plane_id].price * (1. + wear_ratio + loan_rate) / (loan_period * 7)
                    acq_cost = (line.tax + line.hub.tax) * (1 + loan_rate) / (loan_period * 7)
                    for m in Market:
                        op_cost = costs[hub_iata][dst_iata][plane_id][m.name]
                        cash = profits[hub_iata][dst_iata][plane_id][m.name] - plane_cost - acq_cost
                        percent[hub_iata][dst_iata][plane_id][m.name] = cash / (plane_cost + acq_cost + op_cost)

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

    def reduce_by_plane(self, data, by_market=False):
        plane_data = self.by_plane(data, by_market)
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

    def by_hub(self, data, by_market=False):
        line_data = self.by_line(data, by_market)

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

    def by_line(self, data, by_market=False):
        plane_data = self.by_plane(data, by_market)

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

    def schedule_is_valid(self):
        if self.schedule == {}:
            return False

        for day in range(0, 7):
            use_rate = self.reduce_by_plane(self.use_rate(day))
            for plane_id in self.planes.keys():
                if use_rate[plane_id] > 1.:
                    return False

        return True


class FlatPlanning(Planning):
    def __init__(self, lines, planes, fill=0.86):
        super().__init__(lines, planes, fill=fill)
        self.generate_schedule()

    def generate_schedule(self):
        raise NotImplementedError


plan = Planning(
    {"HYD": {"ISB": scrap.JSON.lines["HYD"]["ISB"]}},
    {"Q-400-1": scrap.JSON.planes["Q-400"], "Q-400-2": scrap.JSON.planes["Q-400"]},
    {"Q-400-1": [["HYD-ISB", "HYD-ISB", "HYD-ISB"]] * 7, "Q-400-2": [["HYD-ISB", "HYD-ISB", "HYD-ISB"]] * 7}
)

flights_data = plan.profitability(0)
new_flights_data = plan.reduce_by_plane(flights_data, by_market=False)

print(new_flights_data)
print(plan.schedule_is_valid())
