from copy import copy
from dataclasses import dataclass
from datetime import timedelta
from re import findall
from time import time
from typing import Dict, Optional
from uuid import uuid4

import discord
from discord.ext import commands
from discord.utils import escape_markdown, get
from requests import get as get_url
from simpleeval import simple_eval

from config import CONFIG
from database import add_scammer_ban, get_user, is_user_scammer

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix=CONFIG.bot.prefix, case_insensitive=True, intents=intents
)
bot.remove_command('help')


@bot.event
async def on_ready() -> None:
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, name='!help in Sunset City'
        )
    )
    bot.last_welcome = 0
    print('Ready!')


@bot.event
async def on_member_join(member: discord.Member) -> None:
    if member.bot:
        return

    chat = get(bot.guilds[0].channels, id=CONFIG.guild.channels.chat)

    if is_user_scammer(member.id):
        try:
            await member.send(
                'Our records show that you have previously scammed another '
                'Dank Memer user. Because of this, you are not currently '
                'allowed entry into our server. If this is incorrect, you may '
                'appeal your punishment at '
                'https://sunsetcity.bsoyka.me/appeals.'
            )
        except:
            pass

        await chat.send(
            f"{member} tried to join us but doesn't belong here since we don't"
            ' like scammers.'
        )

        await member.ban(reason='Known scammer', delete_message_days=2)

        return

    embed = discord.Embed(
        title='Welcome to Sunset City!',
        description='We hope you enjoy your time here! Make sure to read '
        'through <#805161020946382871> so you know about our __rules__, '
        '__channels__, and other __important information__.\n\nReact in '
        '<#805309185826881566> for pings and other roles.',
        color=discord.Color.from_rgb(158, 0, 89),
    )
    embed.add_field(
        name='Contact staff:',
        value="Just send <@814371132059680799> a message! We'll get back to "
        'you as soon as possible.',
        inline=True,
    )
    embed.add_field(
        name='Information center:',
        value='**[Click here](https://sunsetcity.bsoyka.me)** to access our '
        'server rules and more.',
        inline=True,
    )
    embed.set_thumbnail(url=str(bot.guilds[0].icon_url))

    welcome_text = member.mention

    if time() - bot.last_welcome > 120:
        welcome_text += f' **<@&{CONFIG.guild.roles.welcomer}>**'

        bot.last_welcome = time()

    await chat.send(welcome_text, embed=embed)

    embed = discord.Embed(
        title='Sunset City Punishment Appeals',
        description='If you ever need to appeal a strike, mute, ban, or '
        'giveaway blacklist, click the link above. Welcome to the server!',
        url='https://sunsetcity.bsoyka.me/appeals',
        color=discord.Color.from_rgb(158, 0, 89),
    )
    embed.set_thumbnail(url=str(bot.guilds[0].icon_url))

    try:
        await member.send(
            "Welcome to Sunset City! Here's some information about our appeals"
            ' system:',
            embed=embed,
        )
    except:
        await chat.send(
            "I tried to DM you information about our appeals system but wasn't"
            ' able to reach you - try out `!appeal` in <#805164652794609684> '
            'to get the link!'
        )


@bot.command()
@commands.is_owner()
async def blacklisted(
    ctx: commands.Context, member: discord.Member, time: str, *, reason: str
) -> None:
    """Notifies a user that they've been blacklisted from giveaways"""

    embed = discord.Embed(
        title="You've been blacklisted from giveaways, lotteries, and events.",
        description='You can appeal '
        '[here](https://sunsetcity.bsoyka.me/appeals) or undo this early by '
        'purchasing `Escape Jail` from the UnbelievaBoat store.',
        color=discord.Color.red(),
    )
    embed.add_field(name='Time', value=time, inline=True)
    embed.add_field(name='Reason', value=reason, inline=True)

    try:
        await member.send(embed=embed)
    except:
        channel = get(
            bot.guilds[0].channels, id=CONFIG.guild.channels.blacklisted
        )
        await channel.send(member.mention, embed=embed)

    await ctx.message.add_reaction('✅')


@bot.command(name='gawreqs')
@commands.is_owner()
async def did_not_meet_reqs(
    ctx: commands.Context, member: discord.Member
) -> None:
    """Notifies a user that their giveaway reaction has been removed"""

    giveaway: discord.Message = ctx.message.reference.resolved
    jump = giveaway.jump_url

    await giveaway.remove_reaction('🎉', member)

    embed = discord.Embed(
        title='Your giveaway entry has been removed.',
        description=f'You did not meet/complete the requirements for [this giveaway]({jump}).',
        color=discord.Color.red(),
    )

    await member.send(embed=embed)

    await ctx.message.delete()


