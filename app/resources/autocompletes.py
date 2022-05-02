"""
Some nice autocomplete handlers that are used everywhere
"""

from resources import players


def amount_all(ctx, *args):
    """Some enhancements for int options"""
    player = players.get(ctx.author.id)
    amount = None
    for option in args:
        if option.name == "amount":
            amount = option
    lst = []
    if not amount:
        return []
    if len(amount.value) == 0 or amount.value in "all":
        lst.append({"name": "all", "value": player.money})
    if len(amount.value) == 0 or amount.value in "half":
        lst.append({"name": "half", "value": round(player.money / 2)})
    if amount.value.isnumeric() and player.money >= int(amount.value):
        lst.append({"name": amount.value, "value": int(amount.value)})
    if amount.value.isnumeric() and player.money >= int(amount.value) * 1000:
        lst.append({"name": f"{amount.value} thousand", "value": int(amount.value) * 1000})
    if amount.value.isnumeric() and player.money >= int(amount.value) * 1000000:
        lst.append({"name": f"{amount.value} million", "value": int(amount.value) * 1000000})

    return lst
