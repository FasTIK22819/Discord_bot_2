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

load_dotenv()
# назначение префикса для команд
client = commands.Bot(command_prefix='!', intents=discord.Intents.all())
players = {}
spisok_mus = []


# with open('musics.csv', mode='w', encoding='utf-8') as m_file:
#     names = ["название", "ссылка"]
#     file_writer = csv.DictWriter(m_file, delimiter=",",
#                                  lineterminator="\r", fieldnames=names)
#     file_writer.writeheader()


# Проверка коммита
# проверка готовности бота к работе
@client.event
async def on_ready():
    print(f'Бот {client.user.name} готов пахать!')


# команда присоединение бота к голосовому каналу
@client.command()
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
        count = 0
        # проверка плейлиста
        with open('musics.csv', mode='r', encoding='utf-8') as m_file:
            file_reader = csv.reader(m_file)
            i = 0
            for row in file_reader:
                i += 1
                if url == row[-1]:
                    await ctx.send(f"Этот трек есть в листе, название - {row[0]}")
                    const.line = i
                    count += 1
                if url == row[0]:
                    url = row[-1]
                    const.line = i
        try:
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception:
            await ctx.send('Ошибка! Нет такого имени')
        name = info['title']

        # добавление трека в плейлист
        if name_title and count == 0:
            a = 0
            with open('musics.csv', mode='r', encoding='utf-8') as m_file:
                file_reader = csv.reader(m_file)
                for row in file_reader:
                    if row == ["название", "ссылка"]:
                        pass
                    else:
                        if name_title in row:
                            if name_title == row[0]:
                                await ctx.send("Это название уже используется, придумайте другое")
                                a += 1
                                break
                        else:
                            if a == 0:
                                with open('musics.csv', mode='a', encoding='utf-8') as m_file:
                                    names = ["название", "ссылка"]
                                    file_writer = csv.DictWriter(m_file, delimiter=",", lineterminator="\r",
                                                                 fieldnames=names)
                                    file_writer.writerow({"название": name_title, "ссылка": url})
                                    a += 1
                                    break

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
async def forward(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    with open('musics.csv', mode='r', encoding='utf-8') as m_file:
        file_reader = csv.reader(m_file)

        line_next = const.line + 1
        if line_next > const.len_sp:
            line_next = 2
        count = 0
        for row in file_reader:
            count += 1
            if count == line_next:
                row_new = row
                break
        url = row_new[0]
        await play(const.ctx_p, url)


# команда предыдущая песня
@client.command()
async def back(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    with open('musics.csv', mode='r', encoding='utf-8') as m_file:
        file_reader = csv.reader(m_file)

        line_next = const.line - 1
        if line_next <= 1:
            line_next = const.len_sp
        count = 0
        for row in file_reader:
            count += 1
            if count == line_next:
                row_new = row
                break
        url = row_new[0]
        await play(const.ctx_p, url)


# команда показать плейлист
@client.command()
async def playlist(ctx):
    m = []
    with open('musics.csv', mode='r', encoding='utf-8') as m_file:
        file_reader = csv.reader(m_file)
        for row in file_reader:
            m.append(' '.join(row))
    embed = disnake.Embed(title='🎶',
                          color=0x228b22)
    embed.add_field(name="плейлист", value='\n'.join(m))
    await ctx.send(embed=embed)


# команда вызова меню
@client.command()
async def menu(ctx):
    await ctx.send(view=MyView_menu(ctx))


# команда для возобновления голосовой связи, если она была приостановлена
@client.command()
async def resume(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)

    if not voice.is_playing():
        voice.resume()
        await ctx.send('Бот готов продолжить пахать')


# команда для возобновления звука, если он был приостановлен
@client.command()
async def pause(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)

    if voice.is_playing():
        voice.pause()
        await ctx.send('Бот отдыхает 🔈')


# команда для остановки звука
@client.command()
async def stop(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.stop()
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
    with open('musics.csv', mode='r', encoding='utf-8') as m_file:
        file_reader = csv.reader(m_file)

        line_next = const.line + 1
        if line_next > const.len_sp:
            line_next = 2
        count = 0
        for row in file_reader:
            count += 1
            if count == line_next:
                row_new = row
                break
        url = row_new[0]
        await play(const.ctx_p, url)


# предыдущая песня
async def back_from_button(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    with open('musics.csv', mode='r', encoding='utf-8') as m_file:
        file_reader = csv.reader(m_file)

        line_next = const.line - 1
        if line_next <= 1:
            line_next = const.len_sp
        count = 0
        for row in file_reader:
            count += 1
            if count == line_next:
                row_new = row
                break
        url = row_new[0]
        await play(const.ctx_p, url)


# показать плейлист
async def playlist_from_button(ctx):
    m = []
    with open('musics.csv', mode='r', encoding='utf-8') as m_file:
        file_reader = csv.reader(m_file)
        for row in file_reader:
            m.append(' '.join(row))
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
    with open('musics.csv', mode='r', encoding='utf-8') as m_file:
        file_reader = csv.reader(m_file)
        for row in file_reader:
            if row == ["название", "ссылка"]:
                pass
            else:
                url = row[0]
                break
    await play(ctx, url)


# ----------------------------------------------------------------------------------------------------------------------


# команда для очистки сообщений канала
@client.command()
async def clear(ctx, amount):
    await ctx.channel.purge(limit=int(amount))
    await ctx.send(f"Очистка мусора завершена (удалено {amount} последних сообщений)")


client.run(TOKEN)
