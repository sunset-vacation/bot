from typing import Callable, List, Optional, Type

from aiohttp import ClientSession
from discord import AsyncWebhookAdapter, Color, Embed, Guild, Member, Webhook
from discord.ext.commands import Context
from dislash import ActionRow, Button, ButtonStyle
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


async def confirm_buttons(ctx: Context, prompt: str):
    row_of_buttons = ActionRow(
        Button(
            style=ButtonStyle.green,
            label='Confirm',
            custom_id='yes_button',
        ),
        Button(
            style=ButtonStyle.red,
            label='Cancel',
            custom_id='no_button',
        ),
    )
    msg = await ctx.send(
        components=[row_of_buttons],
        embed=Embed(
            title=prompt,
            color=Color.blurple(),
        ),
    )

    on_click = msg.create_click_listener(timeout=180)

    @on_click.not_from_user(
        ctx.author, cancel_others=True, reset_timeout=False
    )
    async def on_wrong_user(inter):
        await inter.reply(
            embed=Embed(title="You're not the author", color=Color.red()),
            ephemeral=True,
        )

    @on_click.matching_id('no_button')
    async def on_no_button(inter):
        await msg.edit(
            components=[],
            embed=Embed(title='Operation cancelled', color=Color.red()),
        )

    @on_click.timeout
    async def on_timeout():
        await msg.edit(
            components=[],
            embed=Embed(
                title='Operation timed out',
                color=Color.red(),
            ),
        )

    return msg, on_click
