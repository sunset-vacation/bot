from typing import Dict

from discord import Color, Embed, Guild, Member, Message, Role
from discord.ext.commands import Bot, Cog, Context, command, is_owner
from expiringdict import ExpiringDict

from config import CONFIG
from database import User as DbUser
from database import get_user, level_to_xp
from utils import min_max_int, optional_mention


class XPCog(Cog, name='XP and Leveling'):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.cooldowns = ExpiringDict(
            max_len=100, max_age_seconds=CONFIG.xp.cooldown
        )
        self.rewards: Dict[int, Role] = {
            int(level): role for level, role in CONFIG.xp.roles.items()
        }

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        if message.author.bot or message.guild == None:
            return

        if message.channel.id not in CONFIG.xp.channels:
            return

        user_id = message.author.id
        account = get_user(user_id)

        if self.cooldowns.get(user_id):
            return

        before_level = account.level
        account.xp += 1
        after_level = account.level

        if after_level > before_level:
            await self.level_up(message, after_level)

        account.save()

    async def level_up(self, message: Message, new_level: int) -> None:
        account = get_user(message.author.id)

        to_next = level_to_xp(new_level + 1) - account.xp
        congrats = 'Congrats, you are now at level {:,}! You need {:,} more XP to reach the next level.'.format(
            new_level, to_next
        )

        await self.add_level_roles(message.author, new_level, message.guild)

        try:
            await message.author.send(congrats)
        except:
            await message.reply(f'{message.author.mention} - {congrats}')

    async def add_level_roles(
        self, user: Member, new_level: int, guild: Guild
    ) -> None:
        get_role = lambda role_id: guild.get_role(role_id)

        earned_rewards = [
            get_role(role)
            for level, role in self.rewards.items()
            if new_level >= level
        ]

        await user.add_roles(*earned_rewards, reason='Level role update')

    @command(name='addxp')
    @is_owner()
    async def add_xp(self, ctx: Context, user: Member, amount: int) -> None:
        """Adds the specified amount of XP to a user"""

        account = get_user(user.id)
        account.xp += amount
        account.save()

        await ctx.message.add_reaction('✅')

    @command(aliases=['lb', 'top'])
    async def leaderboard(
        self, ctx: Context, limit: min_max_int(1, 20) = 10
    ) -> None:
        """Retrieves the specified number of top users by XP"""

        # pylint: disable=no-member

        top_ten = DbUser.objects().order_by('-xp')[:limit]

        lines = [
            '__**`{}`**__ {} - **{:,}** ({:,} XP)'.format(
                index,
                optional_mention(account.id, ctx.guild),
                account.level,
                account.xp,
            )
            for index, account in enumerate(top_ten, start=1)
        ]

        await ctx.reply(
            embed=Embed(
                title='Top Ten XP Users',
                description='\n'.join(lines),
                color=Color.blurple(),
            )
        )

    @command(name='fixalllevels')
    @is_owner()
    async def fix_all_levels(self, ctx: Context) -> None:
        for index, user in enumerate(ctx.guild.members):
            if user.bot:
                continue

            account = get_user(user.id)

            if account is not None:
                await self.add_level_roles(user, account.level, ctx.guild)
                await ctx.send(f'{index}. {user}')


def setup(bot: Bot) -> None:
    bot.add_cog(XPCog(bot))
