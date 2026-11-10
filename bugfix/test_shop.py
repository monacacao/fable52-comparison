from datetime import date, datetime
import shop as s


def cart3():
    return [
        {"name": "ペン", "price": 150, "qty": 4, "weight": 20},
        {"name": "ノート", "price": 300, "qty": 2, "weight": 120},
        {"name": "米", "price": 2000, "qty": 1, "food": True, "weight": 5000},
    ]


def test_add_item_independent_carts():
    a = s.add_item({"name": "a", "price": 1, "qty": 1})
    b = s.add_item({"name": "b", "price": 1, "qty": 1})
    assert len(a) == 1 and len(b) == 1


def test_add_item_existing_cart():
    c = []
    s.add_item({"name": "a", "price": 1, "qty": 1}, c)
    assert len(c) == 1


def test_remove_item_keeps_original():
    c = cart3()
    r = s.remove_item(c, "ペン")
    assert len(c) == 3 and [i["name"] for i in r] == ["ノート", "米"]


def test_subtotal_includes_first_item():
    assert s.subtotal(cart3()) == 150 * 4 + 300 * 2 + 2000


def test_total_weight():
    assert s.total_weight(cart3()) == 80 + 240 + 5000
    assert s.total_weight([{"name": "x", "price": 1, "qty": 3}]) == 0


def test_discount_rate_boundaries():
    assert s.discount_rate(4999) == 0.0
    assert s.discount_rate(5000) == 0.05
    assert s.discount_rate(9999) == 0.05
    assert s.discount_rate(10000) == 0.10


def test_coupon_percent():
    assert s.apply_coupon(2000, {"kind": "percent", "value": 10}) == 1800


def test_coupon_fixed():
    assert s.apply_coupon(2000, {"kind": "fixed", "value": 500}) == 1500


def test_coupon_never_negative():
    assert s.apply_coupon(300, {"kind": "fixed", "value": 500}) == 0


def test_coupon_min_total():
    c = {"kind": "fixed", "value": 500, "min_total": 3000}
    assert s.apply_coupon(2999, c) == 2999
    assert s.apply_coupon(3000, c) == 2500


def test_coupon_none():
    assert s.apply_coupon(1234, None) == 1234


def test_round_yen_half_up():
    assert s.round_yen(10.5) == 11
    assert s.round_yen(10.49) == 10


def test_tax_mixed_rates():
    # ペン600+ノート600=1200→10%で120、米2000→8%で160、合計280
    assert s.tax_amount(cart3()) == 280


def test_tax_rounds_after_summing():
    c = [{"name": "a", "price": 105, "qty": 1}, {"name": "b", "price": 105, "qty": 1}]
    assert s.tax_amount(c) == 21


def test_shipping_free_after_discount():
    assert s.shipping_fee(5000) == 0
    assert s.shipping_fee(4999) == 500


def test_shipping_region_surcharge_not_free():
    assert s.shipping_fee(6000, "okinawa") == 800
    assert s.shipping_fee(3000, "hokkaido") == 800


def test_shipping_weight_surcharge():
    assert s.shipping_fee(6000, None, 5000) == 0
    assert s.shipping_fee(6000, None, 5001) == 100
    assert s.shipping_fee(6000, None, 7500) == 300


def test_business_day_weekend_and_holiday():
    assert s.is_business_day(date(2026, 11, 13))        # 金
    assert not s.is_business_day(date(2026, 11, 14))    # 土
    assert not s.is_business_day(date(2026, 11, 15))    # 日
    assert not s.is_business_day(date(2026, 11, 23))    # 祝日


def test_next_business_day_skips_weekend():
    assert s.next_business_day(date(2026, 11, 13)) == date(2026, 11, 16)
    assert s.next_business_day(date(2026, 11, 14)) == date(2026, 11, 16)


def test_next_business_day_skips_holiday():
    assert s.next_business_day(date(2026, 11, 20)) == date(2026, 11, 24)


def test_ship_date_cutoff():
    assert s.ship_date(datetime(2026, 11, 10, 14, 59)) == date(2026, 11, 10)
    assert s.ship_date(datetime(2026, 11, 10, 15, 0)) == date(2026, 11, 11)


def test_ship_date_weekend_order():
    assert s.ship_date(datetime(2026, 11, 14, 9, 0)) == date(2026, 11, 16)


def test_reserve_exact_stock():
    st = s.Stock({"a": 3})
    st.reserve("a", 3)
    assert st.counts["a"] == 0


def test_reserve_insufficient():
    st = s.Stock({"a": 3})
    try:
        st.reserve("a", 4)
    except ValueError:
        assert st.counts["a"] == 3
        return
    raise AssertionError("ValueError が出ませんでした")


def test_low_stock_order():
    st = s.Stock({"c": 2, "a": 2, "b": 0, "d": 9})
    assert st.low_stock(2) == [("b", 0), ("a", 2), ("c", 2)]


def test_pagination():
    items = list(range(1, 11))
    assert s.paginate(items, 1, 4) == [1, 2, 3, 4]
    assert s.paginate(items, 3, 4) == [9, 10]
    assert s.paginate(items, 4, 4) == []
    assert s.total_pages(10, 4) == 3
    assert s.total_pages(8, 4) == 2
    assert s.total_pages(0, 4) == 1


def test_parse_csv_quotes():
    assert s.parse_csv_line('1,"ペン,黒",150') == ["1", "ペン,黒", "150"]
    assert s.parse_csv_line("a,,c") == ["a", "", "c"]


def test_split_bill():
    assert s.split_bill(1000, 3) == [334, 333, 333]
    assert sum(s.split_bill(1001, 4)) == 1001


def test_slugify():
    assert s.slugify("Hello,  World!") == "hello-world"


def test_invoice_flow():
    inv = s.invoice(cart3())
    # 小計3200、割引なし、送料500+重量加算100(5320g)=600、税280
    assert inv == {"subtotal": 3200, "after_discount": 3200, "shipping": 600, "tax": 280, "total": 4080}


def test_invoice_discount_then_free_shipping():
    c = [{"name": "x", "price": 5200, "qty": 1}]
    inv = s.invoice(c)
    # 5200 → 5%引きで4940。割引後は5000未満なので送料500
    assert inv["after_discount"] == 4940 and inv["shipping"] == 500
