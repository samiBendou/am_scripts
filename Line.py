from Airport import Airport


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
