from math import ceil
from sys import stderr
from traceback import print_exception

from discord import Color, Embed
from discord.ext.commands import (
    BadArgument,
    Bot,
    CheckFailure,
    Cog,
    CommandInvokeError,
    CommandNotFound,
    CommandOnCooldown,
    Context,
    DisabledCommand,
    MissingRequiredArgument,
)


class ErrorHandlingCog(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_command_error(self, ctx: Context, error: Exception):
        if hasattr(ctx.command, 'on_error'):
            return

        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        if isinstance(error, CommandInvokeError):
            error = error.original

        if isinstance(error, CommandNotFound):
            pass
        elif isinstance(error, DisabledCommand):
            await ctx.reply(
                embed=Embed(
                    title='That command has been disabled.', color=Color.red()
                )
            )
        elif isinstance(error, CommandOnCooldown):
            await ctx.reply(
                embed=Embed(
                    title='That command is on cooldown.',
                    description=f'Try again in `{ceil(error.retry_after)}` '
                    'seconds.',
                    color=Color.red(),
                )
            )
        elif isinstance(error, CheckFailure):
            await ctx.reply(
                embed=Embed(
                    title="You can't use that command here.", color=Color.red()
                )
            )
        elif isinstance(error, BadArgument):
            await ctx.reply(
                embed=Embed(
                    title='One or more of the arguments provided is invalid.',
                    color=Color.red(),
                )
            )
            print_exception(
                type(error), error, error.__traceback__, file=stderr
            )
        elif isinstance(error, MissingRequiredArgument):
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


def setup(bot: Bot):
    bot.add_cog(ErrorHandlingCog(bot))