@bot.event
async def on_member_remove(member: discord.Member) -> None:
    if member.bot:
        return

    chat = get(bot.guilds[0].channels, id=CONFIG.guild.channels.chat)

    await chat.send(f'{member.name}#{member.discriminator} has left us.')


@bot.command()
@commands.has_role(CONFIG.guild.roles.moderator)
async def modnick(ctx: commands.Context, member: discord.Member) -> None:
    """Moderates the nickname of a member"""

    await member.edit(
        nick='Moderated name ' + str(uuid4())[:8],
        reason=f'Moderated by {ctx.author}',
    )
    await ctx.message.add_reaction('✅')


def chat_only(ctx: commands.Context) -> bool:
    return ctx.channel.id == CONFIG.guild.channels.chat


@bot.command()
@commands.has_role(CONFIG.guild.roles.helper)
@commands.cooldown(1, 3600, commands.BucketType.guild)
@commands.check(chat_only)
async def revive(
    ctx: commands.Context, *, topic: Optional[str] = None
) -> None:
    """Pings the chat revival role

    Can only be used in <#805289244049932319>.
    """

    embed = discord.Embed(title="Let's revive the chat!")
    embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)

    if topic:
        embed.description = topic

    await ctx.send(f'<@&{CONFIG.guild.roles.reviver}>', embed=embed)

    await ctx.message.delete()


@dataclass
class Guide:
    title: str
    content: str
    image: Optional[str] = None


guides_dict: Dict[str, Guide] = {
    'impersonation': Guide(
        title='How to tell if a user is the real Dank Memer',
        content='''
As a Dank Memer related server, we're highly susceptible to bot impersonation scams.

If a user that appears to be Dank Memer fails any of the checks below, please report them ASAP by messaging <@814371132059680799>.
‎
**Check the role!** Dank Memer has the <@&805916013790887978> role.
‎
**Dank Memer is verified!** Dank Memer has a blurple tag with a checkmark and the word BOT next to its name everywhere on Discord. (<:verified_bot:805935774088298556>)
‎
**Check the discriminator!** All Discord users have a four digit number at the end of their username. Dank Memer's is `5192`.
''',
    ),
    'earn': Guide(
        title='How to earn money in our economy system',
        content='''
**Be active in the server!** You'll get a random amount of coins between 5 and 25 per message every 5 minutes. This applies in:

• <#805289244049932319> and <#811698578753323059>
• <#815734968735105075>
• <#815397630325555281>
• <#815062519277813770>


**Win giveaways, lotteries, and events!** Coins and items will be given away occasionally.


**Collect income!** Certain roles can collect special income! Check **`!g income`** to see which roles this applies to.


**Work and commit crimes!** Try out the **`=work`** and **`=crime`** commands. Note that you might end up paying a fine when you commit a crime.''',
    ),
    'income': Guide(
        title='Roles that can use **`=collect-income`**',
        content='''
<@&813890540398444644>・<:sunset_coin:815373344832487524> **50** every 12 hours
<@&822191079574601728>・<:sunset_coin:815373344832487524> **50** every day
<@&806788705511407647>・<:sunset_coin:815373344832487524> **40** every day
<@&811698724072980561>・<:sunset_coin:815373344832487524> **35** every day
<@&805909324127928380>・<:sunset_coin:815373344832487524> **15** every 12 hours
<@&806796939705581609>・<:sunset_coin:815373344832487524> **25** every day (+5 per additional role)
<@&808196236368674856>・<:sunset_coin:815373344832487524> **20** every day
<@&810665824300826624>・<:sunset_coin:815373344832487524> **10** every day

__Learn more about these roles in <#810763036045738014>.__
''',
    ),
    'xp': Guide(
        title='Our XP and leveling system',
        content='''
We have our own XP system here at Sunset City!

You'll earn one XP point per message you send in any of the following channels with a cooldown of 12 seconds:

<#805289244049932319>, <#811698578753323059>, <#816392683391025224>, <#816382350502002760>, <#814303358869438535>, <#815062343930871838>, <#815062519277813770>

You can check your current XP and level with the `!me` command.

The total amount of XP points you'll need to reach a specific level is determined by the formula ` (level ^ 3) + (level * 15) `. This allows levels to require more work as they go on, as graphed below.
''',
        image='https://i.imgur.com/6Hpl8qr.png',
    ),
}


