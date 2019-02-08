from enum import Enum
import numpy as np

add_time = 1.0  # hours
hours_day = 24  # hours / day
l_petrol_bar = 159.0  # L / barrel
petrol_price = 53.53 / l_petrol_bar  # $/L


class Market(Enum):
    eco = "economic"
    biz = "business"
    pre = "premium"


class Airport:

    def __init__(self, lat, lon, tax, price=0., iata=None, name=None, loc=None):
        self.lat = lat  # latitude
        self.lon = lon  # longitude
        self.tax = tax  # $/flights
        self.price = price  # acquisition price in $
        self.iata = iata  # IATA code of airport as string
        self.name = name  # name of the airport
        self.loc = loc  # Country, city and offset from GMT timezone in hours of airport

    @classmethod
    def from_dict(cls, airport):
        return Airport(lat=airport["lat"],
                       lon=airport["lon"],
                       tax=airport["tax"],
                       iata=airport["iata"],
                       name=airport["name"],
                       loc=airport["loc"])


class Plane:
    def __init__(self, name, pax, speed, cons, year, max_range=np.infty, price=0., wear_rate=0., id=None):
        self.id = id
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
        return int(np.floor(24. / (2 * self.flight_time(line))))

    def flight_time(self, line):
        return line.distance / self.speed  # in hours

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
                    np.round(line.demand[m.name] / (2 * self.pax[m.name] * flight_per_day)))
            except ZeroDivisionError:
                count_planes[m.name] = 0
                continue

        return count_planes


class Line:
    def __init__(self, hub, dst, demand, ticket_price=None, distance=None, new=False, tax=None):
        self.hub = hub  # departure hub Airport
        self.dst = dst  # destination Airport
        self.demand = demand  # pax hashed by market ("eco", "biz", "pre")
        self.ticket_price = ticket_price  # $ hashed by market ("eco", "biz", "pre")
        self.distance = distance  # km
        self.new = new  # True if the line has not been acquired yet
        self.tax = hub.tax + dst.tax if tax is None else tax

    def __dict__(self):
        return {
            "hub": self.hub.iata,
            "dst": self.dst.iata,
            "demand": self.demand,
            "ticket_price": self.ticket_price,
            "distance": self.distance,
            "new": self.new,
            "tax": self.tax
        }

    @classmethod
    def from_dict(cls, line, hub, dst):
        return Line(hub=hub,
                    dst=dst,
                    demand=line["demand"],
                    ticket_price=line["ticket_price"],
                    distance=line["distance"],
                    new=line["new"],
                    tax=line["tax"])
