from fosspay.config import _cfg


class Currency:
    def __init__(self, symbol, position):
        self.symbol = symbol
        self.position = position

    def amount(self, amount):
        if self.position == "right":
            return amount + self.symbol
        else:
            return self.symbol + amount


currencies = {
    'aud': Currency("$", "left"),
    'usd': Currency("$", "left"),
    'eur': Currency("€", "right")
    # ... More currencies can be added here
}

currency = currencies[_cfg("currency")]
