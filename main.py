import discord
from dotenv import load_dotenv
from discord.ext import commands
from discord.utils import get
from youtube_dl import YoutubeDL
from config import TOKEN
from flask import Flask
import disnake
from data import db_session, const
from data.user import User
import asyncio

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
user = User()


def main():
    db_session.global_init("db/music.db")
    app.run()


def test_orm_user():
    db_session.global_init("db/music.db")
    from data.user import User
    db_sess = db_session.create_session()
    musics = db_sess.query(User).all()
    spisok_mus = []
    for music in musics:
        spisok_mus.append([str(music).split()[1], str(music).split()[2]])


if __name__ == '__main__':
    test_orm_user()

load_dotenv()
# назначение префикса для команд
client = commands.Bot(command_prefix='!', intents=discord.Intents.all())
players = {}


# Проверка коммита
# проверка готовности бота к работе
@client.event
async def on_ready():
    print(f'Бот {client.user.name} готов пахать!')


# команда присоединение бота к голосовому каналу
@client.command()
@commands.has_role("король обезьян")
async def join(ctx):
    try:
        channel = ctx.message.author.voice.channel
    except Exception:
        await ctx.send('Бот поет только в пещере(зайдите в голосовой канал и добавь туда бота (join)')
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
        embed = discord.Embed(
            title="",
            color=0xe100ff,
            description=f"вход")
        embed.set_thumbnail(
            url=f'https://cdna.artstation.com/p/assets/images/images/008/710/076/original/gabriel-casamasso-turntable.gif?1514763325')
        embed.set_footer(text=f"Команду запросил {ctx.author.name}")
        await ctx.send(embed=embed)
    else:
        voice = await channel.connect()
        embed = discord.Embed(
            title="",
            color=0xe100ff,
            description=f"вход")
        embed.set_thumbnail(
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

    # проверка на вход в голосовой канал
    voice = get(client.voice_clients, guild=ctx.guild)
    try:
        channel = ctx.message.author.voice.channel
    except Exception:
        await ctx.send('Бот поет только в пещере(зайдите в голосовой канал и добавь туда бота (join)')
    # воспроизведение музыки
    if not voice.is_playing():
        db_sess = db_session.create_session()
        musics = db_sess.query(User).all()
        spisok_mus = []
        spisok_title = []
        spisok_url = []
        for music in musics:
            spisok_mus.append([str(music).split()[1], str(music).split()[2]])
            spisok_title.append(str(music).split()[1])
            spisok_url.append(str(music).split()[2])
        for title in spisok_mus:
            if url == title[0]:
                url = title[1]
                const.play_mus = title[0]
                break
        loop = asyncio.get_event_loop()
        try:
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
        except Exception:
            await ctx.send('Ошибка! Нет такого имени')
        name = info['title']
        # добавление в плейлист
        if name_title:
            if name_title not in spisok_title:
                if url not in spisok_url:
                    add = User(name=name_title, url=url)
                    db_sess.add(add)
                    db_sess.commit()
                    await ctx.send(f'Успешно добавлен трек: {url} под названием {name_title}')
                else:
                    await ctx.send(f'Этот трек уже добавлен')
            else:
                await ctx.send(f'Это название уже используется')
        URL = info['url']
        player = discord.FFmpegOpusAudio(URL, executable="ffmpeg/ffmpeg.exe", **FFMPEG_OPTIONS)
        voice.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), client.loop))
        # информация кто использовал команду
        embed = disnake.Embed(title='диджей', description=f"музыка {name}",
                              color=0x228b22)
        embed.set_thumbnail(
            url=f'https://i.pinimg.com/originals/82/83/c7/8283c7b7b68f765e2b3bf46fe9c3682f.gif')
        embed.add_field(name="Включил:", value=f"@{ctx.author.name}")
        await ctx.send(embed=embed)
        await ctx.send(f'ОНО РАБОТАЕТ!!! 🔊 (играет - {url}) 🎵', view=MyView(ctx))
    else:
        await ctx.send("Бот уже играет другую музыку")
        return


# создание очереди из плейлиста
db_sess = db_session.create_session()
musics = db_sess.query(User).all()
queues = []
for music in musics:
    queues.append(str(music).split()[2])


# функция воспроизведения музыки из очереди
async def play_next(ctx, i=None):
    url = ''
    if queues:
        if i:
            i = i
        else:
            i = 0
        if i < len(queues):
            url = queues[i]
        else:
            url = queues[0]
        await play(ctx, url=url)


