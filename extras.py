import asyncio
import discord
import random
from discord.ext import commands
from gtts import gTTS
import os
import requests
import praw
from googleapiclient.discovery import build
import yfinance as yf
import matplotlib.pyplot as plt
import json
from better_profanity import profanity
import base64
import langcodes

with open('keys.json', 'r') as fp:
    keys = json.load(fp)

my_api_key = keys['GOOGLE_API_KEY']
my_cse_id = keys['GOOGLE_CSE_ID']

plt.style.use('ggplot')

voicePaths = {'bullets': ['/home/ubuntu/my-bot/static/Animaker-Voice.mp3', 3],
              'singing challenge': ['/home/ubuntu/my-bot/static/Animaker-Voice (1).mp3', 5],
              'roga dong': ['/home/ubuntu/my-bot/static/ttsMP3.com_VoiceText_2020-7-7_12_29_57.mp3', 4],
              'despacito': ['/home/ubuntu/my-bot/static/ttsMP3.com_VoiceText_2020-7-7_12_29_28.mp3', 1],
              'yeah yeah': ['/home/ubuntu/my-bot/static/ttsMP3.com_VoiceText_2020-7-7_12_28_43.mp3', 1],
              'pewds': ['/home/ubuntu/my-bot/static/Pewdiepie says What A Fking N Word.mp3', 2]}


