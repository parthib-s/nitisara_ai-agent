def estimate_rate(details):
    # Dummy estimator: just sum and base values
    size, weight, route, timeline = (
        details.get('size', 1),
        details.get('weight', 1),
        details.get('route', 'unknown'),
        details.get('timeline', 'standard')
    )
    base = 1000
    rate = base + float(weight) * 10 + float(size) * 5
    if timeline == 'express':
        rate *= 1.2
    return f"Estimated shipment rate for {route}: ${rate:.2f} ({timeline} delivery)."