# команда добавить трек в плейлист не проигрывая его
@client.command()
@commands.has_role("король обезьян")
async def add(ctx, url, name_title=None):
    db_sess = db_session.create_session()
    musics = db_sess.query(User).all()
    spisok_mus = []
    spisok_title = []
    spisok_url = []
    for music in musics:
        spisok_mus.append([str(music).split()[1], str(music).split()[2]])
        spisok_title.append(str(music).split()[1])
        spisok_url.append(str(music).split()[2])
    for title in spisok_mus:
        if url == title[0]:
            url = title[1]
            const.play_mus = title[0]
            break
    if name_title:
        if name_title not in spisok_title:
            if url not in spisok_url:
                add = User(name=name_title, url=url)
                db_sess.add(add)
                db_sess.commit()
                await ctx.send(f'Успешно добавлен трек: {url} под названием {name_title}')
            else:
                await ctx.send(f'Этот трек уже добавлен')
        else:
            await ctx.send(f'Это название уже используется')
    else:
        await ctx.send('Нет имени')


# команда перемещения музыки по имени
@client.command()
@commands.has_role("король обезьян")
async def replace(ctx, name_new_1, name_new_2):
    db_sess = db_session.create_session()
    string_first = db_sess.query(User).filter(User.name == name_new_1).first()
    string_second = db_sess.query(User).filter(User.name == name_new_2).first()
    string_first.name = name_new_2
    string_second.name = name_new_1
    string_first.url, string_second.url = string_second.url, string_first.url
    db_sess.commit()
    await ctx.send('Success!')


# команда перемещения музыки по номеру
@client.command()
@commands.has_role("король обезьян")
async def id_replace(ctx, name_title, id):
    db_sess = db_session.create_session()
    string_first = db_sess.query(User).filter(User.name == name_title).first()
    string_second = db_sess.query(User).filter(User.id == id).first()
    string_first.name = string_second.name
    string_second.name = name_title
    string_first.url, string_second.url = string_second.url, string_first.url
    db_sess.commit()
    await ctx.send('Success!')


