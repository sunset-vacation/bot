from asyncio import get_event_loop
from datetime import datetime
from functools import cache

import mongoengine
from discord import Guild, Member

from config import CONFIG

mongoengine.connect(host=CONFIG.secrets.mongodb_url)


@cache
def level_to_xp(level: int) -> int:
    return (level ** 3) + (level * 15)


class Afk(mongoengine.EmbeddedDocument):
    reason = mongoengine.StringField()
    old_nick = mongoengine.StringField()


class User(mongoengine.Document):
    user_id = mongoengine.IntField(primary_key=True)
    balance = mongoengine.IntField(default=0, min_value=0)
    donated = mongoengine.IntField(default=0, min_value=0)
    xp = mongoengine.IntField(default=0, min_value=0)
    afk = mongoengine.EmbeddedDocumentField(Afk, default=None)

    @property
    def level(self) -> int:
        result = 0

        while True:
            if self.xp >= level_to_xp(result + 1):
                result += 1
            else:
                break

        return result


class ScammerBan(mongoengine.Document):
    user_id = mongoengine.IntField(primary_key=True)
    proof = mongoengine.StringField()
    when = mongoengine.DateTimeField(default=datetime.now)


def get_user(user_id: int) -> User:
    account = User.objects.with_id(user_id)   # pylint: disable=no-member

    if account is not None:
        return account

    return User(user_id=user_id).save()


async def ban_scammer(guild: Guild, member: Member):
    await guild.ban(member, reason='Known scammer', delete_message_days=2)


def add_scammer_ban(user_id: int, guild: Guild, proof: str):
    ban = ScammerBan.objects.with_id(user_id)  # pylint: disable=no-member
    member = guild.get_member(user_id)

    if member is not None:
        get_event_loop().run_until_complete(ban_scammer(guild, member))

    if ban is None:
        ScammerBan(user_id=user_id, proof=proof).save()


def is_user_scammer(user_id: int) -> bool:
    ban = ScammerBan.objects.with_id(user_id)  # pylint: disable=no-member

    if ban is None:
        return False

    return True
