from discord import Guild


def format_coins(amount: int):
    if amount < 0:
        return '- ⏣ {:,}'.format(abs(amount))

    return '⏣ {:,}'.format(amount)


def min_max_int(min_val: int, max_val: int):
    def inner(argument: str):
        argument = int(argument)
        assert min_val <= argument <= max_val
        return argument

    return inner


def optional_mention(user_id: int, guild: Guild):
    try:
        return guild.get_member(user_id).mention
    except AttributeError:
        return str(user_id)
