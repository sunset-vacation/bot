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
    vouches = mongoengine.IntField(default=0, min_value=0)

    @property
    def level(self) -> int:
        result = 0

        while True:
            if self.xp >= level_to_xp(result + 1):
                result += 1
            else:
                break

        return result


def get_user(user_id: int) -> User:
    account = User.objects.with_id(user_id)   # pylint: disable=no-member

    if account is not None:
        return account

    return User(user_id=user_id).save()


class Topic(mongoengine.Document):
    content = mongoengine.StringField()
    thumbnail = mongoengine.URLField()
    credit = mongoengine.StringField()
    thumbnail_approved = mongoengine.BooleanField()
