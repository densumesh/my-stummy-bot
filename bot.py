import asyncio
import discord
from discord.ext import commands
from music import Music
from extras import Extras
from datetime import datetime
import pickle
import os
from discord.utils import get
import requests
import json
import pymongo

with open('keys.json', 'r') as fp:
    keys = json.load(fp)

TOKEN = keys['DISCORD_TOKEN']

client = discord.Client()
client = commands.Bot(command_prefix = ('$', '%'), case_insensitive = True)
client.remove_command("help")

messages = {}
ranks = {'Iron 1': '<:Iron1:733004687141240944>', 
'Iron 2': '<:Iron2:733028968827191406>', 
'Iron 3': '<:Iron3:733028968655224843>', 
'Bronze 1': '<:Bronze1:733004701230170134>', 
'Bronze 2': '<:Bronze2:733004716019023934>', 
'Bronze 3': '<:Bronze3:733028969573646356>', 
'Silver 1': '<:Silver1:733004733433905212>', 
'Silver 2': '<:Silver2:733028968784986142>', 
'Silver 3': '<:Silver3:733028968961278032>', 
'Gold 1': '<:Gold1:733004790295953441>', 
'Gold 2': '<:Gold2:733004810399252531>', 
'Gold 3': '<:Gold3:733028969623847002>', 
'Platinum 1': '<:Plat1:733004824571805772>', 
'Platinum 2': '<:Plat2:733004851532791949>', 
'Platinum 3': '<:Plat3:733028966557941843>'}
conn = pymongo.MongoClient(keys['MongoDB_CONNECTION'])
db = conn.botusers
col = db.bot
users = list(col.find())  


async def valorantRole():
    while True:
        for name in users:
            url = 'https://tracker.gg/valorant/profile/riot/usa/' + name['Riot'][0] + '%23' + name['Riot'][1] + '/overview'
            r = requests.get(url)
            data = r.text
            firstindex = data.find('valorant-rank-bg')
            secondindex = data.find('>', firstindex)
            endindex = data.find('<',secondindex)
            rank = data[secondindex+10:endindex-9]

            guild = client.get_guild(725907147552063587)
            user = guild.get_member(name['name'])
            role = discord.utils.get(guild.roles, name=rank)
            silver = get(guild.roles, name='Silver')
            bronze = get(guild.roles, name='Bronze')
            iron = get(guild.roles, name='Iron')
            gold = get(guild.roles, name='Gold')
            platinum = get(guild.roles, name='Platinum')
            if silver in user.roles:
                await user.remove_roles(silver)
            elif bronze in user.roles:
                await user.remove_roles(bronze)
            elif iron in user.roles:
                await user.remove_roles(iron)
            elif gold in user.roles:
                await user.remove_roles(gold)
            elif platinum in user.roles:
                await user.remove_roles(platinum)
            await user.add_roles(role)
        await asyncio.sleep(3600)


@client.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name='nice time')
    await member.add_roles(role)
    if str(member) == 'el b1ACk#8323':
        role = discord.utils.get(member.guild.roles, name='PHILIMON')
        await member.add_roles(role)

@client.event
async def on_message_delete(message):
    channel = client.get_channel(739626832952950916)
    if not str(message.author.name) == 'my stummy bot':
        embed = discord.Embed(title="Message Deleted", color = 0x1d68e0)
        if not message.attachments:
            embed.add_field(name = f"{message.author.name}", value= f"deleted: **{message.content}**")
        else:
            embed.add_field(name = f"{message.author.name}", value= f"deleted:")
            embed.set_image(url = message.attachments[0].url)
        await channel.send(content=None, embed = embed)

@client.event
async def on_message_edit(before, after):
    channel = client.get_channel(739626832952950916)
    if not str(before.author.name) == 'my stummy bot':
        if not before.content == after.content:
            embed = discord.Embed(title="Message Edited", color = 0x1d68e0)
            embed.add_field(name = f"{before.author.name}", value = f"edited: **{before.content}**\nto: **{after.content}**")
            await channel.send(content=None, embed = embed)

@client.event
async def on_voice_state_update(member, before, after):
    if (before.channel is not None and after.channel is None) or (before.channel is not None and after.channel is not None):
        if client.user in before.channel.members and len([m for m in before.channel.members if not m.bot]) == 0:
            channel = discord.utils.get(client.voice_clients, channel=before.channel)
            await channel.disconnect()
            
