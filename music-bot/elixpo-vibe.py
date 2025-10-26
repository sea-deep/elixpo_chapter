import os
import discord
from discord.ext import commands
from discord import Embed, FFmpegPCMAudio, Interaction, ButtonStyle
from discord.ui import View, Button
from dotenv import load_dotenv
import yt_dlp

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TOKEN')

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Global variables for tracking playback state
current_voice_client = None
current_song_info = {}
is_looping = False
song_queue = []  # Queue to manage songs

# Helper function to download song URL
async def get_audio_url(song_name):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{song_name}", download=False)
        song_info = info['entries'][0]  # Take the first result
        return song_info['url'], song_info['title'], song_info['duration'], song_info['thumbnail']

async def play_next_song(interaction):
    global is_looping, current_song_info, song_queue

    if is_looping and current_song_info:
        # Replay the current song if looping
        audio_source = FFmpegPCMAudio(current_song_info['audio_url'])
        current_voice_client.play(audio_source, after=lambda e: bot.loop.create_task(play_next_song(interaction)))
    elif song_queue:
        # Play the next song if looping is disabled and queue is not empty
        next_song = song_queue.pop(0)
        audio_url, title, duration, thumbnail_url = next_song
        current_song_info = {
            'title': title,
            'duration': duration,
            'requested_by': interaction.user.display_name,
            'audio_url': audio_url
        }
        audio_source = FFmpegPCMAudio(audio_url)
        current_voice_client.play(audio_source, after=lambda e: bot.loop.create_task(play_next_song(interaction)))

        # Send updated Now Playing message
        embed = Embed(
            title="Now Playing",
            description=f"**{title}**",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=thumbnail_url)
        embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.avatar.url)
        embed.add_field(name="Volume", value="100%", inline=True)
        embed.add_field(name="Uptime", value="24/7", inline=True)
        await interaction.followup.send(embed=embed, view=MusicControlView())
    else:
        # Stop playback if queue is empty and looping is disabled
        current_song_info = None


class CustomAudioSource(discord.PCMVolumeTransformer):
    def __init__(self, source, volume=1.0):
        super().__init__(source, volume)

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = value
        self.source.volume = value  # Adjust volume in the underlying source

    def set_volume(self, volume):
        self.volume = volume


