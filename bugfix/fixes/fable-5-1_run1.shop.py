"""ネットショップの計算・在庫・配送をまとめたモジュール。"""
from datetime import date, datetime, timedelta
import math

TAX_STANDARD = 0.10
TAX_REDUCED = 0.08
FREE_SHIPPING_FROM = 5000
BASE_SHIPPING = 500
REGION_SURCHARGE = {"hokkaido": 300, "okinawa": 800, "remote_island": 1200}
HOLIDAYS = {date(2026, 11, 23), date(2026, 12, 29), date(2026, 12, 30), date(2026, 12, 31)}
CUTOFF_HOUR = 15


# ---------- かご ----------
def add_item(item, cart=None):
    """かごに商品を追加して、かごを返す。cart を省略すると新しいかごを作る。"""
    if cart is None:
        cart = []
    cart.append(item)
    return cart


def remove_item(cart, name):
    """名前が一致する商品を全部外した新しいかごを返す。元のかごは変えない。"""
    return [i for i in cart if i["name"] != name]


def subtotal(cart):
    """商品の小計(円)。各商品は {'name','price','qty'}。"""
    total = 0
    for i in range(len(cart)):
        total += cart[i]["price"] * cart[i]["qty"]
    return total


def total_weight(cart):
    """かご全体の重さ(g)。weight が無い商品は 0 とみなす。"""
    return sum(i.get("weight", 0) * i["qty"] for i in cart)


# ---------- 割引・クーポン ----------
def discount_rate(total):
    """合計金額に応じた割引率。5000円以上で5%、10000円以上で10%。"""
    if total >= 10000:
        return 0.10
    if total >= 5000:
        return 0.05
    return 0.0


def apply_coupon(total, coupon):
    """クーポンを適用した金額を返す。coupon は None か {'kind','value','min_total'}。
    kind は 'percent'(value %引き)か 'fixed'(value 円引き)。min_total 未満なら適用しない。
    結果は 0 円未満にならない。"""
    if not coupon or total < coupon.get("min_total", 0):
        return total
    if coupon["kind"] == "percent":
        total = total * (100 - coupon["value"]) / 100
    elif coupon["kind"] == "fixed":
        total = total - coupon["value"]
    return max(0, int(total))


# ---------- 税 ----------
def round_yen(x):
    """円未満を四捨五入する(0.5は切り上げ)。"""
    return int(math.floor(x + 0.5))


def tax_amount(cart):
    """消費税額。食品(food=True)は8%、それ以外は10%。かご全体で合算してから四捨五入する。"""
    raw = 0.0
    for i in cart:
        rate = TAX_REDUCED if i.get("food") else TAX_STANDARD
        raw += i["price"] * i["qty"] * rate
    return round_yen(raw)


# ---------- 送料 ----------
def shipping_fee(total_after_discount, region=None, weight_g=0):
    """送料。割引後の金額が5000円以上なら基本送料は無料。地域加算と重量加算は無料にならない。
    重量加算は、5kgを超えた分を1kgごと(切り上げ)に100円。"""
    fee = 0 if total_after_discount >= FREE_SHIPPING_FROM else BASE_SHIPPING
    fee += REGION_SURCHARGE.get(region, 0)
    if weight_g > 5000:
        fee += math.ceil((weight_g - 5000) / 1000) * 100
    return fee


# ---------- 配送日 ----------
def is_business_day(d):
    return d.weekday() < 5 and d not in HOLIDAYS


def next_business_day(d):
    """d の翌営業日(土日・祝日を除く)。"""
    d += timedelta(days=1)
    while not is_business_day(d):
        d += timedelta(days=1)
    return d


def ship_date(ordered_at):
    """注文日時から発送日を決める。15時より前の営業日の注文は当日発送、それ以外は翌営業日。"""
    d = ordered_at.date()
    if is_business_day(d) and ordered_at.hour < CUTOFF_HOUR:
        return d
    return next_business_day(d)


# ---------- 在庫 ----------
class Stock:
    def __init__(self, counts):
        self.counts = dict(counts)

    def reserve(self, name, qty):
        """在庫を確保する。足りなければ ValueError。ちょうど全部は確保できる。"""
        have = self.counts.get(name, 0)
        if qty > have:
            raise ValueError(f"在庫不足: {name} ({have} < {qty})")
        self.counts[name] = have - qty

    def release(self, name, qty):
        self.counts[name] = self.counts.get(name, 0) + qty

    def low_stock(self, threshold):
        """在庫が threshold 以下の商品を、少ない順に (名前, 数) で返す。同数は名前順。"""
        low = [(n, c) for n, c in self.counts.items() if c <= threshold]
        return sorted(low, key=lambda t: (t[1], t[0]))


# ---------- 一覧表示 ----------
def total_pages(n_items, per_page):
    return max(1, -(-n_items // per_page))


def paginate(items, page, per_page):
    """page は 1 始まり。範囲外のページは空のリスト。"""
    if page < 1:
        return []
    start = (page - 1) * per_page
    return items[start:start + per_page]


# ---------- CSV ----------
def parse_csv_line(line):
    """ダブルクォートで囲まれた欄の中のカンマを区切りとして扱わない、簡単なCSV 1行の解析。"""
    fields, cur, quoted = [], "", False
    for ch in line:
        if ch == '"':
            quoted = not quoted
        elif ch == "," and not quoted:
            fields.append(cur)
            cur = ""
        else:
            cur += ch
    fields.append(cur)
    return fields


# ---------- ほかの道具(バグではない) ----------
def split_bill(total, people):
    """割り勘。端数は先頭の人から1円ずつ多く負担する。"""
    base, extra = divmod(total, people)
    return [base + (1 if i < extra else 0) for i in range(people)]


def slugify(text):
    """英数字以外をハイフンにして、小文字にする。"""
    out, prev = "", ""
    for ch in text.lower():
        c = ch if ch.isalnum() and ch.isascii() else "-"
        if c == "-" and prev == "-":
            continue
        out += c
        prev = c
    return out.strip("-")


def invoice(cart, coupon=None, region=None):
    """請求内容をまとめる。割引率→クーポンの順に適用し、送料は割引後の金額で決める。"""
    sub = subtotal(cart)
    after_rate = int(sub * (1 - discount_rate(sub)))
    after = apply_coupon(after_rate, coupon)
    ship = shipping_fee(after, region, total_weight(cart))
    tax = tax_amount(cart)
    return {"subtotal": sub, "after_discount": after, "shipping": ship, "tax": tax, "total": after + ship + tax}
