"""
Data object model for airline.

This data models fits Airlines-Manager 2 data model. It provides commons abstractions
related to airlines and JSON serialization interface.
The module can be seen as a data model that simply represents an airline
in order to evaluate financial and planning performances.
"""

from enum import Enum
import numpy as np


class Market(Enum):
    """Enumeration giving labels for all the markets."""
    eco = "economic"
    biz = "business"
    pre = "premium"


class Airport:
    """
    Represents an airport.

    Attributes:
        lat (float): latitude in degrees
        lon (float): longitude in degrees
        tax (float): Tax per flights $/flight
        price (float): Acquisition price in $
        iata (str): IATA code of the airport
        name (str): Name of the airport use as label for displaying results
        loc (dict): Country, city and offset from GMT timezone in hours. eg. {"country":"UK", "city":"London", tmz:0}
    """

    def __init__(self, lat, lon, tax, price=0., iata=None, name=None, loc=None):
        self.lat = lat
        self.lon = lon
        self.tax = tax
        self.price = price
        self.iata = iata
        self.name = name
        self.loc = loc

    @classmethod
    def from_dict(cls, airport):
        return Airport(lat=airport["lat"],
                       lon=airport["lon"],
                       tax=airport["tax"],
                       iata=airport["iata"],
                       name=airport["name"],
                       loc=airport["loc"])


class Plane:
    """
    Represents a plane.

    Attributes:
        id (str): Identifier of the plane. Must be unique over fleet. If nothing is indicated, you can use standard
        airplanes identifiers such as F-AABB or VH-IRD...
        name (str): Name of the model of the plane. Since IATA codes for airplanes are not sufficiently exhaustive,
        the planes models are identifiers that can be found on AM2 planes purchase page.
        pax (dict): Aircraft capacity in terms of PAX. Indexed by market eg. {"eco": 80, "biz": 0, "pre": 0}
        speed (float): Cruise speed in km/h
        cons (float): Fuel consumption in L/100km/pax
        range (float): Range of the plane in km
        price (float): Acquisition price in dollars $
        wear_rate (float): Rate that indicates of fast the plane wears %/100h
        year (int): Year of release
    """

    def __init__(self, name, pax, speed, cons, year, plane_range=np.infty, price=0., wear_rate=0., plane_id=None):
        self.id = plane_id
        self.name = name
        self.pax = pax
        self.speed = speed
        self.cons = cons
        self.range = plane_range
        self.price = price
        self.wear_rate = wear_rate
        self.year = year

    def flights_per_day(self, distance, add_time=0.):
        """
        Computes number of flight per day.

        Parameters:
            distance (float): Distance to fly in km
            add_time (float): Additional landed time between flights in hours h

        Returns:
            Number of flights per day
        """
        return int(np.floor(24. / (2 * self.flight_time(distance, add_time))))

    def flight_time(self, distance, add_time=0.):
        """
        Computes flight time to distance.

        Parameters:
            distance (float): Distance to fly in km
            add_time (float): Additional landed in hours h

        Returns:
            Flight time in hours
        """
        return distance / self.speed + add_time

    def flight_time_verbose(self, distance, add_time=0.):
        """
        Creates a string representing flight time

        Parameters:
            distance (float): Distance to fly in km
            add_time (float): Additional landed in hours h

        Returns:
            flight time formatted as "HH:MM"
        """
        flight_time = self.flight_time(distance, add_time)
        hours = int(np.floor(flight_time))
        minutes = int((flight_time - hours) * 60.)
        return str.format("{:d}:{:d}", hours, minutes)

    def match_demand(self, line, add_time=0.):
        """
        Computes the number of planes necessary to fill the demand over a given line.

        Assuming the plane is fully
        dedicated to this line ie. it's use rate is maximum and there is no PAX remaining.

        Parameters:
            line (Line): Line to match
            add_time (float): Additional landed time between flights in hours h

        Returns:
            count_planes: Dictionary of numbers of planes to fill the demand indexed by market.
        """
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
        """
        Identifies given planes with prefix.

        After the method returns, the given planes are modified so their IDs
        correspond to the newly generated ID.

        ID are generated as follows : prefix + "-1", prefix + "-2", ...

        Parameters:
            prefix (str): Prefix string to identify airplanes eg. "HYD-ISB"
            planes (list): List of Plane objects to identify

        Returns:
            planes_dict: A dictionary of planes indexed by generated ID
        """
        planes_dict = {}
        for k in range(0, len(planes)):
            plane_id = prefix + "-{:d}".format(k + 1)
            planes_dict[plane_id] = planes[k]
            planes_dict[plane_id].id = plane_id
        return planes_dict


class Line:
    """
    Represents a line between two airports.

    Attributes:
        hub (Airport): Departure airport
        dst (Airport): Destination airport
        demand (dict): Dictionary of demand, indexed by market eg. {"eco": 3000, "biz":100, "pre":40}
        ticket_price (dict): Dictionary of ticket price indexed by market eg. {"eco": 300, "biz":600, "pre":1200}
        distance (dict): Distance between departure and destination in km
        new (bool): True if the line has not yet been acquired
        tax (float): Airport tax of the line in dollars per flight $/flight
    """

    def __init__(self, hub, dst, demand, ticket_price=None, distance=None, new=False, tax=None):
        self.hub = hub
        self.dst = dst
        self.demand = demand
        self.ticket_price = ticket_price
        self.distance = distance
        self.new = new
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
