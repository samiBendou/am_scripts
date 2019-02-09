from enum import Enum
import numpy as np


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
    def __init__(self, name, pax, speed, cons, year, plane_range=np.infty, price=0., wear_rate=0., plane_id=None):
        self.id = plane_id
        self.name = name
        self.pax = pax
        self.speed = speed  # in km/h
        self.cons = cons  # in L/100km/pax
        self.range = plane_range
        self.price = price
        self.wear_rate = wear_rate
        self.year = year

    def flights_per_day(self, distance, add_time=0.):
        return int(np.floor(24. / (2 * self.flight_time(distance, add_time))))

    def flight_time(self, distance, add_time=0.):
        return distance / self.speed + add_time  # in hours

    def flight_time_verbose(self, distance, add_time=0.):
        flight_time = self.flight_time(distance, add_time)
        hours = int(np.floor(flight_time))
        minutes = int((flight_time - hours) * 60.)
        return str.format("{:d}:{:d}", hours, minutes)

    def match_demand(self, line, add_time=0.):
        count_planes = {}
        flight_per_day = self.flights_per_day(line.distance, add_time)

        for m in Market:
            try:
                count_planes[m.name] = int(np.round(line.demand[m.name] / (2 * self.pax[m.name] * flight_per_day)))
            except ZeroDivisionError:
                count_planes[m.name] = 0

        return count_planes

    @classmethod
    def from_dict(cls, plane):
        return Plane(name=plane["name"],
                     pax=plane["pax"],
                     speed=plane["speed"],
                     cons=plane["cons"],
                     plane_range=plane["range"],
                     price=plane["price"],
                     wear_rate=plane["wear_rate"],
                     year=plane["year"])

    @classmethod
    def id_with(cls, prefix, planes):
        planes_dict = {}
        for k in range(0, len(planes)):
            plane_id = prefix + "-{:d}".format(k + 1)
            planes_dict[plane_id] = planes[k]
            planes_dict[plane_id].id = plane_id
        return planes_dict


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
