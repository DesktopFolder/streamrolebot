import discord
from discord import app_commands
from discord.ext.commands import has_permissions
import pickle
from os.path import isfile
from typing import Optional
import logging as l


"""
Logged in as StreamRoleBot#3286 (ID:)
(<CustomActivity name='C++ folder' emoji=<PartialEmoji animated=False name='📁' id=None>>,)
(<CustomActivity name='C++ folder' emoji=<PartialEmoji animated=False name='📁' id=None>>, <Streaming name='NON EXISTENT STREAM JUST TESTING SOMETHING SORRY'>)
(<CustomActivity name='C++ folder' emoji=<PartialEmoji animated=False name='📁' id=None>>,)
"""


async def respond(interaction: discord.Interaction, *args, **kwargs):
    return await interaction.response.send_message(*args, **kwargs, ephemeral=True)


guild_roles: dict[int, discord.Role] = dict()
live_users: dict[int, set] = dict()


class GuildState:
    def __init__(self, guild_id: int) -> None:
        self.members: dict[int, bool] = dict() 
        self.guild_id = guild_id
        self.role: int | None = None

    def is_active(self, member_id: int) -> bool:
        return self.members.get(member_id, False)

    def set_active(self, member_id: int):
        self.members[member_id] = True

    def set_inactive(self, member_id: int):
        self.members[member_id] = False

    def get_role(self):
        if self.role not in guild_roles:
            return None
        return guild_roles[self.role]

    def update_role(self, role: discord.Role):
        global guild_roles
        self.role = role.id
        guild_roles[self.role] = role

    async def validate(self, guild: discord.Guild):
        global guild_roles
        if self.role is None:
            # Not a valid guild, we have no role.
            return False
        if self.role in guild_roles:
            return True
        role = guild.get_role(self.role)
        if role is None:
            print('Warning: Role was none, likely deleted.')
            return False
        guild_roles[self.role] = role
        return True


class BotState:
    def __init__(self):
        self.guilds: dict[int, GuildState] = dict()
        self.dirty = False
        self.version = 1

    async def validate(self, guild: discord.Guild):
        if guild.id not in self.guilds:
            # If the guild doesn't exist, it's invalid.
            # Guilds only exist once /set_streaming_role is called.
            return False
        return await self.guilds[guild.id].validate(guild)

    def is_active(self, member: discord.Member) -> bool:
        # returns if this member is SET to being active BY THIS BOT.
        gid = member.guild.id
        if gid not in self.guilds:
            return False
        return self.guilds[gid].is_active(member.id)

    def ensure_guild(self, gid: int):
        if gid not in self.guilds:
            self.guilds[gid] = GuildState(gid)
            self.dirty = True
        return self.guilds[gid]

    async def activate(self, member: discord.Member):
        gid = member.guild.id
        mid = member.id

        guild = self.ensure_guild(gid)
        if guild.role is None:
            return False
        r = guild.get_role()
        if r is None:
            return False

        guild.set_active(mid)
        await member.add_roles(r)

        self.dirty = True
        return True # Success.

    async def deactivate(self, member: discord.Member):
        gid = member.guild.id
        mid = member.id

        if gid not in self.guilds:
            return False
        guild = self.guilds[gid]
        if guild.role is None:
            return False
        r = guild.get_role()
        if r is None:
            return False

        try:
            await member.remove_roles(r)
        except:
            pass
        guild.set_inactive(mid)

        self.dirty = True
        return True

    def update_role(self, guild_id, role: discord.Role):
        # updates the role that we use for a specific guild.
        global guild_roles
        guild = self.ensure_guild(guild_id)
        guild.update_role(role)
        self.dirty = True

    def save_if(self):
        if not self.dirty:
            return
        with open('botstate.pkl', 'wb') as file:
            self.dirty = False
            pickle.dump(self, file)

    def __del__(self):
        # self.save_if()
        pass


if isfile('botstate.pkl'):
    botstate = pickle.load(open('botstate.pkl', 'rb'))
    assert type(botstate) == BotState
else:
    botstate = BotState()
testing = False


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        # self.tree.copy_global_to(guild=MY_GUILD) # don't bother with this anymore
        await self.tree.sync()  # this syncs to other guilds


intents = discord.Intents.default()
intents.presences = True # This gets us our presence updates :)
intents.members = True # This gets us our presence updates :)
client = MyClient(intents=intents)


@client.event
async def on_ready():
    if client.user is None:
        print(f"Logged in as None?")
    else:
        print(f"Logged in as {client.user} (ID: {client.user.id})")


