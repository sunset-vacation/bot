from typing import Optional

from discord import Color, Embed
from discord.ext.commands import Bot, Cog, Context, command, is_owner
from discord.ext.commands.core import has_role
from requests import patch

from config import CONFIG
from database import Topic
from utils import get_random_documents


def topic_embed(document: Topic):
    embed = Embed(
        title=document.content,
        color=Color.blurple(),
    )

    if document.thumbnail and document.thumbnail_approved:
        embed.set_thumbnail(url=document.thumbnail)

        if document.credit:
            embed.description = document.credit

    embed.set_footer(text=f'Conversation starter {document.id}')

    return embed


class FunCog(Cog, name='Fun'):
    def __init__(self, bot: Bot):
        self.bot = bot

    @command()
    async def topic(self, ctx: Context) -> None:
        """Displays a conversation starter"""

        document = get_random_documents(Topic, 1)[0]

        await ctx.reply(embed=topic_embed(document))

    @command(name='addtopics')
    @is_owner()
    async def add_topics(self, ctx: Context, *, topics_str: str) -> None:
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

    @command(name='topicphoto')
    @has_role(CONFIG.xp.roles['5'])
    async def set_topic_photo(
        self,
        ctx: Context,
        topic_id: str,
        url: str,
        *,
        credit: Optional[str] = None,
    ):
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

        document.save()

        patch(
            f'https://unbelievaboat.com/api/v1/guilds/{CONFIG.guild.id}/users/{ctx.author.id}',
            headers={'Authorization': CONFIG.secrets.unbelievaboat_auth},
            json={'cash': 20, 'reason': 'topic photo'},
        ).json()

        await ctx.reply(embed=topic_embed(document))


def setup(bot: Bot) -> None:
    bot.add_cog(FunCog(bot))