"""Deterministic synthetic daily demand; no database writes in this module."""
from datetime import datetime, time, timedelta
from random import Random


def generate(day, customers, products, tz):
    """Customers: (id, channel); products: (id, retail_price)."""
    if day.weekday() == 6:
        raise ValueError('Sunday is not an operating day')
    if not customers or not products:
        raise ValueError('Active customers and products are required')
    rng = Random(day.toordinal())
    start = datetime.combine(day, time(6), tzinfo=tz)
    arrivals = sorted(rng.randrange(16 * 3600) for _ in range(rng.randint(150, 400)))
    result = []
    for i, seconds in enumerate(arrivals, 1):
        customer, channel = rng.choice(customers)
        lines = [(pid, rng.randint(1, 3), price)
                 for pid, price in rng.sample(products, rng.randint(1, min(5, len(products))))]
        result.append((f'DAY-{day:%Y%m%d}-{i:04d}', customer, channel,
                       start + timedelta(seconds=seconds), lines))
    return result
