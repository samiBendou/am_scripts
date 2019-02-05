class Hub:
    def __init__(self, name, tax, acquired=True, price=0):
        self.name = name
        self.tax = tax
        self.acquire = acquired
        self.price = 0 if acquired else price
