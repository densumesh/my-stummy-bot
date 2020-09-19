import asyncio
from spotdl import Spotdl
from spotdl.helpers.spotify import SpotifyHelpers
import discord
import random
from discord.ext import commands
import youtube_dl
from googleapiclient.discovery import build
from spotdl.lyrics.providers import Genius
from spotdl.authorize.services import AuthorizeSpotify
import html
import isodate
from spotdl.metadata_search import MetadataSearch
import json

queue = []
loopQueue = []
author = []
videos = []
urls = []
now = []

with open('keys.json', 'r') as fp:
    keys = json.load(fp)


AuthorizeSpotify(client_id=keys['SPOTIFY_CLIENT_ID'], client_secret=keys['SPOTIFY_CLIENT_SECRET'])

DEVELOPER_KEY = keys['YOUTUBE_DEVELOPER_KEY']
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

voicePaths = {'bullets': ['/home/ubuntu/my-bot/static/Animaker-Voice.mp3', 3], 
'singing challenge': ['/home/ubuntu/my-bot/static/Animaker-Voice (1).mp3', 5],
'roga dong': ['/home/ubuntu/my-bot/static/ttsMP3.com_VoiceText_2020-7-7_12_29_57.mp3', 4],
'despacito': ['/home/ubuntu/my-bot/static/ttsMP3.com_VoiceText_2020-7-7_12_29_28.mp3', 1],
'yeah yeah': ['/home/ubuntu/my-bot/static/ttsMP3.com_VoiceText_2020-7-7_12_28_43.mp3', 1],
'pewds': ['/home/ubuntu/my-bot/static/Pewdiepie says What A Fking N Word.mp3', 2]}

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'extractaudio': True,
    'audioformat': 'mp3',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

            
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.uploader = data.get('uploader')
        self.duration= self.parse_duration(int(data.get('duration')))
        self.queueurl = data.get("webpage_url")

    @classmethod
    async def from_url(cls, url, *, loop=None, ytdl, stream=False):
        try:
            loop = loop or asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
            if 'entries' in data:
                data = data['entries'][0]

            filename = data['url'] if stream else ytdl.prepare_filename(data)
            return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
        except:
            return 'Query not found'
    
    @staticmethod
    def parse_duration(duration: int):
        if duration == 0:
            return 'Live'
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []

        if days > 0:
            duration.append('{}'.format(days))
        if hours > 0:
            if hours < 10:
                duration.append('0{}'.format(hours))
            elif hours >= 10:
                duration.append('{}'.format(hours))
        if minutes > 0:
            if minutes < 10:
                duration.append('0{}'.format(minutes))
            elif minutes >= 10:
                duration.append('{}'.format(minutes))
        if minutes <= 0 and hours > 0:
            duration.append('00')
        elif minutes <= 0:
            duration.append('0')
        elif seconds <= 0:
            duration.append('00')
        if seconds > 0:
            if seconds < 10:
                duration.append('0{}'.format(seconds))
            elif seconds >= 10:
                duration.append('{}'.format(seconds))
        return ':'.join(duration)