# Create a view for music control buttons
class MusicControlView(View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="⏸️ Pause", style=ButtonStyle.primary)
    async def pause_button(self, interaction: Interaction, button: Button):
        global current_voice_client
        if current_voice_client and current_voice_client.is_playing():
            current_voice_client.pause()
            button.label = "▶️ Play"  # Change button label to indicate it can be resumed
            await interaction.response.edit_message(content=f"Paused the music. Paused by {interaction.user.mention}.", view=self)
        elif current_voice_client and current_voice_client.is_paused():
            current_voice_client.resume()
            button.label = "⏸️ Pause"  # Change button label back to pause
            await interaction.response.edit_message(content=f"Resumed the music. Resumed by {interaction.user.mention}", view=self)
        else:
            await interaction.response.send_message("No music is currently playing.", ephemeral=True)

    @discord.ui.button(label="⏹️ Stop", style=ButtonStyle.danger)
    async def stop_button(self, interaction: Interaction, button: Button):
        global current_voice_client, song_queue, is_looping
        if current_voice_client and current_voice_client.is_playing():
            is_looping = False
            loop_button = next((b for b in self.children if isinstance(b, discord.ui.Button) and b.label.startswith("🔁")), None)
            if loop_button:
                loop_button.label = "🔁 Loop" 
            current_voice_client.stop()
            song_queue.clear()  # Clear the queue when stopped
            await interaction.response.send_message(f"Stopped the music and cleared the queue. Stopped by {interaction.user.mention}", ephemeral=False)
        else:
            await interaction.response.send_message("No music is currently playing.", ephemeral=True)

    @discord.ui.button(label="⏭️ Skip", style=ButtonStyle.secondary)
    async def skip_button(self, interaction: Interaction, button: Button):
        global current_voice_client, is_looping
        if current_voice_client:
            is_looping = False
            loop_button = next((b for b in self.children if isinstance(b, discord.ui.Button) and b.label.startswith("🔁")), None)
            if loop_button:
                loop_button.label = "🔁 Loop" 
            current_voice_client.stop() 
            await interaction.response.send_message(f"Skipped to the next song and Looping is now Disabled. Skipped by {interaction.user.mention}.", ephemeral=False)
        else:
            await interaction.response.send_message("No music is currently playing to skip.", ephemeral=True)

    @discord.ui.button(label="📃 Queue", style=ButtonStyle.secondary)
    async def queue_button(self, interaction: Interaction, button: Button):
        global song_queue, current_song_info
        if not song_queue:
            await interaction.response.send_message("The Queue is Empty! 🔎", ephemeral=True)
        else:
            queue_list = [f"{i+1}. **{song[1]}**" for i, song in enumerate(song_queue)]
            queue_message = "\n".join(queue_list)
            now_playing = f"**Now Playing:** {current_song_info['title']}" if current_song_info else ""
            full_message = queue_message + queue_message
            Embed = discord.Embed( 
                title="Queue",
                description=full_message,
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=Embed, ephemeral=False)

    @discord.ui.button(label="🔌 Disconnect", style=ButtonStyle.danger)
    async def disconnect_button(self, interaction: Interaction, button: Button):
        global current_voice_client
        if current_voice_client and current_voice_client.is_connected():
            await current_voice_client.disconnect()
            current_voice_client = None
            await interaction.response.send_message(f"Disconnected by {interaction.user.mention}.", ephemeral=False)
        else:
            await interaction.response.send_message("The bot is not connected to any voice channel.", ephemeral=True)


    @discord.ui.button(label="🔁 Loop", style=ButtonStyle.secondary)
    async def loop_button(self, interaction: Interaction, button: Button):
        global is_looping
        is_looping = not is_looping
        if is_looping:
            button.label = "🔁 Looping"
            await interaction.response.edit_message(content=f"Looping is now enabled. Triggered by {interaction.user.mention}", view=self)
            await interaction.response.send_message("Looping is now enabled.", ephemeral=True)
        else:
            button.label = "🔁 Loop"
            await interaction.response.edit_message(content=f"Looping is now disabled. Triggered by {interaction.user.mention}", view=self)
            await interaction.response.send_message("Looping is now disabled.", ephemeral=True)

    @discord.ui.button(label="🔉 Volume Down", style=ButtonStyle.secondary)
    async def volume_down_button(self, interaction: Interaction, button: Button):
        global current_voice_client
        if current_voice_client and current_voice_client.source:
            # Check if the source is a CustomAudioSource
            if isinstance(current_voice_client.source, CustomAudioSource):
                current_volume = current_voice_client.source.volume
                new_volume = max(current_volume - 0.1, 0.0)  # Decrease volume by 10%, min 0
                current_voice_client.source.set_volume(new_volume)  # Use custom method to set volume

                # Update the button's state if the volume is at minimum
                if new_volume == 0.0:
                    button.disabled = True  # Disable the button if volume is at minimum
                    await interaction.response.edit_message(view=self)  # Update the view
                else:
                    await interaction.response.send_message(f"Volume decreased to {int(new_volume * 100)}%.", ephemeral=True)
            else:
                await interaction.response.send_message("The current audio source does not support volume control.", ephemeral=True)
        else:
            await interaction.response.send_message("No music is currently playing.", ephemeral=True)

    @discord.ui.button(label="🔊 Volume Up", style=ButtonStyle.secondary)
    async def volume_up_button(self, interaction: Interaction, button: Button):
        global current_voice_client
        if current_voice_client and current_voice_client.source:
            # Check if the source is a CustomAudioSource
            if isinstance(current_voice_client.source, CustomAudioSource):
                current_volume = current_voice_client.source.volume
                new_volume = min(current_volume + 0.1, 1.0)  # Increase volume by 10%, max 100%
                current_voice_client.source.set_volume(new_volume)  # Use custom method to set volume

                # Update the button's state if the volume is at maximum
                if new_volume == 1.0:
                    button.disabled = True  # Disable the button if volume is at maximum
                    await interaction.response.edit_message(view=self)  # Update the view
                else:
                    await interaction.response.send_message(f"Volume increased to {int(new_volume * 100)}%.", ephemeral=True)
            else:
                await interaction.response.send_message("The current audio source does not support volume control.", ephemeral=True)
        else:
            await interaction.response.send_message("No music is currently playing.", ephemeral=True)

