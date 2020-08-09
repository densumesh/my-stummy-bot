import asyncio
import discord
import random
from discord.ext import commands
from gtts import gTTS
import os
import pickle
import requests
import praw
from googleapiclient.discovery import build
import yfinance as yf
import matplotlib.pyplot as plt
import psutil
import json
import ping3

with open('keys.json', 'r') as fp:
    keys = json.load(fp)

my_api_key = keys['GOOGLE_API_KEY']
my_cse_id = keys['GOOGLE_CSE_ID']

client = discord.Client()
client = commands.Bot(command_prefix = ('$', '%'), case_insensitive = True)
client.remove_command("help")

plt.style.use('ggplot')
bad_words = []
with open('badwords.txt', 'r') as badword:
    for words in badword:
        bad_words.append(words.strip('\n'))


voicePaths = {'bullets': ['/home/ubuntu/my-bot/static/Animaker-Voice.mp3', 3], 
'singing challenge': ['/home/ubuntu/my-bot/static/Animaker-Voice (1).mp3', 5],
'roga dong': ['/home/ubuntu/my-bot/static/ttsMP3.com_VoiceText_2020-7-7_12_29_57.mp3', 4],
'despacito': ['/home/ubuntu/my-bot/static/ttsMP3.com_VoiceText_2020-7-7_12_29_28.mp3', 1],
'yeah yeah': ['/home/ubuntu/my-bot/static/ttsMP3.com_VoiceText_2020-7-7_12_28_43.mp3', 1],
'pewds': ['/home/ubuntu/my-bot/static/Pewdiepie says What A Fking N Word.mp3', 2]}

