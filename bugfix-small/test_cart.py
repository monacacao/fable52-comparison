from datetime import date
import cart as c


def item(p, q=1):
    return {"name": "x", "price": p, "qty": q}


def test_add_item_independent_carts():
    a = c.add_item(item(100))
    b = c.add_item(item(200))
    assert len(a) == 1 and len(b) == 1


def test_subtotal_includes_first_item():
    assert c.subtotal([item(100, 2), item(300)]) == 500


def test_discount_boundaries():
    assert c.discount_rate(5000) == 0.05
    assert c.discount_rate(10000) == 0.10
    assert c.discount_rate(4999) == 0.0


def test_tax_rounds_half_up():
    assert c.tax(105) == 11
    assert c.tax(100) == 10


def test_split_bill_sums_and_even():
    r = c.split_bill(1000, 3)
    assert sum(r) == 1000 and len(r) == 3 and r[0] == 334


def test_days_until():
    assert c.days_until(date(2026, 11, 10), date(2026, 11, 10)) == 0
    assert c.days_until(date(2026, 11, 12), date(2026, 11, 10)) == 2


def test_checkout():
    cart = [item(5000), item(1000, 2)]
    assert c.checkout(cart) == 7000 * 0.95 + c.tax(7000 * 0.95)


def test_checkout_int():
    assert c.checkout([item(1000)]) == 1100