async def checkPermission(interaction):
    # Get the bot's permissions in the guild (server) where the command was issued
    voice_channel = interaction.user.voice.channel
    permissions = voice_channel.permissions_for(interaction.guild.me)  # Bot's permissions in the guild

    # Required permissions list
    required_permissions = [
        permissions.connect,
        permissions.speak,
        permissions.read_messages,
        permissions.send_messages,
        permissions.embed_links,
        permissions.attach_files,
        permissions.manage_messages
    ]

    # Check if all required permissions are granted
    if not all(required_permissions):
        # Use interaction.guild to report the guild name instead of an undefined variable
        guild_name = interaction.guild.name if interaction.guild is not None else "Unknown Guild"
        print(f"Warning: Bot does not have all necessary permissions in the guild: {guild_name}")
        missing_permissions = [
            perm for perm, has_perm in zip([
                "connect", "speak", "read_messages",
                "send_messages", "embed_links", "attach_files", "manage_messages"
            ], required_permissions) if not has_perm
        ]

        # Send a message to the channel about missing permissions
        await interaction.response.send_message(
            f"⚠️ The bot is missing the following permissions in this guild: {', '.join(missing_permissions)}",
            ephemeral=True
        )
        return False
    return True


# Play command as a slash command
@bot.tree.command(name='play', description="Play a song by name")
async def play(interaction: discord.Interaction, song_name: str):
    global current_voice_client, current_song_info, song_queue, is_looping

    if await checkPermission(interaction):
        # Ensure the user is in a voice channel
        if interaction.user.voice:
            user_channel = interaction.user.voice.channel

            # Check if the bot is connected and in the same channel as the user
            if current_voice_client is None or not current_voice_client.is_connected():
                # Connect to the user's channel if not connected
                current_voice_client = await user_channel.connect()
            elif current_voice_client.channel != user_channel:
                # If the bot is connected to another channel, check for members
                if len(current_voice_client.channel.members) > 1:
                    await interaction.response.send_message(
                        "I'm currently playing in another voice channel. Please wait until it becomes free or join that channel.",
                        ephemeral=True
                    )
                    return
                else:
                    # Move to the user's channel if no other members are present
                    await current_voice_client.move_to(user_channel)
            else:
                # The bot is already connected to the same channel
                pass

        else:
            await interaction.response.send_message("You need to be in a voice channel to play a song.", ephemeral=True)
            return

        await interaction.response.send_message("Fetching audio, please wait...", ephemeral=True)

        # Get the song's audio URL, title, duration, and thumbnail
        audio_url, title, duration, thumbnail_url = await get_audio_url(song_name)
        if current_voice_client.is_playing() or current_voice_client.is_paused():
            song_queue.append((audio_url, title, duration, thumbnail_url))
            await interaction.followup.send(f"Added **{title}** to the queue.", ephemeral=True)
        else:
            current_song_info = {
                'title': title,
                'duration': duration,
                'requested_by': interaction.user.display_name,
                'audio_url': audio_url  # Save URL to replay if looping
            }

            embed = discord.Embed(
                title="Now Playing",
                description=f"**{title}**",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=thumbnail_url)
            embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.avatar.url)
            embed.add_field(name="Volume", value="100%", inline=True)
            embed.add_field(name="Uptime", value="24/7", inline=True)

            await interaction.followup.send(embed=embed, view=MusicControlView())

            # Play the song
            audio_source = FFmpegPCMAudio(audio_url)
            current_voice_client.play(audio_source, after=lambda e: bot.loop.create_task(play_next_song(interaction)))