@bot.command(aliases=['g', 'guide'])
async def guides(ctx: commands.Context, guide: Optional[str] = None) -> None:
    """Shows a guide (or the list of guides if not specified)"""

    if guide == None:
        embed = discord.Embed(
            title='List of guide tags',
            color=discord.Color.blurple(),
        )

        for tag, guide in sorted(guides_dict.items()):
            embed.add_field(name=f'**`!g {tag}`**', value=guide.title)

        await ctx.reply('', embed=embed)
        return

    guide = guide.strip().lower()

    if guide not in guides_dict:
        await ctx.reply(
            '',
            embed=discord.Embed(
                title='Guide not found',
                description='Run the command again without any arguments to '
                'view the list of guide tags.',
                color=discord.Color.red(),
            ),
        )
        return

    requested = guides_dict[guide]

    embed = discord.Embed(
        title=requested.title,
        description=requested.content,
        color=discord.Color.blurple(),
    )

    if requested.image:
        embed.set_image(url=requested.image)

    await ctx.reply('', embed=embed)


@bot.command()
async def ping(ctx: commands.Context) -> None:
    """Shows the bot's latency"""

    embed = discord.Embed(title='Pong!', color=discord.Color.blurple())
    embed.add_field(
        name='Bot Latency', value=f'{round(bot.latency * 1000, 4)} ms'
    )

    await ctx.reply(embed=embed)


@bot.command()
@commands.is_owner()
async def sudo(
    ctx: commands.Context, user: discord.Member, *, command: str
) -> None:
    """Processes a command as if it was sent by another user"""
    fake_message = copy(ctx.message)

    fake_message.author = user
    fake_message.content = ctx.prefix + command

    await bot.process_commands(fake_message)
    await ctx.message.add_reaction('✅')


@bot.command(aliases=['me'])
async def user(
    ctx: commands.Context, user: Optional[discord.Member] = None
) -> None:
    """Shows basic details about a user

    This command will only display the current user's information unless
    the current user is a Helper+.
    """

    if (
        ctx.guild.get_role(CONFIG.guild.roles.helper) in ctx.author.roles
        and user != None
    ):
        user = user
    else:
        user = ctx.author

    if user.bot:
        await ctx.reply(
            embed=discord.Embed(
                title='This command cannot be used on bots.',
                color=discord.Color.red(),
            )
        )

    async with ctx.typing():
        account = get_user(user.id)

        embed = discord.Embed(
            title=user.display_name,
            description=f'{user.mention} - `{escape_markdown(str(user))}`',
            color=user.color,
            timestamp=user.joined_at,
        )

        if account is not None:
            if account.afk is not None:
                embed.add_field(
                    name='AFK Reason', value=account.afk.reason, inline=False
                )

        pronoun_roles = [
            role.mention
            for role in user.roles
            if role.id in CONFIG.guild.pronoun_roles
        ]

        if pronoun_roles:
            embed.add_field(name='Pronouns', value=', '.join(pronoun_roles))

        age_roles = [
            role.mention
            for role in user.roles
            if role.id in CONFIG.guild.age_roles
        ]

        if age_roles:
            embed.add_field(name='Age Range', value=age_roles[0])

        if account is not None:
            donated = '⏣ {:,}'.format(account.donated)
        else:
            donated = '⏣ 0'

        embed.add_field(
            name='Experience',
            value='Level {:,} ({:,} XP)'.format(account.level, account.xp),
        )

        embed.add_field(name='DMC Donated', value=donated)

        unb = get_url(
            f'https://unbelievaboat.com/api/v1/guilds/{CONFIG.guild.id}/users/{user.id}',
            headers={'Authorization': CONFIG.secrets.unbelievaboat_auth},
        ).json()
        embed.add_field(
            name='UnbelievaBoat Balance',
            value='<:sunset_coin:815373344832487524> {:,} (Rank: {:,})'.format(
                unb['total'], int(unb['rank'])
            ),
        )

        notif_roles = {
            CONFIG.guild.notification_roles.announcements: 'Announcements',
            CONFIG.guild.notification_roles.partnerships: 'Partnerships',
            CONFIG.guild.notification_roles.giveaways: 'Giveaways',
            CONFIG.guild.notification_roles.events: 'Events',
            CONFIG.guild.notification_roles.lotteries: 'Lotteries',
            CONFIG.guild.notification_roles.heists: 'Heists',
            CONFIG.guild.notification_roles.outside_heists: 'Outside heists',
            CONFIG.guild.notification_roles.suggestions: 'Suggestions',
            CONFIG.guild.notification_roles.new_members: 'New members',
            CONFIG.guild.notification_roles.chat_revival: 'Chat revival',
            CONFIG.guild.notification_roles.bump_reminders: 'Bump reminders',
        }

        roles = ', '.join(
            role.mention
            for role in user.roles[1:][::-1]
            if role.id
            not in {
                *CONFIG.guild.donation_roles.values(),
                *CONFIG.xp.roles.values(),
                CONFIG.guild.roles.member,
                *CONFIG.guild.pronoun_roles,
                *CONFIG.guild.age_roles,
                *notif_roles.keys(),
            }
        )
        embed.add_field(name='Other Roles', value=roles, inline=False)

        subscribed_to = [
            notif_roles[role.id]
            for role in user.roles
            if role.id in notif_roles
        ]

        if subscribed_to:
            embed.add_field(
                name='Notification Roles', value=', '.join(subscribed_to[::-1])
            )

        embed.set_footer(text=f'{user.id} - Joined at')

        embed.set_thumbnail(url=user.avatar_url)

    await ctx.reply(embed=embed)


