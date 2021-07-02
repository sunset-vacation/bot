from typing import Callable, List, Optional, Type

from aiohttp import ClientSession
from discord import AsyncWebhookAdapter, Guild, Member, Webhook
from mongoengine import Document


def format_coins(amount: int) -> str:
    if amount < 0:
        return '- ⏣ {:,}'.format(abs(amount))

    return '⏣ {:,}'.format(amount)


def min_max_int(min_val: int, max_val: int) -> Callable[[str], int]:
    def inner(argument: str) -> int:
        argument = int(argument)
        assert min_val <= argument <= max_val
        return argument

    return inner


def optional_mention(user_id: int, guild: Guild) -> str:
    try:
        return guild.get_member(user_id).mention
    except AttributeError:
        return str(user_id)


def get_random_oids(collection, sample_size: int = 1):
    pipeline = [{'$project': {'_id': 1}}, {'$sample': {'size': sample_size}}]
    return [s['_id'] for s in collection.aggregate(pipeline)]


def get_random_documents(DocClass: Type[Document], sample_size: int = 1):
    doc_collection = DocClass._get_collection()
    random_oids = get_random_oids(doc_collection, sample_size)
    return DocClass.objects(id__in=random_oids)


def adapt_to_pronouns(member: Member, they: str, he: str, she: str):
    role_names: List[str] = [role.name.lower() for role in member.roles]

    if any('he/him' in name for name in role_names):
        return he
    elif any('she/her' in name for name in role_names):
        return she
    else:
        return they


async def send_webhook(
    webhook_url: str, content: Optional[str] = None, **send_kwargs
):
    async with ClientSession() as session:
        webhook = Webhook.from_url(
            webhook_url, adapter=AsyncWebhookAdapter(session)
        )
        await webhook.send(content, **send_kwargs)