@bot.tree.command(name='ping', description="Check the bot's responsiveness")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Hey Buddy! Wanna Vibe? I'm up for streaming music 🎶. Use /help to know how to interact with me")

@bot.tree.command(name='play_url', description="Play music from a YouTube URL")
async def play_url(interaction: discord.Interaction, url: str):
    global current_voice_client, current_song_info, song_queue, is_looping

    if await checkPermission(interaction):
        # Ensure the user is in a voice channel
        if interaction.user.voice:
            user_channel = interaction.user.voice.channel

            # Check if the bot is connected and in the same channel as the user
            if current_voice_client is None or not current_voice_client.is_connected():
                # Connect to the user's channel if not connected
                current_voice_client = await user_channel.connect()
            elif current_voice_client.channel != user_channel:
                # If the bot is connected to another channel, check for members
                if len(current_voice_client.channel.members) > 1:
                    await interaction.response.send_message(
                        "I'm currently playing in another voice channel. Please wait until it becomes free or join that channel.",
                        ephemeral=True
                    )
                    return
                else:
                    # Move to the user's channel if no other members are present
                    await current_voice_client.move_to(user_channel)
            else:
               pass

        else:
            await interaction.response.send_message("You need to be in a voice channel to play a song.", ephemeral=True)
            return

        await interaction.response.send_message("Fetching audio, please wait...", ephemeral=True)

        # Get the audio URL, title, duration, and thumbnail directly from the provided URL
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            title = info['title']
            duration = info['duration']
            thumbnail_url = info['thumbnail']

        if current_voice_client.is_playing() or current_voice_client.is_paused():
            song_queue.append((audio_url, title, duration, thumbnail_url))
            await interaction.followup.send(f"Added **{title}** to the queue.", ephemeral=True)
        else:
            current_song_info = {
                'title': title,
                'duration': duration,
                'requested_by': interaction.user.display_name,
                'audio_url': audio_url  # Save URL to replay if looping
            }

            embed = discord.Embed(
                title="Now Playing",
                description=f"**{title}**",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=thumbnail_url)
            embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.avatar.url)
            embed.add_field(name="Volume", value="100%", inline=True)
            embed.add_field(name="Uptime", value="24/7", inline=True)

            await interaction.followup.send(embed=embed, view=MusicControlView())

            # Play the song
            audio_source = FFmpegPCMAudio(audio_url)
            current_voice_client.play(audio_source, after=lambda e: bot.loop.create_task(play_next_song(interaction)))

@bot.tree.command(name='skip', description="Skip the current song")
async def skip(interaction: discord.Interaction):
    view = MusicControlView()
    await view.skip_button.callback(interaction)

@bot.tree.command(name='join', description="Make the bot join the voice channel you are in")
async def join(interaction: discord.Interaction):
    global current_voice_client

    if await checkPermission(interaction):
    # Check if the user is in a voice channel
        if interaction.user.voice:
            user_channel = interaction.user.voice.channel

            # If the bot is not connected, or not playing in another channel
            if current_voice_client is None or not current_voice_client.is_connected():
                current_voice_client = await user_channel.connect()
                await interaction.response.send_message(f"Joined {user_channel.name}.", ephemeral=False)
            elif current_voice_client.channel != user_channel:
                # Check if there are other users in the current channel
                if len(current_voice_client.channel.members) > 1:
                    await interaction.response.send_message(
                        "I'm currently playing in another voice channel. Please wait until it becomes free or join that channel.",
                        ephemeral=True
                    )
                else:
                    # Disconnect from the current channel and connect to the user's channel
                    await current_voice_client.move_to(user_channel)
                    await interaction.response.send_message(f"Moved to {user_channel.name}.", ephemeral=False)
            else:
                await interaction.response.send_message("I'm already in your voice channel.", ephemeral=True)
        else:
            await interaction.response.send_message("You need to be in a voice channel to use this command.", ephemeral=True)

@bot.tree.command(name='queue', description="Show the current queue")
async def queue(interaction: discord.Interaction):
    view = MusicControlView()
    await view.queue_button.callback(interaction)

