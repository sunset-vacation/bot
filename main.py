from dataclasses import dataclass
from time import time
from typing import Dict, Optional

import discord
from discord.ext import commands
from discord.utils import escape_markdown, get
from dislash import (
    Button,
    ButtonStyle,
    MessageInteraction,
    SlashClient,
    auto_rows,
)
from requests import get as get_url
from simpleeval import simple_eval

from config import CONFIG
from database import get_user

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix=CONFIG.bot.prefix, case_insensitive=True, intents=intents
)
# bot.remove_command('help')

slash = SlashClient(bot)


@bot.event
async def on_ready() -> None:
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, name='!help in Sunset Vacation'
        )
    )
    bot.last_welcome = 0
    print('Ready!')


@bot.event
async def on_member_join(member: discord.Member) -> None:
    if member.bot:
        return

    chat = get(bot.guilds[0].channels, id=CONFIG.guild.channels.chat)

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
        value='**[Click here](https://sunset.bsoyka.me)** to access our '
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
        url='https://sunset.bsoyka.me/appeals',
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


@bot.event
async def on_member_remove(member: discord.Member) -> None:
    if member.bot:
        return

    chat = get(bot.guilds[0].channels, id=CONFIG.guild.channels.chat)

    await chat.send(f'{member.name}#{member.discriminator} has left us.')


def user_has_role(member: discord.Member, role_id: int) -> bool:
    return any(r.id == role_id for r in member.roles)


@bot.event
async def on_dropdown(inter: MessageInteraction):
    if inter.component.custom_id != 'selfroles':
        return

    if inter.select_menu.selected_options[0].value == 'colors' and all(
        not user_has_role(inter.author, r)
        for r in [
            CONFIG.guild.roles.staff,
            CONFIG.guild.roles.vip,
            816915687133151254,
        ]
    ):
        await inter.reply(
            "You don't have permission to access those roles.", ephemeral=True
        )
        return

    roles = {
        'pings': [
            ('Announements', 805309692720054313),
            ('Giveaways', 805309733808111626),
            ('Events', 808618482592645160),
            ('Heists', 844020589060423680),
            ('Outside heists', 844009948828663841),
            ('Suggestions', 806217674739810315),
            ('New members', 806661390512947201),
            ('Chat revival', 822189272298815509),
            ('Disboard bumps', 815398025430171679),
        ],
        'colors': [
            ('Bronze', 816911841468481567),
            ('Lemon', 816911905851572246),
            ('Emerald', 816911951657041920),
            ('Sky', 816912055675125760),
            ('Indigo', 816912112206872576),
            ('Grape', 816912161485488129),
        ],
        'ages': [
            ('13-17', 831420695018733598),
            ('18-24', 831420733006544906),
            ('25+', 831420769024213023),
        ],
        'megaphones': [
            ('Questions', 835011913430597642),
            ('Facts', 835011978304946207),
            ('Photos', 835012036642865153),
        ],
        'pronouns': [
            ('He/him', 854076070127337472),
            ('She/her', 854076069350342667),
            ('They/them', 854076068952801320),
            ('Ask me', 854076068406362172),
            ('Any pronouns', 854076067392389141),
        ],
        'continents': [
            ('North America', 855185170705416203),
            ('South America', 855185263428370451),
            ('Africa', 855185368306155593),
            ('Asia', 855185423873081385),
            ('Antarctica', 855185477925208074),
            ('Europe', 855185537853292554),
            ('Australia', 855185621295169547),
        ],
    }[inter.select_menu.selected_options[0].value]

    buttons = [
        Button(
            style=ButtonStyle.green
            if user_has_role(inter.author, role_id)
            else ButtonStyle.red,
            label=name,
            custom_id=str(role_id),
        )
        for name, role_id in roles
    ]

    msg = await inter.reply(
        'Click the buttons below to toggle your roles:',
        ephemeral=True,
        components=auto_rows(*buttons),
    )

    on_click = msg.create_click_listener(timeout=60)

    @on_click.no_checks()
    async def on_button(inter: MessageInteraction):
        role_id = int(inter.component.custom_id)
        role = get(inter.guild.roles, id=role_id)

        if user_has_role(inter.author, role_id):
            await inter.author.remove_roles(role, reason='Self role')
            await inter.reply(
                f'Removed the {role.mention} role', ephemeral=True
            )
        else:
            await inter.author.add_roles(role, reason='Self role')
            await inter.reply(
                f'Gave you the {role.mention} role', ephemeral=True
            )


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

    if guide is None:
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

    embed = discord.Embed(title='Pong! 🏓', color=discord.Color.blurple())
    embed.add_field(
        name='Bot Latency', value=f'{round(bot.latency * 1000, 4)} ms'
    )

    await ctx.reply(embed=embed)


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

        if account is not None and account.afk is not None:
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

        embed.add_field(
            name='Experience',
            value='Level {:,} ({:,} XP)'.format(account.level, account.xp),
        )

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
                *CONFIG.xp.roles.values(),
                CONFIG.guild.roles.member,
                *CONFIG.guild.pronoun_roles,
                *CONFIG.guild.age_roles,
                *notif_roles.keys(),
            }
        )

        if roles:
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


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user:
        return

    if message.guild is None:
        await message.channel.send(
            "**Commands are disabled in DMs.** If you're trying to contact the"
            ' mods, reach out to <@814371132059680799> instead.'
        )
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


bot.load_extension('handling')
bot.load_extension('xp')
bot.load_extension('afk')
bot.load_extension('developer')
bot.load_extension('staff')
bot.load_extension('fun')
# bot.load_extension('help')

bot.run(CONFIG.bot.token)
