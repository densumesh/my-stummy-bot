import asyncio
import traceback
import html
import json
import os
import time
import random
from logging import ERROR
import datetime
import discord
import traceback
import isodate
import youtube_dl
from discord.ext import commands
from googleapiclient.discovery import build
from spotdl.lyrics.providers import Genius
import spotipy
from spotdl.authorize.services import AuthorizeSpotify
from spotipy.oauth2 import SpotifyClientCredentials

auth_manager = SpotifyClientCredentials(client_id='dd587f9d89f54c43a274fa90660cdfd1', client_secret='797a8619cfcd44efafc63e519a42a4cb')
sp = spotipy.Spotify(auth_manager=auth_manager)

queue = []
videos = []
urls = []

with open('keys.json', 'r') as fp:
    keys = json.load(fp)

AuthorizeSpotify(client_id=keys['SPOTIFY_CLIENT_ID'], client_secret=keys['SPOTIFY_CLIENT_SECRET'])

DEVELOPER_KEY = keys['YOUTUBE_DEVELOPER_KEY']
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''
OPTIONS = {
    "1️⃣": 0,
    "2⃣": 1,
    "3⃣": 2,
    "4⃣": 3,
    "5⃣": 4,
}
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'extractaudio': True,
    'audioformat': 'mp3',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    "force-generic-extractor": True
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}


