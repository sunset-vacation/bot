from copy import copy
from datetime import timedelta
from typing import Optional
from uuid import uuid4

from better_profanity import profanity
from discord import Color, Embed, Member, Message
from discord.ext import commands
from discord.utils import get
from dislash import Button, ButtonStyle, SelectMenu, SelectOption
from tweepy import API as TwitterAPI
from tweepy import OAuthHandler as TwitterOAuthHandler

from config import CONFIG
from database import Topic, User
from utils import confirm_buttons, get_random_documents, send_webhook


def chat_only(ctx: commands.Context) -> bool:
    return ctx.channel.id == CONFIG.guild.channels.chat


def giveaways_only(ctx: commands.Context) -> bool:
    return ctx.channel.id == CONFIG.guild.channels.giveaways


twitter_auth = TwitterOAuthHandler(
    CONFIG.twitter.api_key, CONFIG.twitter.api_secret_key
)
twitter_auth.set_access_token(
    CONFIG.twitter.access_token, CONFIG.twitter.access_token_secret
)

twitter_api = TwitterAPI(twitter_auth)


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
            msg, on_click = await confirm_buttons(
                ctx, "Are you sure you'd like to turn off your leave status?"
            )

            @on_click.matching_id('yes_button')
            async def on_yes_button(inter):
                await ctx.author.remove_roles(
                    leave_role, reason='Self-toggled staff leave role'
                )

                await msg.edit(
                    components=[],
                    embed=Embed(
                        title='Turned staff leave off',
                        color=Color.green(),
                    ),
                )

        else:
            msg, on_click = await confirm_buttons(
                ctx, "Are you sure you'd like to turn on your leave status?"
            )

            @on_click.matching_id('yes_button')
            async def on_yes_button(inter):
                await ctx.author.add_roles(
                    leave_role, reason='Self-toggled staff leave role'
                )

                await msg.edit(
                    components=[],
                    embed=Embed(
                        title='Turned staff leave on',
                        color=Color.green(),
                    ),
                )

                if message:
                    embed = Embed(
                        description=profanity.censor(message, censor_char='•'),
                        color=Color.blurple(),
                    )
                    embed.set_author(
                        name=str(ctx.author), icon_url=ctx.author.avatar_url
                    )

                    await send_webhook(
                        CONFIG.guild.webhooks.leave, embed=embed
                    )

    @commands.command(name='genselfroles')
    @commands.is_owner()
    async def generate_self_roles(self, ctx):
        await ctx.send(
            embed=Embed(
                title='Select a category to view available roles',
                color=Color.blurple(),
            ),
            components=[
                SelectMenu(
                    custom_id='selfroles',
                    placeholder='Click me to select a category',
                    options=[
                        SelectOption(
                            'Ping roles',
                            'pings',
                            "Stay up-to-date with what's going on in our server",
                        ),
                        SelectOption(
                            'Color roles',
                            'colors',
                            'Change the color of your name',
                        ),
                        SelectOption(
                            'Age roles', 'ages', 'Tell others how old you are'
                        ),
                        SelectOption(
                            'Megaphone roles',
                            'megaphones',
                            'Get access to our fun megaphone channels',
                        ),
                        SelectOption(
                            'Pronoun roles',
                            'pronouns',
                            'Tell others how to refer to you',
                        ),
                        SelectOption(
                            'Continent roles',
                            'continents',
                            'Tell others where you live',
                        ),
                    ],
                )
            ],
        )

    def is_user_in_guild(self, user_id: int) -> bool:
        guild = self.bot.guilds[0]
        return guild.get_member(user_id) is not None

    @commands.command(name='cleandb')
    @commands.is_owner()
    async def clean_database(self, ctx):
        removed = 0

        for document in User.objects:
            if not self.is_user_in_guild(document.id):
                document.delete()
                removed += 1

        await ctx.reply(
            embed=Embed(
                title=f'Removed {removed} users from the database',
                color=Color.blurple(),
            )
        )

    @commands.command()
    @commands.is_owner()
    async def blacklisted(
        self, ctx: commands.Context, member: Member, time: str, *, reason: str
    ) -> None:
        """Notifies a user that they've been blacklisted from giveaways"""

        embed = Embed(
            title="You've been blacklisted from giveaways, lotteries, and events.",
            description='You can appeal '
            '[here](https://sunset.bsoyka.me/appeals) or undo this early by '
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

        await ctx.send(
            f'<@&{CONFIG.guild.roles.reviver}>',
            embed=embed,
            components=[
                Button(
                    style=ButtonStyle.link,
                    label='Share us on Twitter',
                    url='https://twitter.com/intent/tweet?text=I%27m%20a%20member%20of%20%40SunsetVacation_%2C%20a%20%23DiscordServer%20dedicated%20to%20fostering%20%23FriendshipsThatLast%21%0A%0ACome%20join%20us%21&url=https%3A%2F%2Fdiscord.gg%2FfFPEFYUnVp&via=SunsetVacation_&related=discord',
                )
            ],
        )

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
    async def tweet(self, ctx: commands.Context, *, message: str) -> None:
        """Tweets a message"""

        length = len(message)

        if length > 280:
            await ctx.reply(
                embed=Embed(
                    title='Message too long',
                    description=f'{length}/280 characters',
                    color=Color.red(),
                )
            )
            return

        _, on_click = await confirm_buttons(
            ctx, "Are you sure you'd like to send this Tweet?"
        )

        @on_click.matching_id('yes_button')
        async def on_yes_button(inter):
            status = twitter_api.update_status(message)
            await ctx.reply(
                f'https://twitter.com/{status.user.screen_name}/status/{status.id_str}'
            )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(StaffCog(bot))
