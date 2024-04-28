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

load_dotenv()
# назначение префикса для команд
client = commands.Bot(command_prefix='!', intents=discord.Intents.all())
players = {}


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


class MyView(discord.ui.View):
    @discord.ui.button(label="<< камень", row=1, style=discord.ButtonStyle.primary)
    async def first_button_callback(self, interaction, button):
        await interaction.response.send_message("You pressed me!")

    @discord.ui.button(label="Остановить охоту на мамонтов", row=1, style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction, button):
        await interaction.response.send_message("You stoped me!")
        print(interaction)
        await stop()

    @discord.ui.button(label="кость >>", row=1, style=discord.ButtonStyle.blurple)
    async def second_button_callback(self, interaction, button):
        await interaction.response.send_message("You pressed me!")


# команда для воспроизведения звука с URL-адреса youtube
@client.command()
async def play(ctx, url, name_title=None):
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

    if not voice.is_playing():
        count = 0
        # проверка плейлиста
        with open('musics.csv', mode='r', encoding='utf-8') as m_file:
            file_reader = csv.reader(m_file)
            for row in file_reader:
                if row == ["название", "ссылка"]:
                    pass
                else:
                    if url == row[-1]:
                        await ctx.send(f"Этот трек есть в листе, название - {row[0]}")
                        count += 1
                    if url == row[0]:
                        url = row[-1]
        try:
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception:
            await ctx.send("Ошибка! Такого названия нет в списке")

        name = info['title']
        name = ''.join(name.split())

        # добавление трека в в плейлист
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
        voice.play(discord.FFmpegPCMAudio(URL, executable="ffmpeg/ffmpeg.exe", **FFMPEG_OPTIONS))
        voice.is_playing()
        await ctx.send('ОНО РАБОТАЕТ!!! 0_0', view=MyView())
    # бот уже играет музыку
    else:
        await ctx.send("Бот уже играет другую музыку")
        return


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


# команда для остановки звука
@client.command()
async def stop(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.stop()
        await ctx.send(f'Музыка OF')
        print(ctx)


# команда для очистки сообщений канала
@client.command()
async def clear(ctx, amount):
    await ctx.channel.purge(limit=int(amount))
    await ctx.send(f"Очистка мусора завершена (удалено {amount} последних сообщений)")


client.run(TOKEN)
