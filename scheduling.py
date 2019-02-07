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
                    count[hub_iata][dst_iata][plane_id] = len(week_schedule[day])

        return count

    def pax(self, day):
        flights = self.flights(day)

        pax = {}
        for hub_iata, lines in self.lines.items():
            pax[hub_iata] = {}
            for dst_iata, line in lines.items():
                pax[hub_iata][dst_iata] = {}
                for plane_id, week_schedule in self.schedule.items():
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
                    for plane_id, week_schedule in self.schedule.items():
                        delta[hub_iata][dst_iata][m.name] -= pax[hub_iata][dst_iata][plane_id][m.name]

        return delta

    def flight_time(self, day):
        flights = self.flights(day)

        time = {}
        for hub_iata, lines in self.lines.items():
            time[hub_iata] = {}
            for dst_iata, line in lines.items():
                time[hub_iata][dst_iata] = {}
                for plane_id, week_schedule in self.schedule.items():
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
                for plane_id, week_schedule in self.schedule.items():
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
                for plane_id, week_schedule in self.schedule.items():
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
                for plane_id, week_schedule in self.schedule.items():
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
                for plane_id, week_schedule in self.schedule.items():
                    cash[hub_iata][dst_iata][plane_id] = {}
                    for m in Market:
                        credit = turnover[hub_iata][dst_iata][plane_id][m.name]
                        debit = cost[hub_iata][dst_iata][plane_id][m.name]
                        cash[hub_iata][dst_iata][plane_id][m.name] = credit - debit

        return cash

    def profitability(self, day):
        flight_time = self.flight_time(day)
        profits = self.profits(day)

        percent = {}
        for hub_iata, lines in self.lines.items():
            percent[hub_iata] = {}
            for dst_iata, line in lines.items():
                percent[hub_iata][dst_iata] = {}
                for plane_id, week_schedule in self.schedule.items():
                    percent[hub_iata][dst_iata][plane_id] = {}
                    wear_ratio = self.planes[plane_id].wear_rate * flight_time[hub_iata][dst_iata][plane_id]
                    plane_cost = self.planes[plane_id].price * (1. + wear_ratio)
                    acq_cost = line.tax + line.hub.tax
                    for m in Market:
                        cash = profits[hub_iata][dst_iata][plane_id][m.name]
                        percent[hub_iata][dst_iata][plane_id][m.name] = cash / (plane_cost + acq_cost)

        return percent


schedule = {"Q-400": [[0, 0, 0]] * 7}
plan = Planning({"HYD": {"ISB": scrap.JSON.lines["HYD"]["ISB"]}}, {"Q-400": scrap.JSON.planes["Q-400"]}, schedule)
data = plan.profitability(0)
print(data)
