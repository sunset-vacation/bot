from asyncio import sleep
from json import dump, load
from pathlib import Path
from re import match
from typing import Dict, Optional

from discord import Color, Embed, Member
from discord.ext.commands import Bot, Cog, Context, command, group, is_owner
from mongoengine import ValidationError

from config import CONFIG
from database import User as DbUser
from database import get_user
from utils import format_coins


class BankCog(Cog, name='Banking'):
    def __init__(self, bot: Bot):
        self.bot = bot

        self.donation_rewards: Dict[int, int] = {
            int(amount): role
            for amount, role in CONFIG.guild.donation_roles.items()
        }

    @command()
    async def bal(self, ctx: Context, user: Member = None) -> None:
        """Shows a user's balance

        This command will only display the current user's information unless the current user is the owner.
        """

        if self.bot.is_owner(ctx.author) and user != None:
            acct_user = user
        else:
            acct_user = ctx.author

        account = get_user(acct_user.id)

        bal = await ctx.reply(
            embed=Embed(
                title=f"{acct_user.name}'s Account Balance",
                description=format_coins(account.balance),
                color=Color.blurple(),
            )
        )

        if acct_user != ctx.author:
            await sleep(10)
            await bal.delete()

    @command(aliases=['dep'])
    @is_owner()
    async def deposit(
        self,
        ctx: Context,
        user: Member,
        amount: int,
        *,
        note: Optional[str] = None,
    ) -> None:
        """Adds coins to a user's balance"""

        account = get_user(user.id)
        account.balance += amount
        account.save()

        await ctx.message.add_reaction('✅')

        try:
            embed = Embed(title='DMC Deposited', color=Color.green())
            embed.add_field(name='Amount', value=format_coins(amount))
            embed.add_field(
                name='New Balance', value=format_coins(account.balance)
            )

            if note is not None:
                embed.description = note

            await user.send(embed=embed)
        except:
            await ctx.message.add_reaction('🤔')

    @command(aliases=["with"])
    @is_owner()
    async def withdraw(
        self,
        ctx: Context,
        user: Member,
        amount: int,
        *,
        note: Optional[str] = None,
    ) -> None:
        """Removes coins from a user's balance"""

        try:
            account = get_user(user.id)
            account.balance -= amount
            account.save()
        except ValidationError:
            await ctx.message.add_reaction('🚫')
            return

        await ctx.message.add_reaction('✅')

        try:
            embed = Embed(title='DMC Withdrawn', color=Color.red())
            embed.add_field(name='Amount', value=format_coins(amount))
            embed.add_field(
                name='New Balance', value=format_coins(account.balance)
            )

            if note is not None:
                embed.description = note

            await user.send(embed=embed)
        except:
            await ctx.message.add_reaction('🤔')

    @command()
    async def give(
        self,
        ctx: Context,
        user: Member,
        amount: int,
        *,
        note: Optional[str] = None,
    ) -> None:
        """Transfers coins to another user"""

        if amount <= 0:
            await ctx.reply(
                embed=Embed(
                    title='The transfer amount cannot be below 1.',
                    color=Color.red(),
                )
            )
            return

        if user.bot:
            await ctx.reply(
                embed=Embed(
                    title="You can't transfer coins to a bot.",
                    color=Color.red(),
                )
            )
            return

        if ctx.author == user:
            await ctx.reply(
                embed=Embed(
                    title="You can't transfer coins to yourself.",
                    color=Color.red(),
                )
            )
            return

        from_account = get_user(ctx.author.id)

        if from_account.balance < amount:
            await ctx.reply(
                embed=Embed(
                    title="You don't have enough coins in your account to send"
                    ' that much.',
                    color=Color.red(),
                )
            )
            return

        to_account = get_user(ctx.author.id)

        from_account.balance -= amount
        to_account.balance += amount

        from_embed = Embed(title='Outgoing DMC Transfer', color=Color.gold())
        from_embed.add_field(name='Amount', value=format_coins(amount))
        from_embed.add_field(
            name='New Balance', value=format_coins(from_account.balance)
        )
        from_embed.add_field(
            name='Recipient', value=user.mention, inline=False
        )

        to_embed = Embed(title='Incoming DMC Transfer', color=Color.gold())
        to_embed.add_field(name='Amount', value=format_coins(amount))
        to_embed.add_field(
            name='New Balance', value=format_coins(to_account.balance)
        )
        to_embed.add_field(
            name='Sender', value=ctx.author.mention, inline=False
        )

        if note is not None:
            from_embed.add_field(name='Note', value=note, inline=False)
            to_embed.add_field(
                name='Note from Sender', value=note, inline=False
            )

        try:
            await ctx.author.send(embed=from_embed)
        except:
            await ctx.send(
                ctx.author.mention + ", I wasn't able to DM you.",
                embed=from_embed,
            )

        try:
            await user.send(embed=to_embed)
        except:
            await ctx.send(
                user.mention + ", I wasn't able to DM you.", embed=to_embed
            )

        await ctx.message.add_reaction('✅')

    @command()
    @is_owner()
    async def extra(self, ctx: Context) -> None:
        """Checks how many coins are not reserved"""

        embed = Embed(
            title='Please check your balance here:',
            description='```\npls bal\n```',
            color=Color.blurple(),
        )
        instruction = await ctx.send(embed=embed)

        def check1(m):
            return (
                m.author == ctx.author
                and m.channel == ctx.channel
                and m.content.strip() == 'pls bal'
            )

        await self.bot.wait_for('message', check=check1)

        def check2(m):
            return (
                m.author.id == CONFIG.users.dank_memer
                and m.channel == ctx.channel
                and m.embeds
            )

        dank = await self.bot.wait_for('message', check=check2)
        emb_desc = dank.embeds[0].description

        groups = match(
            r'\*\*Wallet\*\*: \u23e3 ([\d,]+)\n\*\*Bank\*\*: \u23e3 ([\d,]+)',
            emb_desc,
        ).groups()

        wallet = int(groups[0].replace(',', ''))
        bank = int(groups[1].replace(',', ''))

        balance = wallet + bank
        banks = DbUser.objects().sum('balance')  # pylint: disable=no-member

        with (Path(__file__).parent / 'misc.json').open() as file:
            misc = load(file)

        leftover = balance - (banks + misc['giveaway_pool'])

        embed = Embed(title='Leftover Coins', color=Color.blurple())
        embed.add_field(name='Reserved in Accounts', value=format_coins(banks))
        embed.add_field(
            name='Reserved in Giveaway Pool',
            value=format_coins(misc['giveaway_pool']),
        )
        embed.add_field(
            name='Leftover',
            value='**' + format_coins(leftover) + '**',
            inline=False,
        )

        await ctx.reply(embed=embed)

        await instruction.delete()

    @group()
    async def pool(self, ctx: Context) -> None:
        """Commands for the giveaway pool"""

        if ctx.invoked_subcommand is None:
            with (Path(__file__).parent / 'misc.json').open() as file:
                misc = load(file)

            await ctx.reply(
                embed=Embed(
                    title='Current giveaway pool balance',
                    description=format_coins(misc['giveaway_pool']),
                    color=Color.blurple(),
                )
            )

    @pool.command(name='donate', aliases=['d'])
    async def pool_donate(self, ctx: Context, amount: int) -> None:
        """Donates an amount to the giveaway pool from your bank account"""

        account = get_user(ctx.author.id)

        if account.balance < amount:
            await ctx.reply(
                embed=Embed(
                    title="You don't have that much in your account!",
                    color=Color.red(),
                )
            )

        with (Path(__file__).parent / 'misc.json').open() as file:
            misc = load(file)

        misc['giveaway_pool'] += amount
        account.donated += amount
        account.balance -= amount

        with (Path(__file__).parent / 'misc.json').open('w') as file:
            dump(misc, file)

        account.save()

        get_role = lambda role_id: ctx.guild.get_role(role_id)

        earned_rewards = [
            get_role(role)
            for amount, role in self.donation_rewards.items()
            if account.donated >= amount
        ]
        await ctx.author.add_roles(
            *earned_rewards, reason='Giveaway donation role update'
        )

        await ctx.reply(
            embed=Embed(title='Donation recorded!', color=Color.green())
        )

    @pool.command(name='add', aliases=['a', 'change', 'c'])
    async def pool_add(self, ctx: Context, amount: int) -> None:
        """Changes the giveaway pool balance by the specified amount"""

        with (Path(__file__).parent / 'misc.json').open() as file:
            misc = load(file)

        misc['giveaway_pool'] += amount

        with (Path(__file__).parent / 'misc.json').open('w') as file:
            dump(misc, file)

        await ctx.reply(
            embed=Embed(title='Change recorded!', color=Color.green())
        )

    @command(name='donoadd')
    @is_owner()
    async def add_donation(
        self, ctx: Context, user: Member, amount: int
    ) -> None:
        """Adds a donation amount to a user"""

        account = get_user(user.id)
        account.donated += amount
        account.save()

        get_role = lambda role_id: ctx.guild.get_role(role_id)

        earned_rewards = [
            get_role(role)
            for amount, role in self.donation_rewards.items()
            if account.donated >= amount
        ]
        await user.add_roles(
            *earned_rewards, reason='Giveaway donation role update'
        )

        await ctx.message.add_reaction('✅')


def setup(bot: Bot) -> None:
    bot.add_cog(BankCog(bot))
