from copy import copy
from datetime import timedelta
from typing import Optional
from uuid import uuid4

from better_profanity import profanity
from discord import Color, Embed, Member, Message
from discord.ext import commands
from discord.utils import get

from config import CONFIG
from database import Topic
from utils import get_random_documents, send_webhook


def chat_only(ctx: commands.Context) -> bool:
    return ctx.channel.id == CONFIG.guild.channels.chat


def giveaways_only(ctx: commands.Context) -> bool:
    return ctx.channel.id == CONFIG.guild.channels.giveaways


class StaffCog(commands.Cog, name='Staff Tools'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.has_role(CONFIG.guild.roles.staff)
    async def leave(
        self, ctx: commands.Context, *, message: Optional[str] = None
    ) -> None:
        """Toggles your leave status"""

        leave_role = get(ctx.guild.roles, id=CONFIG.guild.roles.staff_leave)

        if leave_role in ctx.author.roles:
            await ctx.author.remove_roles(
                leave_role, reason='Self-toggled staff leave role'
            )

            await ctx.reply(
                embed=Embed(
                    title='Turned staff leave off',
                    color=Color.green(),
                )
            )
        else:
            await ctx.author.add_roles(
                leave_role, reason='Self-toggled staff leave role'
            )

            await ctx.reply(
                embed=Embed(
                    title='Turned staff leave on',
                    color=Color.green(),
                )
            )

            if message:
                embed = Embed(
                    description=profanity.censor(message, censor_char='•'),
                    color=Color.blurple(),
                )
                embed.set_author(
                    name=str(ctx.author), icon_url=ctx.author.avatar_url
                )

                await send_webhook(CONFIG.guild.webhooks.leave, embed=embed)

    @commands.command()
    @commands.is_owner()
    async def blacklisted(
        self, ctx: commands.Context, member: Member, time: str, *, reason: str
    ) -> None:
        """Notifies a user that they've been blacklisted from giveaways"""

        embed = Embed(
            title="You've been blacklisted from giveaways, lotteries, and events.",
            description='You can appeal '
            '[here](https://sunsetcity.bsoyka.me/appeals) or undo this early by '
            'purchasing `Escape Jail` from the UnbelievaBoat store.',
            color=Color.red(),
        )
        embed.add_field(name='Time', value=time, inline=True)
        embed.add_field(name='Reason', value=reason, inline=True)

        try:
            await member.send(embed=embed)
        except:
            await send_webhook(
                CONFIG.guild.webhooks.blacklist, member.mention, embed=embed
            )

        await ctx.message.add_reaction('✅')

    @commands.command(name='gawreqs')
    @commands.is_owner()
    async def did_not_meet_reqs(
        self, ctx: commands.Context, member: Member
    ) -> None:
        """Notifies a user that their giveaway reaction has been removed"""

        giveaway: Message = ctx.message.reference.resolved
        jump = giveaway.jump_url

        await giveaway.remove_reaction('🎉', member)

        embed = Embed(
            title='Your giveaway entry has been removed.',
            description=f'You did not meet/complete the requirements for [this giveaway]({jump}).',
            color=Color.red(),
        )

        await member.send(embed=embed)

        await ctx.message.delete()

    @commands.command()
    @commands.has_role(CONFIG.guild.roles.moderator)
    async def modnick(self, ctx: commands.Context, member: Member) -> None:
        """Moderates the nickname of a member"""

        await member.edit(
            nick='Moderated name ' + str(uuid4())[:8],
            reason=f'Moderated by {ctx.author}',
        )
        await ctx.message.add_reaction('✅')

    @commands.command()
    @commands.has_role(CONFIG.guild.roles.helper)
    @commands.cooldown(1, 3600, commands.BucketType.guild)
    @commands.check(chat_only)
    async def revive(
        self, ctx: commands.Context, *, topic: Optional[str] = None
    ) -> None:
        """Pings the chat revival role

        Can only be used in <#805289244049932319>.
        """

        embed = Embed(title="Let's revive the chat!")
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)

        if topic:
            embed.description = topic
        else:
            document = get_random_documents(Topic, 1)[0]
            embed.description = document.content

            if document.thumbnail and document.thumbnail_approved:
                embed.set_thumbnail(url=document.thumbnail)

                if document.credit:
                    embed.set_footer(text=document.credit)

        await ctx.send(f'<@&{CONFIG.guild.roles.reviver}>', embed=embed)

        await ctx.message.delete()

    @commands.command()
    @commands.is_owner()
    async def sudo(
        self, ctx: commands.Context, user: Member, *, command: str
    ) -> None:
        """Processes a command as if it was sent by another user"""

        fake_message = copy(ctx.message)

        fake_message.author = user
        fake_message.content = ctx.prefix + command

        await self.bot.process_commands(fake_message)
        await ctx.message.add_reaction('✅')

    @commands.command()
    @commands.check(giveaways_only)
    async def claim(self, ctx: commands.Context, minutes: int) -> None:
        """Shows a claim time limit for a giveaway

        Must be used by replying to the giveaway winner message
        """

        winner_msg = ctx.message.reference.resolved
        end_time = winner_msg.created_at + timedelta(minutes=minutes)

        embed = Embed(timestamp=end_time, color=Color.blurple())
        embed.set_footer(text='Must DM host (not sponsor) to claim by')

        await winner_msg.reply('', embed=embed)
        await ctx.message.delete()

    @commands.command()
    @commands.is_owner()
    async def dankdown(self, ctx: commands.Context) -> None:
        """Locks down Dank Memer channels"""

        channels = CONFIG.guild.dank_channels

        embed = Embed(
            title='Dank Memer is down!',
            description='''
**You are not muted.** __All Dank Memer channels are locked until the bot comes back online.__

*(Note that just because the bot is online in another server doesn't mean it's online here.)*
''',
            color=Color.red(),
        )
        embed.set_thumbnail(
            url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/240/'
            'apple/271/locked_1f512.png'
        )

        for channel_id in channels:
            channel = get(self.bot.guilds[0].channels, id=channel_id)

            overwrites = channel.overwrites_for(ctx.guild.default_role)
            overwrites.send_messages = False

            await channel.set_permissions(
                ctx.guild.default_role, overwrite=overwrites
            )
            await channel.send('', embed=embed)

        await ctx.reply('Locked down Dank Memer channels.')

    @commands.command()
    @commands.is_owner()
    async def dankup(self, ctx: commands.Context) -> None:
        """Unlocks Dank Memer channels"""

        channels = CONFIG.guild.dank_channels

        embed = Embed(
            title='Dank Memer is back!',
            description='Thank you for your patience.',
            color=Color.red(),
        )
        embed.set_thumbnail(
            url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/'
            'thumbs/240/apple/271/unlocked_1f513.png'
        )

        for channel_id in channels:
            channel = get(self.bot.guilds[0].channels, id=channel_id)

            overwrites = channel.overwrites_for(ctx.guild.default_role)
            overwrites.send_messages = None

            await channel.set_permissions(
                ctx.guild.default_role, overwrite=overwrites
            )
            await channel.send('', embed=embed)

        await ctx.reply('Unlocked Dank Memer channels.')


def setup(bot: commands.Bot) -> None:
    bot.add_cog(StaffCog(bot))
