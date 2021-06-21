from discord import Color, Embed, Member, User
from discord.ext import commands
from discord.utils import get

from config import CONFIG


class TradingCog(commands.Cog, name='Trading'):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(aliases=['mm'])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def middleman(self, ctx: commands.Context, user: Member) -> None:
        """Requests a middleman for a trade with a user"""

        if CONFIG.guild.roles.blacklisted in [
            role.id for role in ctx.author.roles
        ]:
            await ctx.reply(
                embed=Embed(
                    title="You're blacklisted from trading!",
                    description='**[Click here](https://www.notion.so/sunsetcity/Punishment-Appeals-6242fa8e28874e938c2588335c28bb18)** to appeal your punishment.',
                    color=Color.red(),
                )
            )
            return

        if CONFIG.guild.roles.blacklisted in [role.id for role in user.roles]:
            await ctx.reply(
                embed=Embed(
                    title='That user is blacklisted from trading.',
                    color=Color.red(),
                )
            )
            return

        if CONFIG.guild.roles.trading not in [
            role.id for role in ctx.author.roles
        ]:
            await ctx.reply(
                embed=Embed(
                    title="You haven't agreed to our trading rules yet!",
                    description='Head over to <#815069229974945822> to do so.',
                    color=Color.red(),
                )
            )
            return

        if CONFIG.guild.roles.trading not in [role.id for role in user.roles]:
            await ctx.reply(
                embed=Embed(
                    title="That user hasn't agreed to our trading rules yet.",
                    color=Color.red(),
                )
            )
            return

        if ctx.author == user:
            await ctx.reply(
                embed=Embed(
                    title="You can't trade with yourself!", color=Color.red()
                )
            )
            return

        if user.bot:
            await ctx.reply(
                embed=Embed(
                    title="You can't trade with bots!", color=Color.red()
                )
            )
            return

        channel = get(
            self.bot.guilds[0].channels, id=CONFIG.channels.middleman
        )
        role = get(self.bot.guilds[0].roles, id=CONFIG.guild.roles.middleman)

        embed = Embed(
            title='A user is looking for a middleman!', color=Color.blurple()
        )
        embed.add_field(name='User 1', value=ctx.author.mention, inline=True)
        embed.add_field(name='User 2', value=user.mention, inline=True)
        embed.add_field(
            name='Command to add users',
            value=f'```\n!ta {ctx.author.id} {user.id}```',
            inline=False,
        )

        await channel.send(role.mention, embed=embed)

        await ctx.reply(
            embed=Embed(
                title='A middleman request has been sent.',
                description="You'll be pinged when you're added to the trading channel. Please respond once added as soon as possible.",
                color=Color.blurple(),
            )
        )

    @commands.command()
    @commands.has_role(CONFIG.guild.roles.middleman)
    async def ta(self, ctx: commands.Context, *users: User) -> None:
        """Adds the specified users to the trading channel"""

        guild = self.bot.guilds[0]
        channel = get(guild.channels, id=CONFIG.channels.middleman)
        role = get(guild.roles, id=CONFIG.guild.roles.middleman_trading)

        for user in users:
            await guild.get_member(user.id).add_roles(role)

        embed = Embed(
            title="You've been added to this channel by a middleman.",
            description='Please follow all instructions from your middleman in this channel. Failure to do so may result in moderation action.',
            color=Color.blurple(),
        )
        embed.add_field(name='Your middleman', value=ctx.author.mention)
        embed.add_field(
            name='Command to remove users',
            value='```\n!tr '
            + ' '.join(str(user.id) for user in users)
            + '```',
            inline=False,
        )

        await channel.send(
            ' '.join(user.mention for user in users), embed=embed
        )

    @commands.command()
    @commands.has_role(CONFIG.guild.roles.middleman)
    async def tr(self, ctx: commands.Context, *users: User) -> None:
        """Removes the specified users from the trading channel"""

        guild = self.bot.guilds[0]
        role = get(guild.roles, id=CONFIG.guild.roles.middleman_trading)

        embed = Embed(
            title='Thank you for using our middleman service!',
            description='If you have any complaints about your middleman, please DM <@814371132059680799>.',
            color=Color.blurple(),
        )
        embed.set_footer(text='Have a great day!')

        for user in users:
            await guild.get_member(user.id).remove_roles(role)

            try:
                await user.send(embed=embed)
            except:
                pass

        await ctx.reply(embed=Embed(title='Success!', color=Color.blurple()))


def setup(bot: commands.Bot) -> None:
    bot.add_cog(TradingCog(bot))
