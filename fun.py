from random import choice
from typing import Optional

from discord import Color, Embed
from discord.ext.commands import Bot, Cog, Context, group, is_owner
from discord.ext.commands.core import has_role
from requests import patch

from config import CONFIG
from database import Topic
from utils import confirm_buttons, get_random_documents


def topic_embed(document: Topic, *, check_approval: bool = True):
    embed = Embed(
        title=document.content,
        color=Color.blurple(),
    )

    if document.thumbnail and (
        document.thumbnail_approved if check_approval else True
    ):
        embed.set_thumbnail(url=document.thumbnail)

        if document.credit:
            embed.description = document.credit

    embed.set_footer(text=f'Conversation starter {document.id}')

    return embed


class FunCog(Cog, name='Fun'):
    def __init__(self, bot: Bot):
        self.bot = bot

    @group()
    async def topic(self, ctx: Context) -> None:
        """Displays a conversation starter"""

        if ctx.invoked_subcommand is None:
            document = get_random_documents(Topic, 1)[0]

            await ctx.reply(embed=topic_embed(document))

    @topic.command(name='add', aliases=['a', '+'])
    @is_owner()
    async def add_topics(self, ctx: Context, *, topics_str: str) -> None:
        """Adds one or more topics to the database"""

        topics = topics_str.splitlines()

        for topic in topics:
            document = Topic(content=topic)
            document.save()

        await ctx.reply(
            embed=Embed(
                title=f'Created {len(topics)} new topic(s)',
                color=Color.blurple(),
            )
        )

    @topic.command(name='search', aliases=['s'])
    @is_owner()
    async def search_topics(self, ctx: Context, *, query: str) -> None:
        """Searches existing topics"""

        # pylint: disable=no-member

        embed = Embed(
            title=f'Search results for: {query}', color=Color.blurple()
        )
        for doc in Topic.objects(__raw__={'$text': {'$search': query}})[:10]:
            embed.add_field(name=doc.content, value=f'*{doc.id}*')

        await ctx.reply(embed=embed)

    @topic.command(name='photo', aliases=['p'])
    @has_role(CONFIG.xp.roles['5'])
    async def set_topic_photo(
        self,
        ctx: Context,
        topic_id: str,
        url: str,
        *,
        credit: Optional[str] = None,
    ):
        """Submits a photo for a topic for approval"""

        # pylint: disable=no-member

        document = Topic.objects.with_id(topic_id)

        if document.thumbnail:
            await ctx.reply(
                embed=Embed(
                    title='That topic already has a photo.', color=Color.red()
                )
            )
            return

        document.thumbnail = url
        document.credit = credit
        document.thumbnail_approved = False

        document.save()

        patch(
            f'https://unbelievaboat.com/api/v1/guilds/{CONFIG.guild.id}/users/{ctx.author.id}',
            headers={'Authorization': CONFIG.secrets.unbelievaboat_auth},
            json={'cash': 20, 'reason': 'topic photo'},
        ).json()

        await ctx.reply(embed=topic_embed(document, check_approval=False))

    @topic.command(name='unapproved', aliases=['u', 'up'])
    @is_owner()
    async def unapproved_topic_photo(self, ctx: Context) -> None:
        """Searches for a topic with an unapproved photo"""

        # pylint: disable=no-member

        results = Topic.objects(
            thumbnail__exists=True, thumbnail_approved=False
        )

        if not results:
            await ctx.reply(
                embed=Embed(
                    title='No more unapproved photos!', color=Color.red()
                )
            )
            return

        document = choice(results)

        await ctx.reply(embed=topic_embed(document, check_approval=False))

        msg, on_click = await confirm_buttons(
            ctx, 'Would you like to approve this photo?'
        )

        @on_click.matching_id('yes_button')
        async def on_yes_button(inter):
            document.thumbnail_approved = True
            document.save()

            await msg.edit(
                embed=Embed(title='Photo approved', color=Color.green()),
                components=[],
            )


def setup(bot: Bot) -> None:
    bot.add_cog(FunCog(bot))
