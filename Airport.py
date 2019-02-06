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
    def from_dict(self, airport):
        return Airport(lat=airport["lat"],
                       lon=airport["lon"],
                       tax=airport["tax"],
                       iata=airport["iata"],
                       name=airport["name"],
                       loc=airport["loc"])
