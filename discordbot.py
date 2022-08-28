import asyncio
from typing import Dict, List, Optional
import aiohttp
import discord
from discord.ext import commands
import os
import traceback
import re
import emoji
import json
import jaconv
import cyrtranslit
import pinyin
import pycld2 as cld2
from langdetect import detect
from ko_pron import romanise
from english_to_kana import EnglishToKana

DEBUG = False
pastauthor: Dict[int, discord.abc.User] = {}

intents = discord.Intents.default()
intents.message_content = True

if not DEBUG:
    pass
    prefix = os.getenv('DISCORD_BOT_PREFIX', default='🦑')
    token = os.environ['DISCORD_BOT_TOKEN']
    voicevox_key = os.environ['VOICEVOX_KEY']
    voicevox_speaker = os.getenv('VOICEVOX_SPEAKER', default='2')
else:
    prefix = "/"
    token = os.environ['GEKKA_DISCORD_BOT_TOKEN']
    voicevox_key = os.environ['GEKKA_VOICEVOX_KEY']
    voicevox_speaker = "2"


client = commands.Bot(command_prefix=prefix, intents=intents)
with open('emoji_ja.json', encoding='utf-8') as file:
    emoji_dataset = json.load(file)

ETK = EnglishToKana()


@client.event
async def on_ready():
    print('Logged in as ' + client.user.name)
    presence = f'{prefix}ヘルプ | 0/{len(client.guilds)}サーバー'
    await client.change_presence(activity=discord.Game(name=presence))


@client.event
async def on_guild_join(guild: discord.Guild):
    presence = f'{prefix}ヘルプ | {len(client.voice_clients)}/{len(client.guilds)}サーバー'
    await client.change_presence(activity=discord.Game(name=presence))


@client.event
async def on_guild_remove(guild: discord.Guild):
    presence = f'{prefix}ヘルプ | {len(client.voice_clients)}/{len(client.guilds)}サーバー'
    await client.change_presence(activity=discord.Game(name=presence))


@client.command(alias=["connect", "con"])
async def 接続(ctx: commands.Context):
    if ctx.message.guild:
        if ctx.author.voice is None:
            await ctx.send('ボイスチャンネルに接続してから呼び出してください。')
        else:
            if ctx.guild.voice_client:
                if ctx.author.voice.channel == ctx.guild.voice_client.channel:
                    await ctx.send('接続済みです。')
                else:
                    await ctx.voice_client.disconnect()
                    await asyncio.sleep(0.5)
                    await ctx.author.voice.channel.connect()
            else:
                await ctx.author.voice.channel.connect()


@client.command(alias=["disconnect", "discon", "dis"])
async def 切断(ctx: commands.Context):
    if ctx.message.guild:
        if ctx.voice_client is None:
            await ctx.send('ボイスチャンネルに接続していません。')
        else:
            await ctx.voice_client.disconnect()


def text_converter(text: str, message: Optional[discord.Message] = None, now_author: Optional[discord.Member] = None) -> str:
    """
    the converter of text for voicevox
    """
    print("got text:", text, end="")
    detected_lang: Optional[str] = None
    try:
        isReliable, textBytesFound, details = cld2.detect(text)
        detected_lang = details[0][1]
    except cld2.error as e:
        # print("ignore error:", e)
        pass

    # Replace new line
    text = text.replace('\n', '、')
    if isinstance(message, discord.Message):
        # Add author's name
        if now_author:
            text = message.author.display_name + '、' + text

        # Replace mention to user
        user_mentions: List[discord.Member] = message.mentions
        for um in user_mentions:
            text = text.replace(
                f"<@{um.id}>", f"、{um.display_name}さんへのメンション")

        # Replace mention to role
        role_mentions: List[discord.Role] = message.role_mentions
        for rm in role_mentions:
            text = text.replace(
                rm.mention, f"、{rm.name}へのメンション")

    # Replace Unicode emoji
    text = re.sub(r'[\U0000FE00-\U0000FE0F]', '', text)
    text = re.sub(r'[\U0001F3FB-\U0001F3FF]', '', text)
    for char in text:
        if char in emoji.UNICODE_EMOJI['en'] and char in emoji_dataset:
            text = text.replace(char, emoji_dataset[char]['short_name'])

    # Replace Discord emoji
    pattern = r'<:([a-zA-Z0-9_]+):\d+>'
    match = re.findall(pattern, text)
    for emoji_name in match:
        emoji_read_name = emoji_name.replace('_', ' ')
        text = re.sub(rf'<:{emoji_name}:\d+>',
                      f'、{emoji_read_name}、', text)

    # Replace URL
    pattern = r'https://tenor.com/view/[\w/:%#\$&\?\(\)~\.=\+\-]+'
    text = re.sub(pattern, '画像', text)
    pattern = r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+(\.jpg|\.jpeg|\.gif|\.png|\.bmp)'
    text = re.sub(pattern, '、画像', text)
    pattern = r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+'
    text = re.sub(pattern, '、ユーアールエル', text)

    # Replace spoiler
    pattern = r'\|{2}.+?\|{2}'
    text = re.sub(pattern, '伏せ字', text)

    # Replace laughing expression
    if text[-1:] == 'w' or text[-1:] == 'W' or text[-1:] == 'ｗ' or text[-1:] == 'W':
        while text[-2:-1] == 'w' or text[-2:-1] == 'W' or text[-2:-1] == 'ｗ' or text[-2:-1] == 'W':
            text = text[:-1]
        text = text[:-1] + '、ワラ'

    # Add attachment presence
    if isinstance(message, discord.Message):
        for attachment in message.attachments:
            if attachment.filename.endswith((".jpg", ".jpeg", ".gif", ".png", ".bmp")):
                text += '、画像'
            else:
                text += '、添付ファイル'

    # Text converting from every lang.
    if detected_lang == "zh":
        text = pinyin.get(text, format="strip", delimiter="")
    elif detected_lang == "ko":
        text = romanise(text, "rr")
    else:
        text = cyrtranslit.to_latin(text, 'ru')
        etk_text = ETK.convert(text)
        a2k_text = jaconv.alphabet2kana(text)
        text = jaconv.alphabet2kana(etk_text.lower())
        #text = romanise(text, "rr")

    text = jaconv.alphabet2kana(text)
    print(" -> ", text, f" (detected langcode: {detected_lang})")
    return text


