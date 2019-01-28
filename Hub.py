class Hub:
    def __init__(self, tax, acquired=True, price=0):
        self.tax = tax
        self.acquire = acquired
        self.price = 0 if acquired else price
