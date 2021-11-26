import discord
import logging
from os import environ

logging.basicConfig(level=logging.DEBUG)
REACTION_OPT_IN = "🔔"    # :bell:
REACTION_KEEP_ROLE = "🎮"    # :video_game:
MATCHMAKING_ROLE_ID = int(environ['MATCHMAKING_ROLE_ID'])   # @matchmaking
GUILD_ID = int(environ['GUILD_ID'])   # Wizard Wars Reborn discord server
CHANNEL_ID = int(environ['CHANNEL_ID'])     # Channel where the message to react to is located
MESSAGE_TO_MONITOR = int(environ['REACTION_MESSAGE'])    # Message where the reacts should be
BOT_TOKEN = environ['LENNYTOKEN']


class Lenny(discord.Client):
    async def on_ready(self):
        print('Ready!')
        self.guild = self.get_guild(GUILD_ID)
        self.message = await self.guild.get_channel(CHANNEL_ID).fetch_message(MESSAGE_TO_MONITOR)
        self.matchmaking_role = self.guild.get_role(MATCHMAKING_ROLE_ID)
        self.opt_in_users = set()
        self.matchmaking_users = set()

        # Read reactions on the message at startup
        for reaction in self.message.reactions:
            if reaction.emoji == REACTION_KEEP_ROLE:
                users = await reaction.users().flatten()
                self.matchmaking_users = {user.id for user in users}    # set of users who want to have the role always
            if reaction.emoji == REACTION_OPT_IN:
                users = await reaction.users().flatten()
                self.opt_in_users = {user.id for user in users}     # set of users who opt in to having role changed based on their Discord presence


intents = discord.Intents.all()
lenny = Lenny(intents=intents, activity=discord.Game('Magicka: Wizard Wars'))


@lenny.event
async def on_raw_reaction_add(data):
    if data.message_id == MESSAGE_TO_MONITOR and data.emoji.name == REACTION_KEEP_ROLE:
        lenny.matchmaking_users.add(data.user_id)
        member = lenny.guild.get_member(data.user_id)
        await member.add_roles(lenny.matchmaking_role, reason='( ͡° ل͜ ͡°)')
    elif data.message_id == MESSAGE_TO_MONITOR and data.emoji.name == REACTION_OPT_IN:
        lenny.opt_in_users.add(data.user_id)


@lenny.event
async def on_raw_reaction_remove(data):
    member = lenny.guild.get_member(data.user_id)
    if data.message_id == MESSAGE_TO_MONITOR and data.emoji.name == REACTION_OPT_IN:
        lenny.opt_in_users.discard(member.id)      # discard doesn't raise an error if by any chance the user isn't in set
    elif data.message_id == MESSAGE_TO_MONITOR and data.emoji.name == REACTION_KEEP_ROLE and lenny.matchmaking_role in member.roles:
        lenny.matchmaking_users.discard(member.id)
        await member.remove_roles(lenny.matchmaking_role, reason='( ͠° ͟ʖ ͡°)')


@lenny.event
async def on_member_update(_, member):
    # if user is opted in and started playing, add role
    if member.id in lenny.opt_in_users and member.activity.name == 'Magicka: Wizard Wars' and lenny.matchmaking_role not in member.roles:
        await member.add_roles(lenny.matchmaking_role, reason='( ͡° ل͜ ͡°)')
    # if user is opted in and stopped playing, remove role
    elif member.id in lenny.opt_in_users and member.id not in lenny.matchmaking_users and member.activity.name != 'Magicka: Wizard Wars' and lenny.matchmaking_role in member.roles:
        await member.remove_roles(lenny.matchmaking_role, reason='( ͠° ͟ʖ ͡°)')
    # if user is matchmaking_user and the role has been removed for any reason, add it back
    elif member.id in lenny.matchmaking_users and lenny.matchmaking_role not in member.roles:
        await member.add_roles(lenny.matchmaking_role, reason='( ͡° ل͜ ͡°)')
lenny.run(BOT_TOKEN)