class Extras(commands.Cog):
    def __init__(self, bot):
        self.client = bot
        self.ttsvoice = 'en'

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
            embed = discord.Embed(title="Soundboard files", description="Do $soundboard along with one of these",
                                  inline=False, color=ctx.message.author.color.value)
            embed.add_field(name="bullets", value="Man how did those bullets not hit!", inline=False)
            embed.add_field(name="singing challenge", value="Yeah Yeah Singing Challenge", inline=False)
            embed.add_field(name="roga dong", value="Top 10 songs of all time", inline=False)
            embed.add_field(name="despacito", value="Despacito", inline=False)
            embed.add_field(name="yeah yeah", value="Yeah Yeah", inline=False)
            embed.add_field(name="pewds", value="PewDiePie says bad things", inline=False)
            await ctx.send(content=None, embed=embed)
            await vc.disconnect()

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('An Error occurred!', delete_after=20)
            await ctx.send(error, delete_after=20)
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send('An Error occurred!', delete_after=20)
            await ctx.send(error, delete_after=20)

    @commands.group()
    async def tts(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid tts command passed... Use $tts play to play tts or $tts voice to change the voice.')

    @tts.command()
    async def play(self, ctx, *args):
        message = await ctx.send("Getting tts for: %s 🔎" % ' '.join(args))
        tts = gTTS(' '.join(args), lang=self.ttsvoice)
        fname = "_".join(' '.join(args).split()) + ".mp3"
        tts.save('/home/ubuntu/my-bot/static/' + fname)
        if ctx.voice_client is None:
            author = ctx.message.author
            voice_channel = author.voice.channel
            vc = await voice_channel.connect()
            vc.play(discord.FFmpegPCMAudio('/home/ubuntu/my-bot/static/' + fname))
            with open('/home/ubuntu/my-bot/static/' + fname, 'rb') as fp:
                await ctx.send('Now playing: {}'.format(' '.join(args)),
                               file=discord.File(fp, "_".join(' '.join(args).split()) + ".mp3"))
            await message.delete()
            await asyncio.sleep(20)
            os.remove('/home/ubuntu/my-bot/static/' + fname)
            await ctx.voice_client.disconnect()
        else:
            ctx.voice_client.play(discord.FFmpegPCMAudio('/home/ubuntu/my-bot/static/' + fname))
            with open('/home/ubuntu/my-bot/static/' + fname, 'rb') as fp:
                await ctx.send('Now playing: {}'.format(' '.join(args)),
                               file=discord.File(fp, "_".join(' '.join(args).split()) + ".mp3"))
            await message.delete()
            await asyncio.sleep(20)
            os.remove('/home/ubuntu/my-bot/static/' + fname)
            await ctx.voice_client.disconnect()

    @tts.command()
    async def voice(self, ctx, ttvoice):
        if len(ttvoice) == 2:
            lang = langcodes.Language.make(language=ttvoice)
        else:
            lang = langcodes.find(ttvoice)
        if not str(lang.display_name()) == f'Unknown language [{ttvoice}]':
            self.ttsvoice = str(lang.language)
            await ctx.send('Voice changed to %s' % lang.display_name())
        else:
            await ctx.send('Incorrect language code.')

    @commands.command()
    @commands.has_role('The Oligarchy')
    async def purge(self, ctx, limit: int = 100, user: discord.Member = None, *, matches: str = None):
        def check_msg(msg):
            if msg.id == ctx.message.id:
                return True
            if user is not None:
                if msg.author.id != user.id:
                    return False
            if matches is not None:
                if matches not in msg.content:
                    return False
            return True
        if limit < 100:
            deleted = await ctx.channel.purge(limit=limit, check=check_msg)
            msg = await ctx.send('Purged ' + str(len(deleted)) + 'messages')
            await asyncio.sleep(2)
            await msg.delete()
        else:
            await ctx.send('Please stop being an absolute idiot.')

    @commands.command(aliases=['h'])
    async def help(self, ctx):
        embed = discord.Embed(title="alBY Bot help", description="Some useful commands", color=ctx.message.author.color.value)
        embed.add_field(name="$play",
                        value="Searches Youtube or accepts Youtube or Spotify links, as well as audio files",
                        inline=False)
        embed.add_field(name="$soundcloud", value="Either put a link or search Soundcloud for music", inline=False)
        embed.add_field(name="$purge", value="Purge messages Usage: $purge # of messages @member", inline=False)
        embed.add_field(name="$lyrics",
                        value="Either put a song to look up lyrics or if a song is playing get its lyrics",
                        inline=False)
        embed.add_field(name="$search", value="Put a query after in order to get first 5 results from Youtube",
                        inline=False)
        embed.add_field(name="$queue", value="Look at the upcoming songs playing", inline=False)
        embed.add_field(name="$pspot",
                        value="If you are listening to something on Spotify, this command will play it on the bot",
                        inline=False)
        embed.add_field(name="$spam", value="Usage: $spam @player message",
                        inline=False)
        embed.add_field(name="$tts",
                        value="$tts play: Put words after to hear it said, $tts voice: Change the tts voice",
                        inline=False)
        embed.add_field(name="$meme", value="Grab a meme from r/memes", inline=False)
        embed.add_field(name="$volume", value="Change the volume of the bot: Put a value between 0-100", inline=False)
        embed.add_field(name="$google", value="Search google and grab the first result", inline=False)
        embed.add_field(name="$stocks", value="Usage: $stocks stock ticker", inline=False)
        embed.set_footer(text="Source: " + 'https://github.com/densumesh/my-stummy-bot')
        await ctx.send(content=None, embed=embed)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def spam(self, ctx, user: discord.Member, *, args=None):
        channel = await user.create_dm()
        for i in range(10):
            if args is not None:
                if not profanity.contains_profanity(args):
                    await channel.send(args)
                else:
                    await ctx.send('Message could not be sent.', delete_after=20)
            else:
                await channel.send('Get on the server')

    @commands.command()
    async def gif(self, ctx, *args):
        r = requests.get(
            'https://api.giphy.com/v1/gifs/search?api_key={}}&q={}&limit=1&offset=0&rating=g&lang=en'.format(
                keys['GIPHY_API_KEY'], ''.join(args)))
        data = r.json()
        gifurl = data['data'][0]['url']
        await ctx.send(gifurl)

    @commands.command()
    async def meme(self, ctx):
        if ctx.message.author.name == 'the one and the only':
            await ctx.send('Please get some friends')
        reddit = praw.Reddit(client_id=keys['REDDIT_CLIENT_ID'],
                             client_secret=keys['REDDIT_CLIENT_SECRET'],
                             user_agent="discord:extras.py (by /u/radiantsmurf)")
        submission = list(reddit.subreddit("memes").top("day", limit=50))
        radint = random.randint(0, len(submission) - 1)
        embed = discord.Embed(title=submission[radint].title, color=ctx.message.author.color.value, url=submission[radint].shortlink)
        image = submission[radint].preview['images'][0]['source']['url']
        embed.set_image(url=image)
        embed.set_footer(text='⬆️ {} | 💬 {}'.format(submission[radint].score, submission[radint].num_comments))
        await ctx.send(content=None, embed=embed)

    @commands.command()
    async def aadi(self, ctx):
        reddit = praw.Reddit(client_id=keys['REDDIT_CLIENT_ID'],
                             client_secret=keys['REDDIT_CLIENT_SECRET'],
                             user_agent="discord:extras.py (by /u/radiantsmurf)")
        submission = list(reddit.subreddit("politicalcompassmemes").top("day", limit=50))
        radint = random.randint(0, len(submission) - 1)
        embed = discord.Embed(title=submission[radint].title, color=ctx.message.author.color.value, url=submission[radint].shortlink)
        image = submission[radint].preview['images'][0]['source']['url']
        embed.set_image(url=image)
        embed.set_footer(text='⬆️ {} | 💬 {}'.format(submission[radint].score, submission[radint].num_comments))
        await ctx.send(content=None, embed=embed)

    @commands.command()
    async def serverinfo(self, ctx):
        embed = discord.Embed(title="Server Info", color=ctx.message.author.color.value)
        embed.add_field(name='Server name: ', value=ctx.message.guild.name)
        embed.add_field(name='Number of members: ', value=ctx.message.guild.member_count)
        embed.add_field(name='Server Owner: ', value=ctx.message.guild.owner, inline=False)
        embed.add_field(name='CPU Util:', value=psutil.cpu_percent(), inline=False)
        embed.add_field(name='Memory Util:', value=psutil.virtual_memory().percent)
        embed.set_thumbnail(url=ctx.message.guild.icon_url)
        await ctx.send(content=None, embed=embed)

    @commands.command(aliases=['google'])
    async def gsearch(self, ctx, *, args):
        service = build("customsearch", "v1", developerKey=my_api_key)
        res = service.cse().list(q=args, cx=my_cse_id).execute()
        firstitem = (res['items'][0]['title'], res['items'][0]['link'])
        embed = discord.Embed(title=firstitem[0], color=ctx.message.author.color.value, url=firstitem[1])
        if 'snippet' in res['items'][0].keys():
            embed.add_field(name='\u200b', value=res['items'][0]['snippet'].strip('\n').strip('\\').strip())
        if 'cse_thumbnail' in res['items'][0]['pagemap'].keys():
            embed.set_thumbnail(url=res['items'][0]['pagemap']['cse_thumbnail'][0]['src'])
        await ctx.send(content=None, embed=embed)

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

        embed = discord.Embed(title=hist['shortName'], color=ctx.message.author.color.value, url=hist['website'])
        embed.set_author(name=hist['symbol'])
        embed.set_thumbnail(url=hist['logo_url'])
        embed.add_field(name='Location:', value=hist['city'] + ', ' + hist['country'], inline=False)
        if float(c1) < 0.00:
            embed.add_field(name='Previous Close:', value=str(hist['previousClose']) + ' ▼' + ' (' + str(c1) + ')',
                            inline=False)
        else:
            embed.add_field(name='Previous Close:', value=str(hist['previousClose']) + ' ▲' + ' (' + str(c1) + ')',
                            inline=False)
        embed.add_field(name='Open:', value=hist['open'], inline=False)

        file = discord.File("./stock.png", filename="image.png")
        embed.set_image(url="attachment://image.png")
        await msg.delete()
        await ctx.send(file=file, embed=embed)
        plt.clf()
        os.remove('./stock.png')

    def stockChange(self, stock1):
        response1 = requests.get('https://sandbox.tradier.com/v1/markets/quotes',
                                 params={'symbols': stock1, 'greeks': 'false'},
                                 headers={'Authorization': keys['TRADIER_BEARER_TOKEN'],
                                          'Accept': 'application/json'})
        c1 = response1.json()['quotes']['quote']['change']
        return c1

    @commands.command()
    async def decode(self, ctx, wtd):
        data = base64.b64decode(wtd + "===")
        if '@' not in data.decode('utf-8'):
            await ctx.send(data.decode("utf-8"))
        else:
            await ctx.send('Stop @ing people')

    @commands.command()
    async def encode(self, ctx, *, wte):
        data = base64.b64encode(bytes(wte, 'utf-8'))
        if '@' not in data.decode('utf-8'):
            await ctx.send(data.decode("utf-8"))
        else:
            await ctx.send('Stop @ing people')

    @commands.command(aliases=['git'])
    async def github(self, ctx):
        await ctx.send('https://github.com/densumesh/my-stummy-bot')

def setup(client):
    client.add_cog(Extras(client))
