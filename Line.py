from Airport import Airport


class Line:
    def __init__(self, hub, dst, demand, ticket_price=None, distance=None, new=False):
        self.hub = hub  # departure hub Airport
        self.dst = dst  # destination Airport
        self.demand = demand  # pax hashed by market ("eco", "biz", "pre")
        self.ticket_price = ticket_price  # $ hashed by market ("eco", "biz", "pre")
        self.distance = distance  # km
        self.new = new  # True if the line has not been acquired yet
        self.tax = hub.tax + dst.tax
