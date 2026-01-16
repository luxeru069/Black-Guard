import discord
from discord.ext import commands, tasks
import asyncio
import time
from collections import defaultdict

# Create bot instance with permissions and intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Required for member join, ban, kick events
bot = commands.Bot(command_prefix="!", intents=intents)

# Store user message timestamps for flood protection
user_message_times = defaultdict(list)

# List of bad words for the profanity filter (you can customize this list)
bad_words = ["badword1", "badword2", "badword3"]  # Replace with actual bad words

# Logging channel for ban/kick actions
log_channel_name = "log-channel"  # Ensure you have a channel with this name for logging

# Event: Bot is online
@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")

# Event: Member joins
@bot.event
async def on_member_join(member):
    welcome_channel = discord.utils.get(member.guild.text_channels, name="welcome")
    if welcome_channel:
        await welcome_channel.send(f"Welcome to the server, {member.mention}!")

# Event: Member is banned
@bot.event
async def on_member_ban(guild, user):
    log_channel = discord.utils.get(guild.text_channels, name=log_channel_name)
    if log_channel:
        await log_channel.send(f"{user} has been banned from the server.")

# Event: Member is kicked
@bot.event
async def on_member_kick(guild, user):
    log_channel = discord.utils.get(guild.text_channels, name=log_channel_name)
    if log_channel:
        await log_channel.send(f"{user} has been kicked from the server.")

# Command: Ping
@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")

# Command: Ban user
@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"{member} has been banned.")
    log_channel = discord.utils.get(ctx.guild.text_channels, name=log_channel_name)
    if log_channel:
        await log_channel.send(f"{member} was banned by {ctx.author} for: {reason}")

# Command: Kick user
@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"{member} has been kicked.")
    log_channel = discord.utils.get(ctx.guild.text_channels, name=log_channel_name)
    if log_channel:
        await log_channel.send(f"{member} was kicked by {ctx.author} for: {reason}")

# Command: Mute user (with a mute role already set up in the server)
@bot.command(name="mute")
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, duration: int, *, reason=None):
    mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if mute_role is None:
        await ctx.send("No 'Muted' role found! Please create one.")
        return

    await member.add_roles(mute_role, reason=reason)
    await ctx.send(f"{member} has been muted for {duration} minutes.")

    await asyncio.sleep(duration * 60)  # Mute duration
    await member.remove_roles(mute_role)
    await ctx.send(f"{member} has been unmuted.")

# Command: Clear messages
@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount)
    await ctx.send(f"{amount} messages have been cleared.", delete_after=5)

# Event: Detect and delete spam messages (sent in quick succession)
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Spam detection (check for repeated messages from the same user)
    async for msg in message.channel.history(limit=10):
        if msg.author == message.author and (message.created_at - msg.created_at).total_seconds() < 5:
            await message.delete()
            await message.channel.send(f"{message.author} Please avoid spamming!")
            return

    # Profanity filter
    if any(word in message.content.lower() for word in bad_words):
        await message.delete()
        await message.channel.send(f"{message.author.mention}, please avoid using inappropriate language.")
        return

    # Flood protection (prevent message flood by same user)
    user_message_times[message.author.id].append(time.time())
    user_message_times[message.author.id] = [t for t in user_message_times[message.author.id] if time.time() - t < 10]

    if len(user_message_times[message.author.id]) > 5:  # More than 5 messages in 10 seconds
        await message.delete()
        await message.channel.send(f"{message.author.mention}, you're sending too many messages too quickly!")
        return

    await bot.process_commands(message)

# Run the bot with your token
bot.run('YOUR_BOT_TOKEN')