def get_active_title(activities: tuple[discord.activity.ActivityTypes]) -> Optional[str]:
    if not testing:
        for a in activities:
            if isinstance(a, discord.Streaming):
                return a.name
    else:
        print(activities)
        for a in activities:
            if isinstance(a, discord.CustomActivity):
                return a.name
    return None


def title_check(title: str):
    import re
    return re.search(r'(\baa\b|advancements|todos los logro)', title.lower()) is not None


def get_valid_activity(activities: tuple[discord.activity.ActivityTypes]) -> Optional[bool]:
    title = get_active_title(activities)
    if title is None:
        return None # The user is not active.
    return title_check(title)


@client.event
async def on_presence_update(_, after: discord.Member):
    global live_users

    if not await botstate.validate(after.guild):
        return

    # Get the user's current activities.
    act = get_valid_activity(after.activities)
    gid = after.guild.id

    if botstate.is_active(after):
        # We have previously set this user to active.
        # Only deactivate them if they are not streaming.
        if act is None:
            await botstate.deactivate(after)
    else:
        # Activate them if they are streaming with a valid title.
        # Note - currently a bug, the user cannot opt out of this.
        # Not really an issue probably. This only occurs if AA / advancements
        # are in the title, so can simply remove those. Or fix the code.
        act = get_valid_activity(after.activities)
        if act is not None:
            # They are live.
            if gid not in live_users:
                live_users[gid] = set()
            live_users[gid].add(after.id)

        if act:
            await botstate.activate(after)

    # If they are not streaming, then store that information.
    if act is None and gid in live_users:
        users = live_users[gid]
        if after.id in users:
            users.remove(after.id)

    botstate.save_if()


@client.tree.command()
@has_permissions(administrator=True)
async def set_streaming_role(interaction: discord.Interaction, role: discord.Role):
    if interaction.guild_id is None:
        return await interaction.response.send_message("Your guild ID is None, please try again later.", ephemeral=True)
    botstate.update_role(interaction.guild_id, role)
    botstate.save_if()
    return await interaction.response.send_message("Set the role successfully.", ephemeral=True)


@client.tree.command()
async def streambot_debug(interaction: discord.Interaction, argument: Optional[str]):
    gd = interaction.guild
    if gd is None:
        return await respond(interaction, "Guild is `None` - this can't be used outside of a server.")
    gid = gd.id

    if argument is None:
        s = live_users.get(gid, set())
        users = [f"<@{uid}>" for uid in s]
        return await respond(interaction, f"Bot is currently aware of {len(s)} streaming users: {users}")
    else:
        return await respond(interaction, "Arguments don't do anything, friend...")


@client.tree.command()
async def live(interaction: discord.Interaction, user: Optional[discord.Member]):
    if interaction.guild is None:
        return await interaction.response.send_message("This cannot be called outside a guild.", ephemeral=True)
    if not await botstate.validate(interaction.guild):
        return await interaction.response.send_message("You have not set up a role.", ephemeral=True)

    target: discord.User | discord.Member
    if user is not None:
        target = user
    else:
        target = interaction.user

    if type(target) != discord.Member:
        return await interaction.response.send_message("This member is not a member (bot error?)", ephemeral=True)

    if target.id not in live_users.get(target.guild.id, set()) and get_valid_activity(target.activities) is None:
        l.debug(f'{target.id} not present in live_users ({target.guild.id}: {live_users.get(target.guild.id)})')
        return await interaction.response.send_message("This user is not live.", ephemeral=True)

    await botstate.activate(target)
    botstate.save_if()
    return await interaction.response.send_message("Activated the user.", ephemeral=True)


@client.tree.command()
async def not_live(interaction: discord.Interaction, user: Optional[discord.Member]):
    if interaction.guild is None:
        return await respond(interaction, "This cannot be called outside a guild.")
    if not await botstate.validate(interaction.guild):
        return await respond(interaction, "You have not set up a role.")

    target: discord.User | discord.Member
    if user is not None:
        target = user
    else:
        target = interaction.user

    if type(target) != discord.Member:
        return await respond(interaction, "This member is not a member (bot error?)")

    await botstate.deactivate(target)
    botstate.save_if()
    return await interaction.response.send_message("Role removed if present.", ephemeral=True)


def main(args):
    if 'testing' in args:
        global testing
        testing = True
    if 'debug' in args:
        l.basicConfig(level=l.DEBUG)
    client.run(open("token.txt").read().strip())


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
