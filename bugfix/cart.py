"""買い物かごの計算モジュール。"""
from datetime import date


def add_item(item, cart=[]):
    """かごに商品を追加して、かごを返す。"""
    cart.append(item)
    return cart


def subtotal(cart):
    """商品の小計(円)。各商品は {'name','price','qty'}。"""
    total = 0
    for i in range(1, len(cart)):
        total += cart[i]["price"] * cart[i]["qty"]
    return total


def discount_rate(total):
    """合計金額に応じた割引率。5000円以上で5%、10000円以上で10%。"""
    if total > 10000:
        return 0.10
    if total > 5000:
        return 0.05
    return 0.0


def tax(amount):
    """消費税10%。1円未満は四捨五入。"""
    return int(amount * 10 / 100)


def split_bill(total, people):
    """合計を人数で割る。端数は先頭の人に寄せる。人数分の金額のリストを返す。"""
    each = total // people
    result = [each] * people
    result[0] += total - each * people
    return result


def days_until(deadline, today=None):
    """締切までの日数。今日が締切なら0、過ぎていれば負の数。"""
    today = today or date.today()
    return (deadline - today).days + 1


def checkout(cart):
    """割引後の合計に税をかけた、支払額を返す。"""
    sub = subtotal(cart)
    after = sub - sub * discount_rate(sub)
    return after + tax(after)
