import asyncio
import discord
from discord.ext import commands
from music import Music
from extras import Extras
import datetime
from discord.utils import get
import requests
import json
import pymongo

with open('keys.json', 'r') as fp:
    keys = json.load(fp)

extensions = ['music', 'extras']
TOKEN = keys['DISCORD_TOKEN']
ban = False
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.dm_messages = True
client = commands.Bot(command_prefix=('$', '%', '!'), case_insensitive=True, intents=intents)
client.remove_command("help")
messages = {}


def is_owner(ctx):
    return ctx.author.id == 344597620448034818
@client.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name='nice time')
    await member.add_roles(role)
    if str(member) == 'Blackimon#8323':
        role = discord.utils.get(member.guild.roles, name='PHILIMON')
        await member.add_roles(role)


@client.event
async def on_message_delete(message):
    channel = client.get_channel(739626832952950916)
    if not str(message.author.name) == 'alBY':
        embed = discord.Embed(title="Message Deleted", color=0x1d68e0)
        if not message.attachments:
            embed.add_field(name=f"{message.author.name}", value=f"deleted: **{message.content}**")
        else:
            embed.add_field(name=f"{message.author.name}", value=f"deleted:")
            embed.set_image(url=message.attachments[0].url)
        await channel.send(content=None, embed=embed)


@client.event
async def on_message(message):
    if "nigga" in message.content.lower() or "nigger" in message.content.lower() or "n1gga" in message.content or "n1gger" in message.content:
        if message.author.id != 431287348882571265:
            channel = client.get_channel(739626832952950916)
            print('work')
            await message.guild.ban(message.author, reason="said the n-word")
            await channel.send('{} said the n-word and was banned'.format(message.author.mention))
    await client.process_commands(message)

@client.event
async def on_message_edit(before, after):
    channel = client.get_channel(739626832952950916)
    if not str(before.author.name) == 'alBY':
        if not before.content == after.content:
            embed = discord.Embed(title="Message Edited", color=0x1d68e0)
            embed.add_field(name=f"{before.author.name}",
                            value=f"edited: **{before.content}**\nto: **{after.content}**")
            await channel.send(content=None, embed=embed)


@client.event
async def on_voice_state_update(member, before, after):
    if (before.channel is not None and after.channel is None) or (
            before.channel is not None and after.channel is not None):
        if client.user in before.channel.members and len([m for m in before.channel.members if not m.bot]) == 0:
            channel = discord.utils.get(client.voice_clients, channel=before.channel)
            await channel.disconnect()


async def membercount():
    guild = client.get_guild(725907147552063587)
    member_count = len(guild.members)
    true_member_count = len([m for m in guild.members if not m.bot])

    membercount = guild.get_channel(747664568939184189)
    usercount = guild.get_channel(747664572030386206)
    channelcount = guild.get_channel(747665003288461372)
    botcount = guild.get_channel(747664574827855963)

    await membercount.edit(name=f"Member Count: {member_count}")
    await usercount.edit(name=f"User Count: {true_member_count}")
    await channelcount.edit(name=f"Channel Count: {len(guild.channels) - 4}")
    await botcount.edit(name=f"Bot Count: {member_count - true_member_count}")
    await asyncio.sleep(3600)


@client.event
async def on_guild_update(before, after):
    guild = client.get_guild(725907147552063587)
    if not before.name == after.name:
        channel = client.get_channel(739626832952950916)
        role = guild.get_role(737184592691462154)
        await channel.send(f"Server name changed from: {before.name} to: {after.name} {role.mention}")
    if not before.icon == after.icon:
        channel = client.get_channel(739626832952950916)
        embed = discord.Embed(title="Server icon changed", color=0x1d68e0)
        role = guild.get_role(737184592691462154)
        embed.add_field(name='To: ', value='\u200b')
        embed.set_image(url=after.icon_url)
        await channel.send(content=role.mention, embed=embed)


@client.event
async def on_member_ban(guild, user):
    if user.guild.id == 725907147552063587:
        channel = client.get_channel(739626832952950916)
        role = guild.get_role(737184592691462154)
        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
            await channel.send(f'{entry.user} banned {user.name} {role.mention}')

@client.event
async def on_member_remove(member):
    if member.guild.id == 725907147552063587:
        guild = client.get_guild(725907147552063587)
        general = client.get_channel(725907147606589469)
        channel = client.get_channel(739626832952950916)
        role = guild.get_role(737184592691462154)
        dm = await member.create_dm()
        link = await general.create_invite(max_age=0, max_uses=0, unique=False)
        async for entry in guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
            if not str(entry.user) == 'alBY#4055':
                await channel.send(f'{entry.user} kicked {member.name} {role.mention}')
            else:
                await channel.send(f'{member.name} left the server {role.mention}')
        await dm.send(link)


@client.command()
@commands.check(is_owner)
async def reload(ctx, extension):
    try:
        client.unload_extension(extension)
        client.load_extension(extension)
        await ctx.send('Reloaded {}'.format(extension))
    except Exception as e:
        await ctx.send('{} cannot be reloaded [{}]'.format(extension, e))


@client.command()
@commands.check(is_owner)
async def load(ctx, extension):
    try:
        client.load_extension(extension)
        await ctx.send('Loaded {}'.format(extension))
    except Exception as e:
        await ctx.send('{} cannot be loaded [{}]'.format(extension, e))

@client.command()
@commands.check(is_owner)
async def unload(ctx, extension):
    try:
        client.unload_extension(extension)
        await ctx.send('Unloaded {}'.format(extension))
    except Exception as e:
        await ctx.send('{} cannot be unloaded [{}]'.format(extension, e))


@client.event
async def on_ready():
    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print('Logged in as {} ({})'.format(client.user, current_time))
    print('------')
    game = discord.Game("$help | Carti's stummy hurts")
    await client.change_presence(activity=game)
    client.loop.create_task(membercount())


for extension in extensions:
    client.load_extension(extension)
client.run(TOKEN)
