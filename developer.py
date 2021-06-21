from discord import TextChannel
from discord.ext.commands import Bot, Cog, Context, command


class DeveloperCog(Cog, name='Developer'):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_check(self, ctx: Context) -> bool:
        return await self.bot.is_owner(ctx.author)

    @command()
    async def load(self, ctx: Context, extension: str) -> None:
        """Loads an extension"""
        self.bot.load_extension(extension)
        await ctx.message.add_reaction('✅')

    @command()
    async def unload(self, ctx: Context, extension: str) -> None:
        """Unloads an extension"""
        self.bot.unload_extension(extension)
        await ctx.message.add_reaction('✅')

    @command(name='reload')
    async def reload_(self, ctx: Context, extension: str) -> None:
        """Reloads an extension"""
        self.bot.reload_extension(extension)
        await ctx.message.add_reaction('✅')

    @command()
    async def say(
        self, ctx: Context, channel: TextChannel, *, message: str
    ) -> None:
        await channel.send(message)
        await ctx.message.add_reaction('✅')


def setup(bot: Bot) -> None:
    bot.add_cog(DeveloperCog(bot))
