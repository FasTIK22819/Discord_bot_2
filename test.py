import discord
import os
import csv
from dotenv import load_dotenv
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from discord import TextChannel
from youtube_dl import YoutubeDL
from config import TOKEN
import disnake
import const
import sqlite3

connection = sqlite3.connect('playlist_db')
cursor = connection.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS media (
    names TEXT UNIQUE,
    url   TEXT UNIQUE
)''')
connection.commit()

load_dotenv()
# назначение префикса для команд
client = commands.Bot(command_prefix='!', intents=discord.Intents.all())
players = {}
spisok_mus = []


# Проверка коммита
# проверка готовности бота к работе
@client.event
async def on_ready():
    print(f'Бот {client.user.name} готов пахать!')


# команда присоединение бота к голосовому каналу
@client.command()
@commands.has_role("король обезьян")
async def join(ctx):
    channel = ctx.message.author.voice.channel
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
        embed = discord.Embed(
            title="",
            color=0xe100ff,
            description=f"вход")
        embed.set_image(
            url=f'https://cdna.artstation.com/p/assets/images/images/008/710/076/original/gabriel-casamasso-turntable.gif?1514763325')
        embed.set_footer(text=f"Команду запросил {ctx.author.name}")
        await ctx.send(embed=embed)
    else:
        voice = await channel.connect()
        embed = discord.Embed(
            title="",
            color=0xe100ff,
            description=f"вход")
        embed.set_image(
            url=f'https://cdna.artstation.com/p/assets/images/images/008/710/076/original/gabriel-casamasso-turntable.gif?1514763325')
        embed.set_footer(text=f"Команду запросил {ctx.author.name}")
        await ctx.send(embed=embed)


# команда изгнать бота из голосового канала
@client.command()
async def leave(ctx):
    channel = ctx.message.author.voice.channel
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.disconnect()


# класс кнопок
class MyView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

    # кнопка назад
    @discord.ui.button(label="", row=1, style=discord.ButtonStyle.primary, emoji='⏪')
    async def first_button_callback(self, interaction, button):
        await back_from_button(self.ctx)

    # кнопка стоп
    @discord.ui.button(label="Остановить", row=1, style=discord.ButtonStyle.danger, emoji='⏺️')
    async def stop_button(self, interaction, button):
        await stop_from_button(self.ctx)

    # кнопка паузы
    @discord.ui.button(label="Пауза", row=1, style=discord.ButtonStyle.green, emoji='⏸️')
    async def pause_button(self, interaction, button):
        await pause_from_button(self.ctx)

    # кнопка продолжить
    @discord.ui.button(label="Продолжить", row=1, style=discord.ButtonStyle.green, emoji='▶️')
    async def resume_button(self, interaction, button):
        await resume_from_button(self.ctx)

    # кнопка вперед
    @discord.ui.button(label="", row=1, style=discord.ButtonStyle.blurple, emoji='⏩')
    async def second_button_callback(self, interaction, button):
        await forward_from_button(self.ctx)

    # кнопка плейлист
    @discord.ui.button(label="Плейлист", row=2, style=discord.ButtonStyle.blurple, emoji='🎶')
    async def list_button_callback(self, interaction, button):
        await playlist_from_button(self.ctx)


# меню 2
class MyView_menu(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

    # кнопка плейлист
    @discord.ui.button(label="Плейлист", row=2, style=discord.ButtonStyle.blurple, emoji='🎶')
    async def list_button_callback(self, interaction, button):
        await playlist_from_button(self.ctx)

    # кнопка, при нажатии играет 1-я песня из плейлиста
    @discord.ui.button(label="Плей", row=3, style=discord.ButtonStyle.blurple, emoji='🎧')
    async def play_button_callback(self, interaction, button):
        await play_from_button(self.ctx)


# команда для воспроизведения звука с URL-адреса youtube
@client.command()
@commands.has_role("король обезьян")
async def play(ctx, url, name_title=None):
    const.ctx_p = ctx
    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    voice = get(client.voice_clients, guild=ctx.guild)

    # вход в голосовой канал
    try:
        channel = ctx.message.author.voice.channel
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
    except Exception:
        await ctx.send('Бот поет только в пещере(зайдите в голосовой канал)')

    if not voice.is_playing():
        result = cursor.execute('SELECT names, url FROM media').fetchall()
        for title in result:
            if url == title[0]:
                url = title[1]
                const.play_mus = title[0]
                break
        try:
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception:
            await ctx.send('Ошибка! Нет такого имени')
        name = info['title']
        if name_title:
            cursor.execute(f'SELECT names FROM media WHERE names="{name_title}"')
            if cursor.fetchone() is None:
                cursor.execute(f"INSERT INTO media (names, url) VALUES ('{name_title}', '{url}')")
                connection.commit()

        URL = info['url']
        spisok_mus.append(URL)
        voice.play(discord.FFmpegPCMAudio(URL, executable="ffmpeg/ffmpeg.exe", **FFMPEG_OPTIONS))
        voice.is_playing()
        # информация кто использовал команду
        embed = disnake.Embed(title='диджей', description=f"музыка {name}",
                              color=0x228b22)
        embed.set_image(
            url=f'https://i.pinimg.com/originals/82/83/c7/8283c7b7b68f765e2b3bf46fe9c3682f.gif')
        embed.add_field(name="Включил:", value=f"@{ctx.author.name}")
        await ctx.send(embed=embed)
        await ctx.send(f'ОНО РАБОТАЕТ!!! 🔊 (играет - {url}) 🎵', view=MyView(ctx))
    else:
        await ctx.send("Бот уже играет другую музыку")
        return


# команда пропуск песни
@client.command()
@commands.has_role("король обезьян")
async def forward(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    url = ''
    await ctx.channel.purge(limit=3)
    result = cursor.execute('SELECT names, url FROM media').fetchall()
    for i in range(len(result)):
        if result[i][0] == const.play_mus:
            if i + 1 < len(result):
                url = result[i + 1][0]
                break
            else:
                url = result[0][0]
    await play(ctx, url)


# команда предыдущая песня
@client.command()
@commands.has_role("король обезьян")
async def back(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    url = ''
    await ctx.channel.purge(limit=3)
    result = cursor.execute('SELECT names, url FROM media').fetchall()
    for i in range(len(result)):
        if result[i][0] == const.play_mus:
            if i > 0:
                url = result[i - 1][0]
                break
            else:
                url = result[-1][0]
    await play(ctx, url)


# команда показать плейлист
@client.command()
async def playlist(ctx):
    result = cursor.execute(f'SELECT names, url FROM media').fetchall()
    m = []
    for mus in result:
        mus = ' '.join(mus)
        m.append(mus)
    embed = disnake.Embed(title='🎶',
                          color=0x228b22)
    embed.add_field(name="плейлист", value='\n'.join(m))
    await ctx.send(embed=embed)


@client.command()
@commands.has_role("король обезьян")
async def delete(ctx, title):
    try:
        result = cursor.execute(f'SELECT url FROM media WHERE names="{title}"').fetchall()
        cursor.execute(f'DELETE FROM media WHERE names="{title}"')
        await ctx.send(f'Трек {result[0][0]} под названием "{title}" был успешно удален.')
    except Exception:
        await ctx.send('НЕ УДАЛОСЬ УДАЛИТЬ. Проверьте правильно ли написано название и есть ли оно в плейлисте')
        await playlist(ctx)
    connection.commit()


# команда вызова меню
@client.command()
@commands.has_role("король обезьян")
async def menu(ctx):
    await ctx.send(view=MyView_menu(ctx))


# команда для возобновления голосовой связи, если она была приостановлена
@client.command()
@commands.has_role("король обезьян")
async def resume(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if not voice.is_playing():
        voice.resume()
        await ctx.send('Бот готов продолжить пахать')


# команда для возобновления звука, если он был приостановлен
@client.command()
@commands.has_role("король обезьян")
async def pause(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
        await ctx.send('Бот отдыхает 🔈')


# команда для остановки звука
@client.command()
@commands.has_role("король обезьян")
async def stop(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.stop()
        await ctx.channel.purge(limit=2)
        await ctx.send(f'Музыка OF 🔇')
        embed = disnake.Embed(title='диджей',
                              color=0x228b22)
        embed.add_field(name="Выключил:", value=f"@{ctx.author.name}")
        await ctx.send(embed=embed)


# ------функции кнопок--------------------------------------------------------------------------------------------------
# остановка бота
async def stop_from_button(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.stop()
        await ctx.channel.purge(limit=2)
        await ctx.send(f'Музыка OF 🔇')
        embed = disnake.Embed(title='диджей',
                              color=0x228b22)
        embed.set_image(
            url=f'https://yt3.googleusercontent.com/lc-EyUTVJPzpCUzuQwmLj'
                f'TM6itlMZ0-jhzXDFwA4bcBo8U6vbC58YsSUV1wY1l4HNZsNqHUEwQ=s900-c-k-c0x00ffffff-no-rj')
        embed.add_field(name="Выключил:", value=f"@{ctx.author.name}")
        await ctx.send(embed=embed)


# пропуск песни
async def forward_from_button(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    url = ''
    await ctx.channel.purge(limit=2)
    result = cursor.execute('SELECT names, url FROM media').fetchall()
    for i in range(len(result)):
        if result[i][0] == const.play_mus:
            if i + 1 < len(result):
                url = result[i + 1][0]
                break
            else:
                url = result[0][0]
    await play(ctx, url)


# предыдущая песня
async def back_from_button(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    url = ''
    await ctx.channel.purge(limit=2)
    result = cursor.execute('SELECT names, url FROM media').fetchall()
    for i in range(len(result)):
        if result[i][0] == const.play_mus:
            if i > 0:
                url = result[i - 1][0]
                break
            else:
                url = result[-1][0]
    await play(ctx, url)


# показать плейлист
async def playlist_from_button(ctx):
    result = cursor.execute(f'SELECT names, url FROM media').fetchall()
    m = []
    for mus in result:
        mus = ' '.join(mus)
        m.append(mus)
    embed = disnake.Embed(title='🎶',
                          color=0x228b22)
    embed.add_field(name="плейлист", value='\n'.join(m))
    await ctx.send(embed=embed)


async def pause_from_button(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
        await ctx.send('Бот отдыхает ')


async def resume_from_button(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if not voice.is_playing():
        voice.resume()
        await ctx.send('Бот готов продолжить пахать')


# играет 1 песню из плелиста
async def play_from_button(ctx):
    url = ''
    result = cursor.execute(f'SELECT names, url FROM media').fetchall()
    url = result[0][0]
    await play(ctx, url)


# ----------------------------------------------------------------------------------------------------------------------


# команда для очистки сообщений канала
@client.command()
async def clear(ctx, amount):
    await ctx.channel.purge(limit=int(amount))
    await ctx.send(f"Очистка мусора завершена (удалено {amount} последних сообщений)")


client.run(TOKEN)
