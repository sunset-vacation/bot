from discord import Color, Embed
from discord.ext.commands import Cog, command, has_role
from discord.utils import get

from config import CONFIG


class StaffCog(Cog, name='Staff Tools'):
    def __init__(self, bot):
        self.bot = bot

    @command()
    @has_role(CONFIG.guild.roles.staff)
    async def leave(self, ctx):
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


def setup(bot):
    bot.add_cog(StaffCog(bot))
