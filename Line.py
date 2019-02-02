class Line:
    def __init__(self, name, distance, tax, hub, demand, ticket_price=None, price=0., new=False):
        self.name = name
        self.distance = distance  # in km
        self.tax = tax  # in $/flight
        self.hub = hub
        self.demand = demand
        self.ticket_price = ticket_price  # in $
        self.price = price  # acquisition price
        self.new = new


