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
    else:
        voice = await channel.connect()


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

    @discord.ui.button(label="<<", row=1, style=discord.ButtonStyle.primary)
    async def first_button_callback(self, interaction, button):
        await back_from_button(self.ctx)

    @discord.ui.button(label="Остановить", row=1, style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction, button):
        await stop_from_button(self.ctx)

    @discord.ui.button(label=">>", row=1, style=discord.ButtonStyle.blurple)
    async def second_button_callback(self, interaction, button):
        await forward_from_button(self.ctx)


# команда для воспроизведения звука с URL-адреса youtube
@client.command()
async def play(ctx, url, name_title=None):
    const.ctx_p = ctx
    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    voice = get(client.voice_clients, guild=ctx.guild)

    # вход в голосовой канал
    channel = ctx.message.author.voice.channel
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()

    count = 0
    # проверка плейлиста
    with open('musics.csv', mode='r', encoding='utf-8') as m_file:
        file_reader = csv.reader(m_file)
        i = 0
        for row in file_reader:
            i += 1
            if url == row[-1]:
                await ctx.send(f"Этот трек есть в листе, название - {row[0]}")
                line = i
                count += 1
            if url == row[0]:
                url = row[-1]
                line = i
    const.line = line
    try:
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception:
        await ctx.send('Ошибка! Нет такого имени')
    name = info['title']
    name = ''.join(name.split())

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
                    else:
                        if a == 0:
                            with open('musics.csv', mode='a', encoding='utf-8') as m_file:
                                names = ["название", "ссылка"]
                                file_writer = csv.DictWriter(m_file, delimiter=",", lineterminator="\r",
                                                             fieldnames=names)
                                file_writer.writerow({"название": name_title, "ссылка": url})
                                a += 1

    URL = info['url']
    spisok_mus.append(URL)
    while True:
        for el in spisok_mus:
            voice.play(discord.FFmpegPCMAudio(el, executable="ffmpeg/ffmpeg.exe", **FFMPEG_OPTIONS))
            voice.is_playing()
        await ctx.send(f'ОНО РАБОТАЕТ!!! 0_0 (играет - {url})', view=MyView(ctx))
        return


# Пропуск песни
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


# Предыдущая песня
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
        await ctx.send('\n'.join(m))


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
        await ctx.send('Бот отдыхает')


# Остановка бота
async def stop_from_button(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.stop()
        await ctx.send(f'Музыка OF...')


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


# команда для остановки звука
@client.command()
async def stop(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.stop()
        await ctx.send(f'Музыка OF')


# команда для очистки сообщений канала
@client.command()
async def clear(ctx, amount):
    await ctx.channel.purge(limit=int(amount))
    await ctx.send(f"Очистка мусора завершена (удалено {amount} последних сообщений)")


client.run(TOKEN)