# команда пропуск песни
@client.command()
@commands.has_role("король обезьян")
async def forward(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    await voice.disconnect()

    url = ''
    await ctx.channel.purge(limit=3)
    db_sess = db_session.create_session()
    musics = db_sess.query(User).all()
    spisok_mus = []
    for music in musics:
        spisok_mus.append([str(music).split()[1], str(music).split()[2]])
    for i in range(len(spisok_mus)):
        if spisok_mus[i][0] == const.play_mus:
            if i + 1 < len(spisok_mus):
                url = spisok_mus[i + 1][0]
                break
            else:
                url = spisok_mus[0][0]
    await play(ctx, url)


# команда предыдущая песня
@client.command()
@commands.has_role("король обезьян")
async def back(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    url = ''
    await ctx.channel.purge(limit=3)
    db_sess = db_session.create_session()
    musics = db_sess.query(User).all()
    spisok_mus = []
    for music in musics:
        spisok_mus.append([str(music).split()[1], str(music).split()[2]])
    for i in range(len(spisok_mus)):
        if spisok_mus[i][0] == const.play_mus:
            if i > 0:
                url = spisok_mus[i - 1][0]
                break
            else:
                url = spisok_mus[-1][0]
    await play(ctx, url)


# команда показать плейлист
@client.command()
async def playlist(ctx):
    db_sess = db_session.create_session()
    musics = db_sess.query(User).all()
    spisok_mus = []
    for music in musics:
        spisok_mus.append([str(music).split()[1], str(music).split()[2]])
    m = []
    for mus in spisok_mus:
        mus = ' '.join(mus)
        m.append(mus)
    embed = disnake.Embed(title='🎶',
                          color=0x228b22)
    embed.add_field(name="плейлист", value='\n'.join(m))
    await ctx.send(embed=embed)


# команда удаления трека из плейлиста
@client.command()
@commands.has_role("король обезьян")
async def delete(ctx, title):
    try:
        db_sess = db_session.create_session()
        musics = db_sess.query(User).all()
        spisok_mus = []
        for music in musics:
            if title == str(music).split()[1]:
                spisok_mus.append(str(music).split()[1])
                db_sess.query(User).filter(User.name == title).delete()
                db_sess.commit()
        await ctx.send(f'Трек {spisok_mus[0]} под названием "{title}" был успешно удален.')
    except Exception:
        await ctx.send('НЕ УДАЛОСЬ УДАЛИТЬ. Проверьте правильно ли написано название и есть ли оно в плейлисте')
        await playlist(ctx)


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
        await ctx.channel.purge(limit=1)
        await ctx.send('Бот готов продолжить пахать', delete_after=5)


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
        del voice
        await ctx.channel.purge(limit=2)
        await ctx.send(f'Музыка OF 🔇')
        embed = disnake.Embed(title='диджей',
                              color=0x228b22)
        embed.set_thumbnail(
            url=f'https://yt3.googleusercontent.com/lc-EyUTVJPzpCUzuQwmLj'
                f'TM6itlMZ0-jhzXDFwA4bcBo8U6vbC58YsSUV1wY1l4HNZsNqHUEwQ=s900-c-k-c0x00ffffff-no-rj')
        embed.add_field(name="Выключил:", value=f"@{ctx.author.name}")
        await ctx.send(embed=embed, delete_after=30)


# команда переименовывания трека
@client.command()
@commands.has_role("король обезьян")
async def rename(ctx, old_name, new_name):
    db_sess = db_session.create_session()
    string_first = db_sess.query(User).filter(User.name == old_name).first()
    string_first.name = new_name
    db_sess.commit()
    await ctx.send('Трек успешно переименован')


# ------функции кнопок--------------------------------------------------------------------------------------------------
# остановка бота
async def stop_from_button(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.stop()
        await voice.disconnect()
        del voice
        await ctx.channel.purge(limit=2)
        await ctx.send(f'Музыка OF 🔇')
        embed = disnake.Embed(title='диджей',
                              color=0x228b22)
        embed.set_thumbnail(
            url=f'https://yt3.googleusercontent.com/lc-EyUTVJPzpCUzuQwmLj'
                f'TM6itlMZ0-jhzXDFwA4bcBo8U6vbC58YsSUV1wY1l4HNZsNqHUEwQ=s900-c-k-c0x00ffffff-no-rj')
        embed.add_field(name="Выключил:", value=f"@{ctx.author.name}")
        await ctx.send(embed=embed, delete_after=30)


# пропуск песни
async def forward_from_button(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    await voice.disconnect()
    try:
        channel = ctx.message.author.voice.channel
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
    except Exception:
        await ctx.send('Бот поет только в пещере(зайдите в голосовой канал)')
    url = ''
    await ctx.channel.purge(limit=2)
    db_sess = db_session.create_session()
    musics = db_sess.query(User).all()
    spisok_mus = []
    for music in musics:
        spisok_mus.append([str(music).split()[1], str(music).split()[2]])
    for i in range(len(spisok_mus)):
        if spisok_mus[i][0] == const.play_mus:
            if i + 1 < len(spisok_mus):
                url = spisok_mus[i + 1][0]
                break
            else:
                url = spisok_mus[0][0]
    await play(ctx, url)


# предыдущая песня
async def back_from_button(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    await voice.disconnect()
    try:
        channel = ctx.message.author.voice.channel
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
    except Exception:
        await ctx.send('Бот поет только в пещере(зайдите в голосовой канал)')
    url = ''
    await ctx.channel.purge(limit=2)
    db_sess = db_session.create_session()
    musics = db_sess.query(User).all()
    spisok_mus = []
    for music in musics:
        spisok_mus.append([str(music).split()[1], str(music).split()[2]])
    for i in range(len(spisok_mus)):
        if spisok_mus[i][0] == const.play_mus:
            if i > 0:
                url = spisok_mus[i - 1][0]
                break
            else:
                url = spisok_mus[-1][0]
    await play(ctx, url)


# показать плейлист
async def playlist_from_button(ctx):
    db_sess = db_session.create_session()
    musics = db_sess.query(User).all()
    spisok_mus = []
    for music in musics:
        spisok_mus.append([str(music).split()[1], str(music).split()[2]])
    m = []
    for mus in spisok_mus:
        mus = ' '.join(mus)
        m.append(mus)
    embed = disnake.Embed(title='🎶',
                          color=0x228b22)
    embed.add_field(name="плейлист", value='\n'.join(m))
    await ctx.send(embed=embed)


# пауза
async def pause_from_button(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
        await ctx.send('Бот отдыхает ')


# продолжить
async def resume_from_button(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    if not voice.is_playing():
        voice.resume()
        await ctx.channel.purge(limit=1)
        await ctx.send('Бот готов продолжить пахать', delete_after=5)


# играет 1 песню из плейлиста
async def play_from_button(ctx):
    db_sess = db_session.create_session()
    musics = db_sess.query(User).all()
    spisok_mus = []
    for music in musics:
        spisok_mus.append([str(music).split()[1], str(music).split()[2]])
    url = spisok_mus[0][0]
    await play(ctx, url)


# ----------------------------------------------------------------------------------------------------------------------


# команда для очистки сообщений канала
@client.command()
async def clear(ctx, amount):
    await ctx.channel.purge(limit=int(amount))
    await ctx.send(f"Очистка мусора завершена (удалено {amount} последних сообщений)", delete_after=5)


client.run(TOKEN)
