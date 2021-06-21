from math import ceil
from sys import stderr
from traceback import print_exception

from discord import Color, Embed
from discord.ext import commands


class ErrorHandlingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        if hasattr(ctx.command, 'on_error'):
            return

        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        if isinstance(error, commands.CommandNotFound):
            pass
        elif isinstance(error, commands.DisabledCommand):
            await ctx.reply(
                embed=Embed(
                    title='That command has been disabled.', color=Color.red()
                )
            )
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(
                embed=Embed(
                    title='That command is on cooldown.',
                    description=f'Try again in `{ceil(error.retry_after)}` '
                    'seconds.',
                    color=Color.red(),
                )
            )
        elif isinstance(error, commands.CheckFailure):
            await ctx.reply(
                embed=Embed(
                    title="You can't use that command here.", color=Color.red()
                )
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.reply(
                embed=Embed(
                    title='One or more of the arguments provided is invalid.',
                    color=Color.red(),
                )
            )
            print_exception(
                type(error), error, error.__traceback__, file=stderr
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(
                embed=Embed(
                    title='One or more required arguments is missing.',
                    description=f'`{error.param.name}`',
                    color=Color.red(),
                )
            )
        else:
            embed = Embed(
                title='An unknown error has occurred.',
                color=Color.red(),
            )
            embed.add_field(name='Error type', value=type(error).__name__)

            await ctx.reply(embed=embed)

            print_exception(
                type(error), error, error.__traceback__, file=stderr
            )


def setup(bot: commands.Bot):
    bot.add_cog(ErrorHandlingCog(bot))