class Extras(commands.Cog):
    @commands.command()
    async def soundboard(self, ctx, *args):
        try:
            if not str(args) == '()':
                author = ctx.message.author
                voice_channel = author.voice.channel
                vc = await voice_channel.connect()
                if len(args) >= 2:
                    vc.play(discord.FFmpegPCMAudio(voicePaths[(' '.join(args))][0]))
                    await ctx.send('Now playing: **{}**'.format((' '.join(args))))
                    await asyncio.sleep(voicePaths[' '.join(args)][1])
                    await vc.disconnect()
                elif len(args) <= 1:
                    vc.play(discord.FFmpegPCMAudio(voicePaths[''.join(args)][0]))
                    await ctx.send('Now playing: **{}**'.format(''.join(args)))
                    await asyncio.sleep(voicePaths[''.join(args)][1])
                    await vc.disconnect()
            else:
                choice = random.choice(list(voicePaths.keys()))
                author = ctx.message.author
                voice_channel = author.voice.channel
                vc = await voice_channel.connect()
                vc.play(discord.FFmpegPCMAudio(voicePaths[choice][0]))
                await ctx.send('Now playing: **{}**'.format(choice))
                await asyncio.sleep(voicePaths[choice][1])
                await vc.disconnect()
        except KeyError:
            await ctx.send('**{}** is not valid file.'.format(' '.join(args)))
            embed = discord.Embed(title="Soundboard files", description="Do $soundboard along with one of these", inline=False, color = 0x1d68e0)
            embed.add_field(name= "bullets", value= "Man how did those bullets not hit!", inline=False)
            embed.add_field(name= "singing challenge", value="Yeah Yeah Singing Challenge", inline=False) 
            embed.add_field(name= "roga dong", value="Top 10 songs of all time", inline=False)
            embed.add_field(name= "despacito", value="Despactito", inline=False)
            embed.add_field(name= "yeah yeah", value="Yeah Yeah", inline=False)
            embed.add_field(name= "pewds", value="Pewdipie says bad things", inline=False)
            await ctx.send(content=None, embed=embed)
            await vc.disconnect()

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('An Error occured!', delete_after = 20)
            print(error)
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send('An Error occured!', delete_after = 20)
            print(error)

    @commands.command()
    async def tts(self, ctx, *args):
        message = await ctx.send("Getting tts for: %s 🔎" % ' '.join(args))
        tts = gTTS(' '.join(args), lang='en')
        fname = "_".join(' '.join(args).split()) + ".mp3"
        tts.save('/home/ubuntu/my-bot/static/'+fname)
        if ctx.voice_client is None:
            author = ctx.message.author
            voice_channel = author.voice.channel
            vc = await voice_channel.connect()
            vc.play(discord.FFmpegPCMAudio('/home/ubuntu/my-bot/static/'+fname))
            with open('/home/ubuntu/my-bot/static/'+fname, 'rb') as fp:
                await ctx.send('Now playing: {}'.format(' '.join(args)), file=discord.File(fp, "_".join(' '.join(args).split()) + ".mp3"))
            await message.delete()
            asyncio.sleep(20)
            os.remove('/home/ubuntu/my-bot/static/'+fname)
        else:
            ctx.voice_client.play(discord.FFmpegPCMAudio('/home/ubuntu/my-bot/static/'+fname))
            with open('/home/ubuntu/my-bot/static/'+fname, 'rb') as fp:
                await ctx.send('Now playing: {}'.format(' '.join(args)), file=discord.File(fp, "_".join(' '.join(args).split()) + ".mp3"))
            await message.delete()
            asyncio.sleep(20)
            os.remove('/home/ubuntu/my-bot/static/'+fname)


    @commands.command(aliases= ['h'])
    async def help(self, ctx):
        embed = discord.Embed(title="Phil Death help", description="Some useful commands", color = 0x1d68e0)
        embed.add_field(name= "$play", value= "Either put a link or search YouTube for music", inline=False)
        embed.add_field(name= "$soundcloud", value= "Either put a link or search Soundcloud for music", inline=False)
        embed.add_field(name= "$spotify", value= "Put a spotify link", inline=False)
        embed.add_field(name= "$lyrics", value="Either put a song to look up lyrics or if a song is playing get its lyrics", inline=False)
        embed.add_field(name= "$search", value="Put a query after in order to get first 5 results from Youtube", inline=False)
        embed.add_field(name= "$queue", value= "Look at the upcoming songs playing", inline=False)
        embed.add_field(name= "$addperson", value="Add a person to the rank stats. i.e. $addperson @name Riot id#tag", inline=False)
        embed.add_field(name= "$rank", value= "Gets valorant ranks, include name if you want a specific person", inline=False)
        embed.add_field(name= "$tts", value="Put words after to hear it said", inline=False)
        embed.add_field(name= "$soundboard", value="Play music from the soundboard", inline=False)
        embed.add_field(name= "$volume", value="Change the volume of the bot: Put a value between 0-100", inline=False)
        embed.set_footer(text= "Source: ")
        await ctx.send(content=None, embed=embed)
            
    
    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def spam(self, ctx, user: discord.Member, *, args = None):
        channel = await user.create_dm()
        for i in range(10):
            if not args == None:
                if not args in bad_words:
                    await channel.send(args)
                else:
                    await ctx.send('Message could not be sent.', delete_after = 20)
            else:
                await channel.send('Get on the server')
        

    @commands.command()
    async def gif(self, ctx, *args):
        r = requests.get('https://api.giphy.com/v1/gifs/search?api_key=BBNTu65mlxYCMwTULokqcwG62bnYw99O&q={}&limit=1&offset=0&rating=g&lang=en'.format(' '.join(args)))
        data = r.json()
        gifurl = data['data'][0]['url']
        await ctx.send(gifurl)

    @commands.command()
    async def meme(self, ctx):
        if ctx.message.author.name == 'the one and the only':
            await ctx.send('Please get some friends')
        reddit = praw.Reddit(client_id="jmj6Nil7ySwIKw",
                     client_secret="uynNO5lqrPR7eAeQ1j8wVrZEZ0o",
                     user_agent="discord:extras.py (by /u/radiantsmurf)")
        submission = list(reddit.subreddit("memes").top("day", limit=50))
        radint = random.randint(0,len(submission)-1)
        embed = discord.Embed(title=submission[radint].title, color = 0x1d68e0, url= submission[radint].shortlink)
        image = submission[radint].preview['images'][0]['source']['url']
        embed.set_image(url = image)
        embed.set_footer(text='⬆️ {} | 💬 {}'.format(submission[radint].score, submission[radint].num_comments))
        await ctx.send(content= None, embed= embed)

    @commands.command()
    async def aadi(self, ctx):
        reddit = praw.Reddit(client_id="jmj6Nil7ySwIKw",
                     client_secret="uynNO5lqrPR7eAeQ1j8wVrZEZ0o",
                     user_agent="discord:extras.py (by /u/radiantsmurf)")
        submission = list(reddit.subreddit("politicalcompassmemes").top("day", limit=50))
        radint = random.randint(0,len(submission)-1)
        embed = discord.Embed(title=submission[radint].title, color = 0x1d68e0, url= submission[radint].shortlink)
        image = submission[radint].preview['images'][0]['source']['url']
        embed.set_image(url = image)
        embed.set_footer(text='⬆️ {} | 💬 {}'.format(submission[radint].score, submission[radint].num_comments))
        await ctx.send(content= None, embed= embed)

    @commands.command()
    async def serverinfo(self, ctx):
        embed = discord.Embed(title="Server Info", color = 0x1d68e0)
        embed.add_field(name= 'Server name: ', value= ctx.message.guild.name)
        embed.add_field(name= 'Number of members: ', value = ctx.message.guild.member_count)
        embed.add_field(name = 'Server Owner: ', value = ctx.message.guild.owner, inline = False)
        embed.add_field(name = 'CPU Util:', value= psutil.cpu_percent(), inline = False)
        embed.add_field(name = 'Memory Util:', value= psutil.virtual_memory().percent)
        embed.set_thumbnail(url = ctx.message.guild.icon_url)
        await ctx.send(content = None, embed = embed)
    

    
    @commands.command(aliases = ['google'])
    async def gsearch(self, ctx, *, args):
        service = build("customsearch", "v1", developerKey=my_api_key)
        res = service.cse().list(q=args, cx=my_cse_id).execute()
        firstitem = (res['items'][0]['title'], res['items'][0]['link'])
        embed = discord.Embed(title=firstitem[0], color = 0x1d68e0, url = firstitem[1])
        if 'snippet' in res['items'][0].keys():
            embed.add_field(name = '\u200b', value = res['items'][0]['snippet'].strip('\n').strip('\\').strip())
        if 'cse_thumbnail' in res['items'][0]['pagemap'].keys():
            embed.set_thumbnail(url = res['items'][0]['pagemap']['cse_thumbnail'][0]['src'])
        await ctx.send(content = None, embed = embed)
    
    @commands.command()
    async def stocks(self, ctx, *, args):
        msg = await ctx.send('Getting stock info 🔎')
        ticker = yf.Ticker(str(args))
        hist = ticker.info
        hist1 = ticker.history(period='1mo', interval='60m', prepost=True)
        hist1['Close'].plot(figsize=(16, 9), label=args)
        c1 = self.stockChange(str(args))

        plt.ylabel('Price of Stock')
        plt.title("Current stock prices")
        plt.legend()
        plt.savefig('stock.png', bbox_inches='tight')


        embed = discord.Embed(title=hist['shortName'], color = 0x1d68e0, url = hist['website'])
        embed.set_author(name = hist['symbol'])
        embed.set_thumbnail(url = hist['logo_url'])
        embed.add_field(name = 'Location:', value = hist['city'] + ', ' + hist['country'], inline = False)
        if float(c1) < (0.00):
            embed.add_field(name = 'Previous Close:', value= str(hist['previousClose']) + ' ▼' + ' (' + str(c1) + ')', inline = False)
        else:
            embed.add_field(name = 'Previous Close:', value= str(hist['previousClose']) + ' ▲' + ' (' + str(c1) + ')', inline = False) 
        embed.add_field(name = 'Open:', value =  hist['open'], inline = False)

        file = discord.File("./stock.png", filename="image.png")
        embed.set_image(url="attachment://image.png")
        await msg.delete()
        await ctx.send(file = file, embed = embed)
        plt.clf()
        os.remove('./stock.png')


    def stockChange(self, stock1):
        response1 = requests.get('https://sandbox.tradier.com/v1/markets/quotes', params={'symbols': stock1, 'greeks': 'false'}, headers={'Authorization': 'Bearer RfcIci33DAu7lxb5dKUAjNKDAODy', 'Accept': 'application/json'})
        c1 = response1.json()['quotes']['quote']['change']
        return c1
    
    @commands.command()
    async def ping(self, ctx, *, args):
        print(args)
        r = ping3.verbose_ping(args)

        await ctx.send(r)