@bot.tree.command(name='pause', description="Pause or resume the current song")
async def pause(interaction: discord.Interaction):
    view = MusicControlView()
    await view.pause_button.callback(interaction)

@bot.tree.command(name='stop', description="Stop the current song and clear the queue")
async def stop(interaction: discord.Interaction):
    view = MusicControlView()
    await view.stop_button.callback(interaction)

@bot.tree.command(name='loop', description="Toggle looping of the current song")
async def loop(interaction: discord.Interaction):
    view = MusicControlView()
    await view.loop_button.callback(interaction)

@bot.tree.command(name='help', description="Show help information")
async def help(interaction: discord.Interaction):
  help_message = """
**Music Bot Commands**

**/play <song_name>**: Play a song by name.
**/play_url <url>**: Play music from a YouTube URL.
**/skip**: Skip the current song.
**/queue**: Show the current queue.
**/pause**: Pause or resume the current song.
**/stop**: Stop the current song and clear the queue.
**/loop**: Toggle looping of the current song.
**/ping**: Check the bot's responsiveness.

**Music Control Buttons**:
- ⏸️ **Pause**: Pause or resume the current song.
- ⏹️ **Stop**: Stop the current song and clear the queue.
- ⏭️ **Skip**: Skip to the next song.
- 📃 **Queue**: Show the current queue.
- 🔌 **Disconnect**: Disconnect the bot from the voice channel.
- 🔁 **Loop**: Toggle looping of the current song.
- 🔉 **Volume Down**: Decrease the volume.
- 🔊 **Volume Up**: Increase the volume.
"""
  await interaction.response.send_message(help_message, ephemeral=False)

@bot.tree.command(name='replay', description="Replay the current song")
async def replay(interaction: discord.Interaction):
    global current_voice_client, current_song_info

    if current_voice_client and current_song_info:
        audio_url = current_song_info['audio_url']
        title = current_song_info['title']
        thumbnail_url = current_song_info['thumbnail']

        embed = Embed(
            title="Now Playing",
            description=f"**{title}**",
            color=discord.Color.blue()
        )

        embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.avatar.url)
        embed.add_field(name="Volume", value="100%", inline=True)
        embed.add_field(name="Uptime", value="24/7", inline=True)

        await interaction.followup.send(embed=embed, view=MusicControlView())

        # Replay the song
        audio_source = FFmpegPCMAudio(audio_url)
        current_voice_client.stop()  # Stop the current playback
        current_voice_client.play(audio_source, after=lambda e: bot.loop.create_task(play_next_song(interaction)))
    else:
        await interaction.response.send_message("No song is currently playing to replay.", ephemeral=True)


@bot.tree.command(name='now_playing', description="Show the currently playing song")
async def now_playing(interaction: discord.Interaction):
    global current_song_info

    if current_song_info:
        embed = Embed(
            title="Now Playing",
            description=f"**{current_song_info['title']}**",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Requested by {current_song_info['requested_by']}", icon_url=interaction.user.avatar.url)
        embed.add_field(name="Volume", value="100%", inline=True)
        embed.add_field(name="Uptime", value="24/7", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=False)
    else:
        await interaction.response.send_message("No song is currently playing.", ephemeral=True)

@bot.tree.command(name='disconnect', description="Disconnect the bot from the voice channel")
async def disconnect(interaction: discord.Interaction):
    global current_voice_client

    if current_voice_client and current_voice_client.is_connected():
        await current_voice_client.disconnect()
        current_voice_client = None
        await interaction.response.send_message(f"Disconnected from the voice channel. Disconnected by {interaction.user.mention}.", ephemeral=False)
    else:
        await interaction.response.send_message("The bot is not connected to any voice channel.", ephemeral=True)

@bot.tree.command(name='clear_queue', description="Clear the current song queue")
async def clear_queue(interaction: discord.Interaction):
    global song_queue
    if song_queue:
        song_queue.clear()
        await interaction.response.send_message("The queue has been cleared.", ephemeral=False)
    else:
        await interaction.response.send_message("The queue is already empty.", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync() 
    print(f'{bot.user.name} has connected to Discord!')
# Run the bot
bot.run(TOKEN)