@bot.command()
async def math(ctx: commands.Context, *, expression: str) -> None:
    """Evaluates a mathematical expression"""

    result = simple_eval(expression)

    await ctx.reply(
        embed=discord.Embed(
            title='Calculation Result',
            description=escape_markdown(str(result)),
            color=discord.Color.blurple(),
        )
    )


def giveaways_only(ctx: commands.Context) -> bool:
    return ctx.channel.id == CONFIG.guild.channels.giveaways


@bot.command()
@commands.check(giveaways_only)
async def claim(ctx: commands.Context, minutes: int) -> None:
    """Shows a claim time limit for a giveaway

    Must be used by replying to the giveaway winner message
    """

    winner_msg = ctx.message.reference.resolved
    end_time = winner_msg.created_at + timedelta(minutes=minutes)

    embed = discord.Embed(timestamp=end_time, color=discord.Color.blurple())
    embed.set_footer(text='Must DM host (not sponsor) to claim by')

    await winner_msg.reply('', embed=embed)
    await ctx.message.delete()


@bot.command()
@commands.is_owner()
async def dankdown(ctx: commands.Context) -> None:
    """Locks down Dank Memer channels"""

    channels = CONFIG.guild.dank_channels

    embed = discord.Embed(
        title='Dank Memer is down!',
        description='''
**You are not muted.** __All Dank Memer channels are locked until the bot comes back online.__

*(Note that just because the bot is online in another server doesn't mean it's online here.)*
''',
        color=discord.Color.red(),
    )
    embed.set_thumbnail(
        url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/240/'
        'apple/271/locked_1f512.png'
    )

    for channel_id in channels:
        channel = get(bot.guilds[0].channels, id=channel_id)

        overwrites = channel.overwrites_for(ctx.guild.default_role)
        overwrites.send_messages = False

        await channel.set_permissions(
            ctx.guild.default_role, overwrite=overwrites
        )
        await channel.send('', embed=embed)

    await ctx.reply('Locked down Dank Memer channels.')


@bot.command()
@commands.is_owner()
async def dankup(ctx: commands.Context) -> None:
    """Unlocks Dank Memer channels"""

    channels = CONFIG.guild.dank_channels

    embed = discord.Embed(
        title='Dank Memer is back!',
        description='''
Thank you for your patience.
''',
        color=discord.Color.red(),
    )
    embed.set_thumbnail(
        url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/'
        'thumbs/240/apple/271/unlocked_1f513.png'
    )

    for channel_id in channels:
        channel = get(bot.guilds[0].channels, id=channel_id)

        overwrites = channel.overwrites_for(ctx.guild.default_role)
        overwrites.send_messages = None

        await channel.set_permissions(
            ctx.guild.default_role, overwrite=overwrites
        )
        await channel.send('', embed=embed)

    await ctx.reply('Unlocked Dank Memer channels.')


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user:
        return

    if message.guild == None:
        await message.channel.send(
            "**Commands are disabled in DMs.** If you're trying to contact the"
            ' mods, reach out to <@814371132059680799> instead.'
        )
        return

    if message.channel.id == CONFIG.guild.channels.scammer_banner:
        for user_id in findall(r'(\d{10,})', message.content):
            add_scammer_ban(int(user_id), message.guild, message.jump_url)
            await message.add_reaction('✅')
            return

    if message.channel.id == CONFIG.guild.channels.outside_heists:
        await message.channel.send(
            embed=discord.Embed(
                title='Opt out',
                description='You can hide this channel by reacting to **[this message](https://discord.com/channels/805161020946382868/805309185826881566/824828154127712256)** with the :moneybag: emoji.',
                color=discord.Color.blurple(),
            )
        )
        return

    await bot.process_commands(message)


bot.load_extension('bank')
bot.load_extension('trading')
bot.load_extension('handling')
bot.load_extension('xp')
bot.load_extension('afk')
bot.load_extension('developer')
bot.load_extension('staff')
bot.load_extension('help')

bot.run(CONFIG.bot.token)
