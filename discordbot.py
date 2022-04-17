import asyncio
from typing import Optional
import aiohttp
import discord
from discord.ext import commands
import os
import traceback
import re
import emoji
import json
import jaconv
from english_to_kana import EnglishToKana

DEBUG = False

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


client = commands.Bot(command_prefix=prefix)
with open('emoji_ja.json', encoding='utf-8') as file:
    emoji_dataset = json.load(file)

ETK = EnglishToKana()


@client.event
async def on_ready():
    print('Logged in as ' + client.user.name)
    presence = f'{prefix}ヘルプ | 0/{len(client.guilds)}サーバー'
    await client.change_presence(activity=discord.Game(name=presence))


@client.event
async def on_guild_join(guild):
    presence = f'{prefix}ヘルプ | {len(client.voice_clients)}/{len(client.guilds)}サーバー'
    await client.change_presence(activity=discord.Game(name=presence))


@client.event
async def on_guild_remove(guild):
    presence = f'{prefix}ヘルプ | {len(client.voice_clients)}/{len(client.guilds)}サーバー'
    await client.change_presence(activity=discord.Game(name=presence))


@client.command(alias=["connect", "con"])
async def 接続(ctx):
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
async def 切断(ctx):
    if ctx.message.guild:
        if ctx.voice_client is None:
            await ctx.send('ボイスチャンネルに接続していません。')
        else:
            await ctx.voice_client.disconnect()


def text_converter(text: str, message: Optional[discord.Message] = None) -> str:
    """
    docstring
    """
    print("got text:", text, end="")

    text = text.replace('\n', '、')
    if isinstance(message,discord.Message):
        # Add author's name
        text = message.author.display_name + '、' + text

        # Replace new line

        # Replace mention to user
        user_mentions = message.mentions
        for um in user_mentions:
            text = text.replace(
                um.mention, f"、{um.display_name}さんへのメンション")

        # Replace mention to role
        role_mentions = message.role_mentions
        for rm in role_mentions:
            text = text.replace(
                rm.mention, f"、{rm.name}へのメンション")

    # Replace Unicode emoji
    text = re.sub(r'[\U0000FE00-\U0000FE0F]', '', text)
    text = re.sub(r'[\U0001F3FB-\U0001F3FF]', '', text)
    for char in text:
        if char in emoji.UNICODE_EMOJI['en'] and char in emoji_dataset:
            text = text.replace(
                char, emoji_dataset[char]['short_name'])

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
    text = re.sub(pattern, '、URL', text)

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

    etk_text = ETK.convert(text)
    a2k_text = jaconv.alphabet2kana(text)
    text = jaconv.alphabet2kana(etk_text.lower())
    print(" -> ", text, f" (ETK:{etk_text}, A2K:{a2k_text})")
    return text


async def mp3_player(text: str, voice_client: discord.VoiceClient, message: Optional[discord.Message] = None):
    """
    docstring
    """
    mp3url = f'https://api.su-shiki.com/v2/voicevox/audio/?text={text}&key={voicevox_key}&speaker={voicevox_speaker}&intonationScale=1'
    while voice_client.is_playing():
        await asyncio.sleep(0.5)
    try:
        voice_client.play(discord.FFmpegPCMAudio(mp3url))
    except OSError as e:
        print("audio playing stopped cuz fatal error occurred:", e)
        if message:
            await message.reply(f"エラーが発生したので再生をストップしました、ごめんなさい！ ><\n```\n{e.strerror}\n```")


@client.event
async def on_message(message):
    if message.guild.voice_client:
        if not message.author.bot:
            if not message.content.startswith(prefix) and message.author.guild.voice_client:
                text = message.content
                text = text_converter(text, message)
                # download_path = f'tmp'
                # if not os.path.exists(download_path):
                #     os.makedirs(download_path, exist_ok=True)
                # mp3_path = f'{download_path}/{message.id}.mp3'
                # if not os.path.exists(mp3_path):
                #     print("Downloading...")
                #     try:
                #         async with aiohttp.ClientSession() as session:
                #             async with session.get(mp3url) as resp:
                #                 if resp.status == 200:
                #                     with open(mp3_path, 'wb') as f:
                #                         f.write(await resp.read())
                #                     print("Downloaded.")
                #                 else:
                #                     print("Download failed.")
                #     except Exception as e:
                #         print("Download failed cuz something error happend;", e)
                # else:
                #     print("Already downloaded.")
                # if os.path.exists(mp3_path):
                #     while message.guild.voice_client.is_playing():
                #         await asyncio.sleep(0.5)
                #     message.guild.voice_client.play(
                #         discord.FFmpegPCMAudio(mp3_path))
                #     os.remove(mp3_path)
                # else:
                #     await message.reply("音声のダウンロードをミスっちゃいました、ごめんなさい！")
                await mp3_player(text, message.guild.voice_client, message)
    await client.process_commands(message)


@client.event
async def on_voice_state_update(member, before, after):
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
async def on_command_error(ctx, error):
    orig_error = getattr(error, 'original', error)
    error_msg = ''.join(
        traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)


@client.command(alias=["help", "h"])
async def ヘルプ(ctx):
    message = f'''◆◇◆{client.user.name}の使い方◆◇◆
{prefix}＋コマンドで命令できます。
{prefix}接続：ボイスチャンネルに接続します。
{prefix}切断：ボイスチャンネルから切断します。'''
    await ctx.send(message)

if __name__ == "__main__":
    client.run(token)