async def mp3_player(text: str, voice_client: discord.VoiceClient, message: Optional[discord.Message] = None):
    """
    playing a mp3 exported voicevox
    """
    mp3url = f'https://api.su-shiki.com/v2/voicevox/audio/?text={text}&key={voicevox_key}&speaker={voicevox_speaker}&intonationScale=1'
    while voice_client.is_playing():
        await asyncio.sleep(0.5)
    try:
        voice_client.play(discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(mp3url), volume=0.75))
    except OSError as e:
        print("audio playing stopped cuz fatal error occurred:", e)
        if message:
            await message.reply(f"エラーが発生したので再生をストップしました、ごめんなさい！ ><\n```\n{e.strerror}\n```")


@client.event
async def on_message(message: discord.Message):
    if message.guild.voice_client:
        if not message.author.bot:
            if not message.content.startswith(prefix) and message.author.guild.voice_client:
                author = None
                if message.guild.id not in pastauthor.keys() or pastauthor[message.guild.id] == message.author:
                    pastauthor[message.guild.id] = message.author
                    author = message.author

                text = message.content
                text = text_converter(text, message, author)
                await mp3_player(text, message.guild.voice_client)
    await client.process_commands(message)


@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if before.channel is None:
        if member.id == client.user.id:
            presence = f'{prefix}ヘルプ | {len(client.voice_clients)}/{len(client.guilds)}サーバー'
            await client.change_presence(activity=discord.Game(name=presence))
        else:
            if member.guild.voice_client is None:
                await asyncio.sleep(0.5)
                await after.channel.connect()
            else:
                if member.guild.voice_client.channel is after.channel:
                    text = member.display_name + 'さんが入室しました'
                    text = text_converter(text)
                    await mp3_player(text, member.guild.voice_client)
    elif after.channel is None:
        if member.id == client.user.id:
            presence = f'{prefix}ヘルプ | {len(client.voice_clients)}/{len(client.guilds)}サーバー'
            await client.change_presence(activity=discord.Game(name=presence))
        else:
            if member.guild.voice_client:
                if member.guild.voice_client.channel is before.channel:
                    if len(member.guild.voice_client.channel.members) == 1:
                        await asyncio.sleep(0.5)
                        await member.guild.voice_client.disconnect()
                    else:
                        text = member.display_name + 'さんが退室しました'
                        text = text_converter(text)
                        await mp3_player(text, member.guild.voice_client)
    elif before.channel != after.channel:
        if member.guild.voice_client:
            if member.guild.voice_client.channel is before.channel:
                if len(member.guild.voice_client.channel.members) == 1 or member.voice.self_mute:
                    await asyncio.sleep(0.5)
                    await member.guild.voice_client.disconnect()
                    await asyncio.sleep(0.5)
                    await after.channel.connect()


@client.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    orig_error = getattr(error, 'original', error)
    error_msg = ''.join(
        traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)


@client.command(alias=["help", "h"])
async def ヘルプ(ctx: commands.Context):
    message = f'''◆◇◆{client.user.name}の使い方◆◇◆
{prefix}＋コマンドで命令できます。
{prefix}接続：ボイスチャンネルに接続します。
{prefix}切断：ボイスチャンネルから切断します。'''
    await ctx.send(message)

if __name__ == "__main__":
    client.run(token)