class DownloadError(commands.CommandError):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.uploader = data.get('uploader')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.queueurl = data.get("webpage_url")

    @classmethod
    async def from_url(cls, url, *, loop=None, ytdl, stream=False):
        try:
            loop = loop or asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
            if 'entries' in data:
                data = data['entries'][0]
            if data is None:
                return "Couldn't find anything that matches `{}`".format(url)
            filename = data['url'] if stream else ytdl.prepare_filename(data)
            return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
        except youtube_dl.DownloadError as e:
            return str(e)

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
        if minutes <= 0 < hours:
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

    def requester_check():
        def predicate(ctx):
            return ctx.message.author == ctx.voice_client.source.requester
        return commands.check(predicate)

    async def song(self, ctx, url, ytdl):
        member = ctx.message.author
        if member.voice is not None:
            if ctx.voice_client is None:
                voice_channel = member.voice.channel
                vc = await voice_channel.connect()
                if not vc.is_playing():
                    player = await YTDLSource.from_url(url, ytdl=ytdl, loop=self.client.loop, stream=True)
                    if isinstance(player, str):
                        await ctx.send(player, delete_after=20)
                        raise DownloadError
                    vc.play(player, after=lambda e: self.play_next(ctx))
                    player.requester = ctx.message.author
                    await ctx.message.add_reaction('⏯')
                    await ctx.send('Now Playing: **{}** ({}). Requested by: `{}`'.format(player.title, player.duration, str(ctx.message.author.display_name)))
                    await self.client.change_presence(activity=discord.Game(name="Now Playing: {} ({})".format(player.title, player.duration)))
                else:
                    if not self.autoplay:
                        player = await YTDLSource.from_url(url, ytdl=ytdl, loop=self.client.loop, stream=True)
                        if isinstance(player, str):
                            await ctx.send(player, delete_after=20)
                            raise DownloadError
                        player.requester = ctx.message.author
                        queue.append(player)
                        await ctx.send('**{}** ({}) queued. Position in queue: `{}`'.format(player.title, player.duration, len(queue)))
                    else:
                        player = await YTDLSource.from_url(url, ytdl=ytdl, loop=self.client.loop, stream=True)
                        if isinstance(player, str):
                            await ctx.send(player, delete_after=20)
                            raise DownloadError
                        player.requester = ctx.message.author
                        queue.insert(0, player)
                        await ctx.send(
                            '**{}** ({}) queued. Position in queue: `1`'.format(player.title, player.duration))
            else:
                if not ctx.voice_client.is_playing():
                    player = await YTDLSource.from_url(url, ytdl=ytdl, loop=self.client.loop, stream=True)
                    if isinstance(player, str):
                        await ctx.send(player)
                        raise DownloadError
                    ctx.voice_client.play(player, after=lambda e: self.play_next(ctx))
                    player.requester = ctx.message.author
                    await ctx.message.add_reaction('⏯')
                    await ctx.send('Now Playing: **{}** ({}). Requested by: `{}`'.format(player.title, player.duration,
                                                                                         str(ctx.message.author.display_name)))
                    await self.client.change_presence(
                        activity=discord.Game(name="Now Playing: {} ({})".format(player.title, player.duration)))
                else:
                    if not self.autoplay:
                        player = await YTDLSource.from_url(url, ytdl=ytdl, loop=self.client.loop, stream=True)
                        if isinstance(player, str):
                            await ctx.send(player)
                            raise DownloadError
                        player.requester = ctx.message.author
                        queue.append(player)
                        await ctx.send(
                            '**{}** ({}) queued. Position in queue: `{}`'.format(player.title, player.duration,
                                                                                 len(queue)))
                    else:
                        player = await YTDLSource.from_url(url, ytdl=ytdl, loop=self.client.loop, stream=True)
                        if isinstance(player, str):
                            await ctx.send(player)
                            raise DownloadError
                        player.requester = ctx.message.author
                        queue.insert(0, player)
                        await ctx.send(
                            '**{}** ({}) queued. Position in queue: `1`'.format(player.title, player.duration))
        else:
            await ctx.send('You are not connected to a voice channel', delete_after=20)

    async def cog_command_error(self, ctx, error):
        await ctx.send(str(error).strip('Command raised an exception: '), delete_after=20)
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(traceback.format_exc(), delete_after=20)

    @commands.command()
    async def lyrics(self, ctx, *args):
        genius = Genius()
        lyric = None
        if not str(args) == '()':
            lyrics = genius.from_query(' '.join(args))
            lyric = lyrics.split("\n\n")
            embed = discord.Embed(title='Lyrics for ' + ' '.join(args), color=ctx.message.author.color.value)
        else:
            if ctx.voice_client is not None:
                try:
                    lyrics = genius.from_query(ctx.voice_client.source.title)
                    lyric = lyrics.split("\n\n")
                    embed = discord.Embed(title='Lyrics for ' + ctx.voice_client.source.title, color=ctx.message.author.color.value)
                except:
                    await ctx.send('Genius could not find `{}`. Please retry and provide the song name.'.format(ctx.voice_client.source.title))
            else:
                await ctx.send('No song is currently playing', delete_after=20)
        if lyric:
            for l in lyric:
                if len(l) >= 1000:
                    res_first, res_second = l[:len(l) // 2], l[len(l) // 2:]
                    embed.add_field(name='\u200b', value=res_first, inline=False)
                    embed.add_field(name='\u200b', value=res_second, inline=False)
                else:
                    embed.add_field(name='\u200b', value=l, inline=False)
            await ctx.send(content=None, embed=embed)

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client is not None:
            await ctx.message.add_reaction('⏸')
            ctx.voice_client.pause()
        else:
            await ctx.send('Not connected to a voice channel', delete_after=20)

    @commands.command()
    async def shuffle(self, ctx):
        random.shuffle(queue)
        await ctx.message.add_reaction('🔀')

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client is not None:
            ctx.voice_client.resume()
            await ctx.message.add_reaction('▶️')
        else:
            await ctx.send('Not connected to a voice channel', delete_after=30)

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()
            queue.clear()
            await ctx.message.add_reaction('🛑')
        else:
            await ctx.send('Not connected to a voice channel', delete_after=20)

    @commands.command()
    async def clear(self, ctx):
        queue.clear()
        await ctx.send('Cleared', delete_after=20)
        await ctx.message.add_reaction('🍑')

    @commands.command(aliases=['p'])
    async def play(self, ctx, *args):
        ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        if not self.loop:
            if 'https://open.spotify.com/track' in ' '.join(args):
                track = sp.track(' '.join(args))
                await self.song(ctx, '{} - {}'.format(track['artists'][0]['name'], track['name']), ytdl)
            else:
                ytdl_format_options['default_search'] = 'ytsearch'
                ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
                await self.song(ctx, ' '.join(args), ytdl)
        else:
            await ctx.send('Music is looping, unloop to add music to the queue', delete_after=20)

    @commands.command(aliases=['sc'])
    async def soundcloud(self, ctx, *args):
        if not self.loop:
            ytdl_format_options['default_search'] = 'scsearch'
            ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
            await self.song(ctx, ' '.join(args), ytdl)
        else:
            await ctx.send('Music is looping, unloop to add music to the queue', delete_after=20)

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
            safeSearch='strict'
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
            videos.append('{}. {} - {} ({})'.format(i + 1, search_result['snippet']['title'],
                                                    search_result['snippet']['channelTitle'], str(duration)))
            urls.append('https://www.youtube.com/watch?v=' + search_result['id']['videoId'])

        self.searchClear = True

        def _check(r, u):
            return (
                    r.emoji in OPTIONS.keys()
                    and u == ctx.author
                    and r.message.id == msg.id
            )

        embed = discord.Embed(
            title="Choose the number of the video you would like.",
            description=(
                html.unescape('\n'.join(videos)
                )
            ),
            colour=ctx.message.author.color.value
        )
        embed.set_author(name="Search Results")
        embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        msg = await ctx.send(embed=embed)
        for emoji in list(OPTIONS.keys())[:min(len(videos), len(OPTIONS))]:
            await msg.add_reaction(emoji)

        try:
            reaction, _ = await self.client.wait_for("reaction_add", timeout=60.0, check=_check)
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.message.delete()
        else:
            await msg.delete()
            self.searchClear = False
            url = urls[int(OPTIONS[reaction.emoji])]
            ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
            await self.song(ctx, url, ytdl)
            urls.clear()
            videos.clear()

    @commands.command()
    async def cancel(self, ctx):
        urls.clear()
        videos.clear()
        await self.sent.delete()
        await ctx.send('Canceled', delete_after=20)

    @commands.command(aliases=['s', 'fs'])
    async def skip(self, ctx):
        if not self.loop:
            if ctx.voice_client is not None:
                if len(queue) >= 1:
                    if not isinstance(ctx, discord.guild.Guild):
                        await ctx.message.add_reaction('⏭')
                    ctx.voice_client.pause()
                    ctx.voice_client.play(source=queue[0], after=lambda e: self.play_next(ctx))
                    ctx.voice_client.source.volume = self.volume
                    if not isinstance(ctx, discord.guild.Guild):
                        asyncio.run_coroutine_threadsafe(ctx.send(
                            'Now playing: **{}** ({}). Requested by: `{}`'.format(queue[0].title, queue[0].duration,
                                                                                  str(queue[0].requester.display_name))),
                            self.client.loop)
                        await self.client.change_presence(
                            activity=discord.Game(name="Now Playing: {} ({})".format(queue[0].title, queue[0].duration)))
                    else:
                        channel = ctx.get_channel(725907147904253993)
                        asyncio.run_coroutine_threadsafe(channel.send(
                            'Now Playing: **{}** ({}). Requested by: `{}`'.format(queue[0].title, queue[0].duration,
                                                                                  str(queue[0].requester.display_name))),
                            self.client.loop)
                        await self.client.change_presence(
                            activity=discord.Game(name="Now Playing: {} ({})".format(queue[0].title, queue[0].duration)))
                    del queue[0]

                else:
                    ctx.voice_client.pause()
                    await self.client.change_presence(
                        activity=discord.Game(name="$help | Carti's stummy hurts"))
                    if not isinstance(ctx, discord.guild.Guild):
                        await ctx.send('No songs in queue right now.', delete_after=20)
                    else:
                        channel = ctx.get_channel(725907147904253993)
                        await channel.send('No songs in queue right now.', delete_after=20)
            else:
                await ctx.send('Not connected to a voice channel', delete_after=20)
        else:
            if not isinstance(ctx, discord.guild.Guild):
                await ctx.send('Music is currently looping, please unloop to skip', delete_after=20)
            else:
                channel = ctx.get_channel(725907147904253993)
                await channel.send('Music is currently looping, please unloop to skip', delete_after=20)

    @commands.command(name='queue', aliases=['q'])
    async def _queue(self, ctx):
        try:
            field = []
            if not self.loop:
                embed = discord.Embed(title="Queue", color=ctx.message.author.color.value)
                embed.add_field(
                    value='{} | `{} Requested by: {}`'.format(ctx.voice_client.source.title, ctx.voice_client.source.duration,
                                                              str(ctx.voice_client.source.requester.display_name)),
                    name='__Currently Playing:__', inline=False)

                if len(queue) >= 1:
                    for i in range(len(queue)):
                        field.append('`{}`. {} | `{} Requested by: {}`'.format(i + 1, queue[i].title, queue[i].duration,
                                                                               str(queue[i].requester.display_name)))
                    firstpage = field[0:10]
                    embed.add_field(name='__Up Next:__', value='\n\n'.join(firstpage), inline=False)
                    embed.set_footer(text="{} songs in queue | Page 1 | 1-10".format(len(queue)),
                                     icon_url=ctx.message.author.avatar_url)
                await ctx.send(content=None, embed=embed)
            else:
                await ctx.send('Music is looping currently', delete_after=20)
        except:
            await ctx.send('No songs in queue.')

    @commands.command()
    async def autoplay(self, ctx):
        self.autoplay = not self.autoplay
        ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        if self.autoplay:
            await ctx.send('Autoplay on!')
            youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                            developerKey=DEVELOPER_KEY)
            url = self.remove_prefix(ctx.voice_client.source.queueurl, 'https://www.youtube.com/watch?v=')
            search_response = youtube.search().list(
                relatedToVideoId=url,
                part='snippet',
                type='video',
                maxResults=10,
                safeSearch='strict'
            ).execute()

            for search_result in search_response.get('items', []):
                player = await YTDLSource.from_url('https://www.youtube.com/watch?v=' + search_result['id']['videoId'],
                                                   ytdl=ytdl, loop=self.client.loop, stream=True)
                player.requester = ctx.message.author
                queue.append(player)

        else:
            await ctx.send('Autoplay off!')

    @commands.command(aliases=['replay'])
    async def restart(self, ctx):
        ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        player = await YTDLSource.from_url(ctx.voice_client.source.title, ytdl=ytdl, loop=self.client.loop, stream=True)
        ctx.voice_client.pause()
        ctx.voice_client.play(source=player, after=lambda e: self.play_next(ctx))
        await ctx.message.add_reaction('🔁')

    @commands.command(aliases=['r'])
    async def remove(self, ctx, index: int):
        if len(queue) == 0:
            await ctx.send('Empty queue.')
        else:
            await ctx.send('Removed `{} - {}`'.format(queue[index-1].title, queue[index-1].author))
            queue.pop(index - 1)
            await ctx.message.add_reaction('💥')

    def remove_prefix(self, text, prefix):
        if text.startswith(prefix):
            return text[len(prefix):]
        return text

    @commands.command(aliases=['pspot', 'pspotify'])
    async def play_spotify(self, ctx):
        if not self.loop:
            member = ctx.message.author
            ytdl_format_options['default_search'] = 'ytsearch'
            ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
            for activity in member.activities:
                if isinstance(activity, discord.Spotify):
                    await self.song(ctx, activity.title + " " + activity.artists[0], ytdl)
        else:
            await ctx.send('Music is looping, unloop to add music to the queue', delete_after=20)

    @commands.command(aliases=['l'])
    async def loop(self, ctx, i=20):
        self.loop = not self.loop
        ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        if self.loop:
            await ctx.message.add_reaction('🔁')
            for _ in range(i):
                player = await YTDLSource.from_url(ctx.voice_client.source.title, ytdl=ytdl, loop=self.client.loop, stream=True)
                queue.append(player)
        else:
            queue.clear()
            await ctx.send('Stopping loop', delete_after=30)

    @commands.command()
    async def unloop(self, ctx):
        self.loop = False
        queue.clear()
        await ctx.send('Stopping loop', delete_after=30)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel is not None and after.channel is None:
            if str(member) == 'alBY#4055':
                queue.clear()
                self.autoplay = False
        if str(member) == 'alBY#4055':
            if after.mute:
                await self.skip(member.guild)
                await member.edit(mute=False)

    def play_next(self, ctx):
        if len(queue) >= 1:
            ctx.voice_client.play(source=queue[0], after=lambda e: self.play_next(ctx))
            ctx.voice_client.source.volume = self.volume
            if not self.loop:
                if not isinstance(ctx, discord.guild.Guild):
                    asyncio.run_coroutine_threadsafe(ctx.send(
                        'Now Playing: **{}** ({}). Requested by: `{}`'.format(queue[0].title, queue[0].duration,
                                                                              str(queue[0].requester.display_name))),
                        self.client.loop)
                    asyncio.run_coroutine_threadsafe(self.client.change_presence(
                        activity=discord.Game(name="Now Playing: {} ({})".format(queue[0].title, queue[0].duration))), self.client.loop)
                else:
                    channel = ctx.get_channel(725907147904253993)
                    asyncio.run_coroutine_threadsafe(channel.send(
                        'Now Playing: **{}** ({}). Requested by: `{}`'.format(queue[0].title, queue[0].duration,
                                                                              str(queue[0].requester.display_name))),
                        self.client.loop)
                    asyncio.run_coroutine_threadsafe(self.client.change_presence(
                        activity=discord.Game(name="Now Playing: {} ({})".format(queue[0].title, queue[0].duration))), self.client.loop)
            del queue[0]
        else:
            self.autoplay = False
            asyncio.run_coroutine_threadsafe(self.client.change_presence(
                activity=discord.Game(name="$help | Carti's stummy hurts")),
                self.client.loop)
            asyncio.run_coroutine_threadsafe(asyncio.sleep(5), self.client.loop)
            asyncio.run_coroutine_threadsafe(ctx.voice_client.disconnect(), self.client.loop)

    @commands.command(aliases=['v'])
    async def volume(self, ctx, volume: int):
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.", delete_after=20)

        ctx.voice_client.source.volume = volume / 100
        self.volume = volume / 100
        await ctx.send("Changed volume to **{}%**".format(volume))

def setup(client):
    client.add_cog(Music(client))
