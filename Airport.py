class Airport:

    def __init__(self, lat, lon, tax, price=0., iata=None, name=None, location=None):
        self.lat = lat  # latitude
        self.lon = lon  # longitude
        self.tax = tax  # $/flights
        self.price = price  # acquisition price in $
        self.iata = iata  # IATA code of airport as string
        self.name = name  # name of the airport
        self.location = location  # Country, city and offset from GMT timezone in hours of airport