async def membercount():
    guild = client.get_guild(725907147552063587)
    member_count = len(guild.members)
    true_member_count = len([m for m in guild.members if not m.bot])

    membercount = guild.get_channel(737373941701804130)
    usercount = guild.get_channel(737373942825746442)
    channelcount = guild.get_channel(737373943681384458)
    rolecount = guild.get_channel(737373944704794746)
    botcount = guild.get_channel(737373945937920000)

    await membercount.edit(name=f"Member Count: {member_count}")
    await usercount.edit(name=f"User Count: {true_member_count}")
    await channelcount.edit(name=f"Channel Count: {len(guild.channels)-5}")
    await rolecount.edit(name=f"Role Count: {len(guild.roles)}")
    await botcount.edit(name=f"Bot Count: {member_count-true_member_count}")
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
        role = guild.get_role(737184592691462154)
        embed = discord.Embed(title="Server icon changed", color = 0x1d68e0)
        role = guild.get_role(737184592691462154)
        embed.add_field(name= 'To: ', value = '\u200b')
        embed.set_image(url = after.icon_url)
        await channel.send(content = role.mention, embed = embed)

@client.event
async def on_member_ban(guild, user):
    channel = client.get_channel(739626832952950916)
    role = guild.get_role(737184592691462154)
    await channel.send(f"{user.name} was banned {role.mention}")

@client.event
async def on_member_remove(member):
    guild = client.get_guild(725907147552063587)
    channel = client.get_channel(739626832952950916)
    role = guild.get_role(737184592691462154)
    await channel.send(f"{member.name} was kicked {role.mention}")



@client.command()
async def rank(ctx, *args):
    embed = discord.Embed(title="Valorant Ranks", color = 0x1d68e0)
    message = await ctx.send("Getting Valorant ranks🔎")
    if str(args) == '()':
        for name in users:
            try:
                url = 'https://tracker.gg/valorant/profile/riot/usa/' + name['Riot'][0] + '%23' + name['Riot'][1] + '/overview'
                r = requests.get(url)
                data = r.text
                firstindex = data.find('valorant-rank-bg')
                secondindex = data.find('>', firstindex)
                endindex = data.find('<',secondindex)
                rank = data[secondindex+10:endindex-7]
                guild = client.get_guild(725907147552063587)
                user = guild.get_member(name['name'])
                if 'Silver' in rank:
                    embed.add_field(name= "{}{}".format(user.name, ranks[rank]), value = '{}'.format(rank), inline=False)
                elif 'Bronze' in rank:
                    embed.add_field(name= "{}{}".format(user.name, ranks[rank]), value = '{}'.format(rank), inline=False)
                elif 'Iron' in rank:
                    embed.add_field(name= "{}{}".format(user.name, ranks[rank]), value = '{}'.format(rank), inline=False)
                elif 'Gold' in rank:
                    embed.add_field(name= "{}{}".format(user.name, ranks[rank]), value = '{}'.format(rank), inline=False)
                elif 'Platinum' in rank:
                    embed.add_field(name= "{}{}".format(user.name, ranks[rank]), value = '{}'.format(rank), inline=False)
            except KeyError:
                continue
        await ctx.send(content=None, embed=embed)
        await message.delete()

    else:
        try: 
            guild = client.get_guild(725907147552063587)
            user = guild.get_member_named(' '.join(args))
            url = 'https://tracker.gg/valorant/profile/riot/usa/' + users[int(user.id)][0] + '%23' + users[int(user.id)][1] + '/overview'
            r = requests.get(url)
            data = r.text
            firstindex = data.find('valorant-rank-bg')
            secondindex = data.find('>', firstindex)
            endindex = data.find('<',secondindex)
            rank = data[secondindex+10:endindex-7]
            embed.add_field(name= "{}{}".format(user.name, ranks[rank]), value = '{}'.format(rank), inline=False)
            await ctx.send(content=None, embed=embed)
            await message.delete()
        except:
            await message.delete()
            await ctx.send('Person not found')

@client.event
async def on_ready():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print('Logged in as {} ({})'.format(client.user, current_time))
    print('------')
    game = discord.Game("$help | Carti's stummy hurts")
    await client.change_presence(activity=game)
    client.loop.create_task(valorantRole())
    client.loop.create_task(membercount())

client.add_cog(Music(client))
client.add_cog(Extras(client))
client.run(TOKEN)