class Music(commands.Cog):
    def __init__(self, bot):
        self.client = bot
        self.loop = False
        self.searchClear = False
        self.autoplay = False
        self.volume = 0.5

    async def song(self, ctx, url, ytdl):
        member = ctx.message.author
        if not member.voice == None:
            if ctx.voice_client is None:
                voice_channel = member.voice.channel
                vc = await voice_channel.connect()
                if not vc.is_playing():
                    player = await YTDLSource.from_url(url, ytdl = ytdl, loop=self.client.loop, stream=True)
                    if player == 'Query not found':
                        await ctx.send(player)
                        return
                    vc.play(player, after=lambda e: self.play_next(ctx))
                    author.append(ctx.message.author)
                    now.append(player)
                    await ctx.message.add_reaction('⏯')
                    await ctx.send('Now playing: **{}** ({}). Requested by: `{}`'.format(player.title, player.duration, str(ctx.message.author.display_name)))
                else:
                    player = await YTDLSource.from_url(url, ytdl = ytdl,loop=self.client.loop, stream=True)
                    if player == 'Query not found':
                        await ctx.send(player)
                        return
                    queue.append(player)
                    now.append(player)
                    author.append(ctx.message.author)
                    await ctx.send('**{}** ({}) queued. Position in queue: `{}`'.format(player.title, player.duration, len(queue)))
            else:
                if not ctx.voice_client.is_playing():
                    player = await YTDLSource.from_url(url, ytdl = ytdl, loop=self.client.loop, stream=True)
                    if player == 'Query not found':
                        await ctx.send(player)
                        return
                    ctx.voice_client.play(player, after=lambda e: self.play_next(ctx))
                    author.append(ctx.message.author)
                    now.append(player)
                    await ctx.message.add_reaction('⏯')
                    await ctx.send('Now playing: **{}** ({}). Requested by: `{}`'.format(player.title, player.duration, str(ctx.message.author.display_name)))
                else:
                    player = await YTDLSource.from_url(url, ytdl = ytdl,loop=self.client.loop, stream=True)
                    if player == 'Query not found':
                        await ctx.send(player)
                        return
                    queue.append(player)
                    now.append(player)
                    author.append(ctx.message.author)
                    await ctx.send('**{}** ({}) queued. Position in queue: `{}`'.format(player.title, player.duration, len(queue)))
        else:
            await ctx.send('You are not connected to a voice channel', delete_after = 20)

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error, delete_after = 20)
        
    @commands.command()
    async def lyrics(self, ctx, *args):
        genius = Genius()
        if not str(args) == '()':
            lyrics = genius.from_query(' '.join(args))
            lyric = lyrics.split("\n\n")
            embed = discord.Embed(title='Lyrics for ' + ' '.join(args), color = 0x1d68e0)
        else:
            if not ctx.voice_client is None:
                lyrics = genius.from_query(now[-len(queue)-1].title)
                lyric = lyrics.split("\n\n")
                embed = discord.Embed(title='Lyrics for ' + now[-len(queue)-1].title, color = 0x1d68e0)
            else:
                await ctx.send('No song is currently playing', delete_after = 20)
        for l in lyric:
            if len(l) >= 1000:
                print('big')
                res_first, res_second = l[:len(l)//2],  l[len(l)//2:]
                print(len(res_first))
                print(len(res_second))
                embed.add_field(name= '\u200b',value= res_first, inline=False)
                embed.add_field(name= '\u200b',value= res_second, inline=False)
            else:
                embed.add_field(name= '\u200b',value= l, inline=False)
        await ctx.send(content=None, embed=embed)
    
    @commands.command()
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
        deleted = await ctx.channel.purge(limit=limit, check=check_msg)
        msg = await ctx.send('Purged ' + len(deleted) + 'messages')
        await asyncio.sleep(2)
        await msg.delete()

    @commands.command()
    async def pause(self, ctx):
        if not ctx.voice_client is None:
            await ctx.message.add_reaction('⏸')
            ctx.voice_client.pause()   
        else:
            await ctx.send('Not connected to a voice channel', delete_after = 20)
    
    @commands.command()
    async def shuffle(self, ctx):
        random.shuffle(queue)
        await ctx.message.add_reaction('🔀')

    @commands.command()
    async def resume(self, ctx):
        if not ctx.voice_client is None:
            ctx.voice_client.resume()
            await ctx.message.add_reaction('▶️')
        else:
            await ctx.send('Not connected to a voice channel', delete_after = 30)
    
    @commands.command()
    async def stop(self, ctx):
        if not ctx.voice_client is None:
            await ctx.voice_client.disconnect()
            loopQueue.clear()
            queue.clear()
            await ctx.message.add_reaction('🛑')
        else:
            await ctx.send('Not connected to a voice channel', delete_after = 20)
    
    @commands.command()
    async def clear(self, ctx):
        loopQueue.clear()
        queue.clear()
        await ctx.send('Cleared', delete_after = 20)
        await ctx.message.add_reaction('🍑')
    
    
    @commands.command(aliases = ['p'])
    async def play(self, ctx, *args):
        if not str(args) == '()':
            ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
            if not self.loop:
                if 'https://open.spotify.com/track' in ' '. join(args):
                    searcher = MetadataSearch(' '. join(args))
                    metadata = searcher.on_youtube_and_spotify()
                    await self.song(ctx,metadata["external_urls"]["youtube"], ytdl)
                    loopQueue.append(metadata["external_urls"]["youtube"])              
                else:
                    ytdl_format_options['default_search'] = 'ytsearch'
                    ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
                    await self.song(ctx,' '. join(args), ytdl) 
                    loopQueue.append(' '.join(args))
            else:
                await ctx.send('Music is looping, unloop to add music to the queue', delete_after = 20)
        else:
            ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
            youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
            developerKey=DEVELOPER_KEY)
            runOnce = True
            request = youtube.search().list(
                part="snippet",
                maxResults=1,
                order="relevance",
                regionCode="US",
                relevanceLanguage="en",
                type="video",
                videoCategoryId="10"
            ).execute()

            for search_result in request.get('items', []):
                if runOnce:
                    await self.song(ctx, 'https://www.youtube.com/watch?v=' + search_result['id']['videoId'], ytdl)
                    runOnce = False
                else:
                    player = await YTDLSource.from_url('https://www.youtube.com/watch?v=' + search_result['id']['videoId'], ytdl = ytdl, loop=self.client.loop, stream=True)
                    queue.append(player)
                    now.append(player)
                    author.append(ctx.message.author)
                    
    @commands.command(aliases = ['sc']) 
    async def soundcloud(self, ctx, *args):
        if not self.loop:
            ytdl_format_options['default_search'] = 'scsearch'
            ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
            await self.song(ctx,' '. join(args), ytdl)   
            loopQueue.append(' '.join(args))
        else:
            await ctx.send('Music is looping, unloop to add music to the queue', delete_after = 20)

    @commands.command()
    async def search(self, ctx, *args):
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
            developerKey=DEVELOPER_KEY)

        if self.searchClear:
            urls.clear()
            videos.clear()
            self.searchClear = False

        search_response = youtube.search().list(
            q=' '.join(args),
            part='id,snippet',
            type='video',
            maxResults=5,
            safeSearch = 'strict'
        ).execute()

        for i, search_result in enumerate(search_response.get('items', [])):
            request = youtube.videos().list( 
                part="contentDetails",
                id=search_result['id']['videoId']).execute()

            duration = isodate.parse_duration(request['items'][0]['contentDetails']['duration'])
            duration1 = str(duration).split(':')

            if duration1[0] == '0':
                del duration1[0]

            duration = ':'.join(duration1)
            videos.append('{}. {} - {} ({})'.format(i+1, search_result['snippet']['title'], search_result['snippet']['channelTitle'], str(duration)))
            urls.append('https://www.youtube.com/watch?v=' + search_result['id']['videoId'])
            
        self.searchClear = True
        self.sent = await ctx.send('Choose the number of the video you would like + $.\n' + html.unescape('\n'.join(videos) + '\n'))

    @commands.command(name = '1')
    async def one(self, ctx):
        self.searchClear = False
        url = urls[0]
        ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        await self.sent.delete()
        await self.song(ctx,url, ytdl)  
        urls.clear()
        videos.clear()
        loopQueue.append(url)
    
    @commands.command(name = '2')
    async def two(self, ctx):
        self.searchClear = False
        url = urls[1]
        ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        await self.sent.delete()
        await self.song(ctx,url, ytdl)        
        urls.clear()
        videos.clear()
        loopQueue.append(url)

    @commands.command(name = '3')
    async def three(self, ctx):
        self.searchClear = False
        url = urls[2]
        ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        await self.sent.delete()
        await self.song(ctx,url, ytdl)  
        urls.clear()
        videos.clear()
        loopQueue.append(url)

    @commands.command(name = '4')
    async def four(self, ctx):
        self.searchClear = False
        url = urls[3]
        ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        await self.sent.delete()
        await self.song(ctx,url, ytdl)  
        urls.clear()
        videos.clear()
        loopQueue.append(url)

    @commands.command(name = '5')
    async def five(self, ctx):
        self.searchClear = False
        url = urls[4]
        ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        await self.sent.delete()
        await self.song(ctx,url, ytdl)  
        urls.clear()
        videos.clear()
        loopQueue.append(url)

    @commands.command()
    async def cancel(self, ctx):
        urls.clear()
        videos.clear()
        await self.sent.delete()
        await ctx.send('Canceled', delete_after = 20)

    @commands.command(aliases = ['s'])
    async def skip(self, ctx):
        if not self.loop:
            if not ctx.voice_client is None:
                if len(queue) >= 1:
                    if not isinstance(ctx, discord.guild.Guild):
                        await ctx.message.add_reaction('⏭')
                    ctx.voice_client.pause()
                    ctx.voice_client.play(source=queue[0], after=lambda e: self.play_next(ctx))
                    ctx.voice_client.source.volume = self.volume
                    if not isinstance(ctx, discord.guild.Guild):
                        asyncio.run_coroutine_threadsafe(ctx.send('Now playing: **{}** ({}). Requested by: `{}`'.format(queue[0].title, queue[0].duration,str(author[-len(queue)-1].display_name))), self.client.loop)
                    else:
                        channel = ctx.get_channel(725907147904253993)
                        asyncio.run_coroutine_threadsafe(channel.send('Now playing: **{}** ({}). Requested by: `{}`'.format(queue[0].title, queue[0].duration,str(author[-len(queue)-1].display_name))), self.client.loop)
                    del queue[0]
                    
                else:
                    ctx.voice_client.pause()
                    if not isinstance(ctx, discord.guild.Guild):
                        await ctx.send('No songs in queue right now.', delete_after = 20)
                    else:
                        channel = ctx.get_channel(725907147904253993)
                        await channel.send('No songs in queue right now.', delete_after = 20)
            else:
                await ctx.send('Not connected to a voice channel', delete_after = 20)
        else:
            if not isinstance(ctx, discord.guild.Guild):
                await ctx.send('Music is currently looping, please unloop to skip', delete_after = 20)
            else:
                channel = ctx.get_channel(725907147904253993)
                await channel.send('Music is currently looping, please unloop to skip', delete_after = 20)

    @commands.command(name = 'queue', aliases = ['q'])
    async def _queue(self, ctx):
        field = []
        if not self.loop:
            embed = discord.Embed(title="Queue", color = 0x1d68e0)
            embed.add_field(value= '{} | `{} Requested by: {}`' .format(now[-len(queue)-1].title, now[-len(queue)-1].duration, str(author[-len(queue)-1].display_name)), name= '__Currently Playing:__', inline=False)

            if len(queue) >= 1:
                for i in range(len(queue)):
                    field.append('`{}`. {} | `{} Requested by: {}`' .format(i + 1, queue[i].title,queue[i].duration,str(author[-i-1].display_name)))
                firstpage = field[0:10]
                embed.add_field(name= '__Up Next:__', value = '\n\n'.join(firstpage), inline = False)
                embed.set_footer(text= "{} songs in queue | Page 1 | 1-10".format(len(queue)), icon_url=ctx.message.author.avatar_url)
            await ctx.send(content=None, embed=embed)
        else:
            await ctx.send('Music is looping currently', delete_after = 20)

    @commands.command()
    async def autoplay(self, ctx):
        self.autoplay = not self.autoplay
        ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        if self.autoplay:
            await ctx.send('Autoplay on!')
            youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
            developerKey=DEVELOPER_KEY)
            url = self.remove_prefix(now[-len(queue)-1].queueurl, 'https://www.youtube.com/watch?v=')
            search_response = youtube.search().list(
                relatedToVideoId= url,
                part='snippet',
                type='video',
                maxResults=10,
                safeSearch = 'strict'
            ).execute()

            for search_result in search_response.get('items', []):
                player = await YTDLSource.from_url('https://www.youtube.com/watch?v=' + search_result['id']['videoId'], ytdl = ytdl, loop=self.client.loop, stream=True)
                queue.append(player)
                now.append(player)
                author.append(ctx.message.author)
        else:
            await ctx.send('Autoplay off!')

    @commands.command(aliases = ['replay'])
    async def restart(self, ctx):
        ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        player = await YTDLSource.from_url(loopQueue[-len(queue) - 1], ytdl = ytdl,loop=self.client.loop, stream=True)
        ctx.voice_client.pause()
        ctx.voice_client.play(source=player, after=lambda e: self.play_next(ctx))
        await ctx.message.add_reaction('🔁')
    
    @commands.command(aliases = ['r'])
    async def remove(self, ctx, index: int):
        if len(queue) == 0:
            await ctx.send('Empty queue.')
        else:
            queue.pop(index - 1)
            await ctx.message.add_reaction('💥')

    def remove_prefix(self, text, prefix):
        if text.startswith(prefix):
            return text[len(prefix):]
        return text
    

    @commands.command(aliases = ['l'])
    async def loop(self, ctx, i = 20):
        self.loop = not self.loop
        ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        if self.loop:
            await ctx.message.add_reaction('🔁')
            for _ in range(i):
                player = await YTDLSource.from_url(loopQueue[-1], ytdl = ytdl,loop=self.client.loop, stream=True)
                queue.append(player)
            loopQueue.clear()
        else:
            queue.clear()
            loopQueue.clear()
            await ctx.send('Stopping loop', delete_after = 30)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel is None and after.channel is not None:
            if str(member) == 'el b1ACk#8323':
                choice = random.choice(list(voicePaths.keys()))
                voice = await member.voice.channel.connect()
                voice.play(discord.FFmpegPCMAudio(voicePaths[choice][0]))
                await asyncio.sleep(voicePaths[choice][1])
                await voice.disconnect()
        if before.channel is not None and after.channel is None:
            if str(member) == 'alBY#4055':
                queue.clear()
                loopQueue.clear()
                now.clear()
        if str(member) == 'alBY#4055':
            if after.mute:
                await self.skip(member.guild)
                asyncio.sleep(2)
                await member.edit(mute=False)


    def play_next(self, ctx):
        if len(queue) >= 1:
            ctx.voice_client.play(source=queue[0], after=lambda e: self.play_next(ctx))
            ctx.voice_client.source.volume = self.volume
            if not self.loop:
                if not isinstance(ctx, discord.guild.Guild):
                    asyncio.run_coroutine_threadsafe(ctx.send('Now playing: **{}** ({}). Requested by: `{}`'.format(queue[0].title, queue[0].duration,str(author[-len(queue)-1].display_name))), self.client.loop)
                else:
                    channel = ctx.get_channel(725907147904253993)
                    asyncio.run_coroutine_threadsafe(channel.send('Now playing: **{}** ({}). Requested by: `{}`'.format(queue[0].title, queue[0].duration,str(author[-len(queue)-1].display_name))), self.client.loop)
            del queue[0]
        else:
            now.clear()
            loopQueue.clear()
            self.autoplay = False
            asyncio.run_coroutine_threadsafe(asyncio.sleep(90), self.client.loop)
            if not ctx.voice_client.is_playing():
                asyncio.run_coroutine_threadsafe(ctx.voice_client.disconnect(), self.client.loop)


    @commands.command(aliases = ['v'])
    async def volume(self, ctx, volume: int):
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.", delete_after = 20)
            
        ctx.voice_client.source.volume = volume / 100
        self.volume = volume / 100
        await ctx.send("Changed volume to **{}%**".format(volume))
    
