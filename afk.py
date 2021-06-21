from datetime import datetime
from textwrap import shorten
from typing import Optional, Union

import discord
from discord.abc import Messageable
from discord.errors import Forbidden
from discord.ext.commands import Bot, Cog, Context, check, command, is_owner
from discord.utils import get

from config import CONFIG
from database import Afk as DbAfk
from database import User as DbUser
from database import get_user


def afk_access(ctx: Context) -> bool:
    return any(
        role.id in (CONFIG.guild.roles.afk_access, CONFIG.guild.roles.staff)
        for role in ctx.author.roles
    )


class AfkCog(Cog, name='AFK'):
    def __init__(self, bot: Bot):
        self.bot = bot

    @command(name='afk')
    @check(afk_access)
    async def afk_command(self, ctx: Context, *, reason: str) -> None:
        """Marks you as AFK

        Shows the given reason (shortened to 75 characters) when someone mentions you in Sunset City and adds `[AFK]` to your nickname

        AFK status is automatically removed when you start typing or send a message in our server
        """
        reason = shorten(reason, 75, placeholder='...')

        account = get_user(ctx.author.id)
        afk = DbAfk(reason=reason, old_nick=ctx.author.nick)

        try:
            await ctx.author.edit(nick='[AFK] ' + ctx.author.display_name)
        except Forbidden:
            pass

        account.afk = afk
        account.save()

        embed = discord.Embed(title='You have been marked AFK', color=discord.Color.blurple())
        embed.add_field(name='Reason', value=reason)
        embed.set_footer(
            text='This will be cleared automatically when you start typing in '
            'Sunset City'
        )

        await ctx.send(embed=embed, delete_after=5)
        await ctx.message.delete()

    @command(name='removeafk')
    @is_owner()
    async def remove_afk(self, ctx: Context, user: discord.Member) -> None:
        await self.remove_afk_if_needed(get_user(user.id), user, ctx.channel)
        await ctx.message.add_reaction('✅')

    async def remove_afk_if_needed(
        self,
        account: DbUser,
        user: discord.Member,
        channel: Optional[discord.TextChannel] = None,
    ) -> None:
        if account.afk is None:
            return

        if channel is None:
            channel = self.bot.get_channel(CONFIG.guild.channels.chat)

        try:
            await user.edit(nick=account.afk.old_nick)
        except Forbidden:
            pass

        await channel.send(
            user.mention,
            embed=discord.Embed(
                title='Your AFK status has been removed', color=discord.Color.blurple()
            ),
            delete_after=4,
        )

        del account.afk
        account.save()

    @Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        from_account = get_user(message.author.id)

        if from_account is not None:
            await self.remove_afk_if_needed(
                from_account, message.author, message.channel
            )

        for mentioned_user in message.mentions:
            if (
                mentioned_user.bot
                or self.bot.get_user(mentioned_user.id) is None
            ):
                return

            mentioned_account = get_user(mentioned_user.id)

            if mentioned_account is not None:
                if mentioned_account.afk is not None:
                    old_name = (
                        mentioned_account.afk.old_nick
                        if mentioned_account.afk.old_nick is not None
                        else mentioned_user.name
                    )

                    embed = discord.Embed(
                        title=f'{old_name} is currently AFK',
                        color=discord.Color.gold(),
                    )
                    embed.add_field(
                        name='Reason', value=mentioned_account.afk.reason
                    )
                    await message.reply(embed=embed, delete_after=8)

    @Cog.listener()
    async def on_typing(
        self, channel: Messageable, user: Union[discord.User, discord.Member], when: datetime
    ) -> None:
        if user.bot or type(user) != discord.Member:
            return

        from_account = get_user(user.id)

        if from_account is not None:
            await self.remove_afk_if_needed(from_account, user, channel)

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        user = self.bot.get_user(payload.user_id)

        if user.bot or payload.member is None:
            return

        from_account = get_user(user.id)

        if from_account is not None:
            await self.remove_afk_if_needed(from_account, payload.member)

    @Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        member = get(self.bot.guilds, id=CONFIG.guild.id).get_member(after.id)

        if member is None:
            return

        if member.bot:
            return

        from_account = get_user(member.id)

        if from_account is not None:
            await self.remove_afk_if_needed(from_account, member)

    @Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        user = self.bot.guilds[0].get_member(invite.inviter.id)

        if user is None:
            return

        if user.bot:
            return

        from_account = get_user(user.id)

        if from_account is not None:
            await self.remove_afk_if_needed(from_account, user)


def setup(bot) -> None:
    bot.add_cog(AfkCog(bot))
