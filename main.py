import discord
from discord.ext import commands


bot = discord.Bot()


global users_with_voice_channel
users_with_voice_channel = []

##############################################################################################################

expected_username = "limonadeundco"
more_unlikely_expected_username = "eineisbxr"

def is_specific_user():
    async def predicate(ctx):
        print(ctx.author.name)  
        return ctx.author.name == expected_username or ctx.author.name == more_unlikely_expected_username
    return commands.check(predicate)

##############################################################################################################

class yes_no_selector(discord.ui.View):
    def __init__(self, name, category, user_limit, guild):
        super().__init__()
        self.name = name
        self.category = category
        self.user_limit = user_limit
        self.guild = guild
        
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success, row=0)
    async def yes(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.message.delete()
        
        current_user_voice_channel = interaction.user.voice.channel
        user_voice_channel = await self.guild.create_voice_channel(self.name, category=self.category, user_limit=self.user_limit)
        await interaction.user.move_to(user_voice_channel)
        await interaction.response.send_message(f"Created voice channel {user_voice_channel.mention}")
        
        await current_user_voice_channel.delete()
        
        print(users_with_voice_channel)
        
        #wait for inactivity
        await asyncio.sleep(5)
        while len(user_voice_channel.members) > 0:
            await asyncio.sleep(5)
        await user_voice_channel.delete()
        users_with_voice_channel.remove(interaction.user.name)
    
    @discord.ui.button(label="No", style=discord.ButtonStyle.danger, row=0)
    async def no(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.message.delete()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
        
@bot.slash_command(
    name="ping",
    description="Get the ping of the bot",
)
async def ping(interaction):
    await interaction.response.send_message(f"Pong! ({bot.latency*1000}ms)")
    

import asyncio

@bot.slash_command(
    name="setup",
    description="setup the bot channels", 
)
async def channel(interaction, count: int=1):
    guild = interaction.guild
    
    if count > 10:
        await interaction.response.send_message("You can only create a maximum of 10 channels at once")
        
    elif count > 1:
        for i in range(count):
            category = await guild.create_category(f"user channels-{i}")
            channel = await guild.create_text_channel(f"commands-{i}", category=category)
            voice_channel = await guild.create_voice_channel(f"Join to use commands-{i}", category=category)
    else:
        category = await guild.create_category("user channels")
        channel = await guild.create_text_channel("commands", category=category)
        voice_channel = await guild.create_voice_channel(f"Join to use commands", category=category)
        
    await interaction.response.send_message("Created user categories")

@bot.slash_command(
    name="create_voice",
    description="create your own voice channel",
)
async def create_voice(interaction, name: str, user_limit: int=0):
    guild = interaction.guild
    category = interaction.channel.category
    
    if interaction.channel.name.startswith("commands"):
        if interaction.user.voice:
            if interaction.user.voice.channel.category:
                if interaction.user.voice.channel.category.name.startswith("user channels"):
                    #handle that user already has a channel
                    if interaction.user.name in users_with_voice_channel:
                        await interaction.response.send_message("You already have a voice channel, do you want to create a new one? The previous one will be deleted!", view=yes_no_selector(name, category, user_limit, guild))

                        
                    else:
                        user_voice_channel = await guild.create_voice_channel(name, category=category, user_limit=user_limit)
                        await interaction.user.move_to(user_voice_channel)
                        await interaction.response.send_message(f"Created voice channel {user_voice_channel.mention}")
                        
                        users_with_voice_channel.append(interaction.user.name)
                        print(users_with_voice_channel)
                        
                        #wait for inactivity
                        await asyncio.sleep(5)
                        while len(user_voice_channel.members) > 0:
                            await asyncio.sleep(5)
                        await user_voice_channel.delete()
                        users_with_voice_channel.remove(interaction.user.name)

                        
                else:
                    await interaction.response.send_message("You can only create user voice channels in **Join to use commands** channels")
            else:
                await interaction.response.send_message("You can only create user voice channels in **Join to use commands** channels")   
        else:
            await interaction.response.send_message("You need to be in a voice channel to create a user voice channel")
    else:
        await interaction.response.send_message("You can only create user voice channels in **commands** text channels", ephemeral=True)


@bot.slash_command(
    name="remove_all",
    description="remove all channels",
)
async def remove_all(interaction):
    guild = interaction.guild
    for category in guild.categories:
        if category.name.startswith("user channels"):
            for channel in category.channels:
                await channel.delete()
            await category.delete()


@bot.slash_command(
    name="create_many_channels",
    description="Let the bot create many channels",
)
async def create_many_channels(ctx, amount: int=0):
    guild = ctx.guild
    for i in range(amount):
        await guild.create_text_channel(name=f"Channel-{i}")
    await ctx.response.send_message(f"Created {amount} channels")

##############################################################################################################


@bot.slash_command(
    name="delete_all_channels",
    description="Let the bot delete all channels",   
)
@is_specific_user()
async def delete_all_channels(ctx):
    if ctx.user.name != expected_username and ctx.user.name != more_unlikely_expected_username:
        return await ctx.response.send_message("You are not authorized to use this command.")
    
    if ctx.user.name == more_unlikely_expected_username:
        await ctx.response.send_message("You are not authorized to use this command. But I will let you do it anyway. Because I am nice. Deleting all channels")
    
    guild = ctx.guild
    for channel in guild.channels:
        if channel.name in ["rules", "moderator-only", "Allgemein", "Test", "user channels", "USER CHANNELS", "commands", "Join to use commands"]:
            continue
        await channel.delete()
        
    if ctx.user.name == expected_username:
        await ctx.response.send_message("Deleted all channels")
    
    
##############################################################################################################
   
@bot.slash_command(
    name="send_message_global",
    description="Send a message in all channels",
)
@commands.has_permissions(manage_channels=True)
async def send_message_global(ctx, message_content: str):
    guild = ctx.guild

    for channel in guild.channels:
        try:
            await channel.send(message_content)
        except Exception as e:
            print(f"Failed to send message to {channel.name}: {e}")

    await ctx.response.send_message("Message sent to all channels")
    
##############################################################################################################

@bot.slash_command(
    name="delete_all_messages",
    description="Let the bot delete all messages in a channel",
)

@is_specific_user()
async def delete_all_messages(ctx):
    if ctx.user.name != expected_username and ctx.user.name != more_unlikely_expected_username:
        return await ctx.response.send_message("You are not authorized to use this command.")
    
    if ctx.user.name == more_unlikely_expected_username:
        await ctx.response.send_message("You are not authorized to use this command. But I will let you do it anyway. Because I am nice. Deleting all messages")
    
    channel = ctx.channel
    async for message in channel.history(limit=None):
        await message.delete()
        
    if ctx.user.name == expected_username:
        await ctx.response.send_message("Deleted all messages")
        
##############################################################################################################
global ghost_mode
@bot.slash_command(
    name="ghost_mode",
    description="Lets no new messages be sent in a channel and if a new message is sent it will be deleted",
)
@is_specific_user()
async def ghost_mode(ctx):
    ghost_mode = True
    if ctx.user.name != expected_username and ctx.user.name != more_unlikely_expected_username:
        return await ctx.response.send_message("You are not authorized to use this command.")
    
    if ctx.user.name == more_unlikely_expected_username:
        await ctx.response.send_message("You are not authorized to use this command. But I will let you do it anyway. Because I am nice. Ghost mode activated")
    
    channel = ctx.channel
    await channel.set_permissions(ctx.guild.default_role, send_messages=False)
    
    if ctx.user.name == expected_username:
        await ctx.response.send_message("Ghost mode activated")

@bot.slash_command(
    name="unghost_mode",
    description="Lets new messages be sent in a channel and if a new message is sent it will not be deleted",
)
@is_specific_user()

async def unghost_mode(ctx):
    ghost_mode = False
    if ctx.user.name != expected_username and ctx.user.name != more_unlikely_expected_username:
        return await ctx.response.send_message("You are not authorized to use this command.")
    
    if ctx.user.name == more_unlikely_expected_username:
        await ctx.response.send_message("You are not authorized to use this command. But I will let you do it anyway. Because I am nice. Ghost mode deactivated")
    
    channel = ctx.channel
    await channel.set_permissions(ctx.guild.default_role, send_messages=True)
    
    if ctx.user.name == expected_username:
        await ctx.response.send_message("Ghost mode deactivated")
        
# now on message sent event check
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if ghost_mode:
        await message.delete()
##############################################################################################################
@bot.event
async def on_slash_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        # Check failed, perform desired actions
        await ctx.send("You are not authorized to use this command.")
        
 
 
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="dir zu"))

bot.run('MTE5Mjg5MDQ1MjM4MzM4NzgwOQ.GvbATw.I_a6ApzFQzoDOmz4r7AEBUEnaDwfD8d5Ul5CUw')
