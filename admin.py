import discord
from discord.ext import commands
from discord.utils import get
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')  # Store your token in a .env file

# Set up bot with intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# List of bad words (basic example – moderate level, customize as needed)
BAD_WORDS = {
    'ass', 'asshole', 'bastard', 'bitch', 'bloody', 'bollocks', 'cock',
    'crap', 'cunt', 'damn', 'dick', 'douche', 'fuck', 'fucker', 'fucking',
    'goddamn', 'hell', 'jerk', 'kike', 'motherfucker', 'nigga', 'nigger',
    'piss', 'prick', 'pussy', 'shit', 'slut', 'spastic', 'twat', 'wank',
    'whore'
}

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'Bot is online: {bot.user}')

# Event: Welcome new members
@bot.event
async def on_member_join(member):
    welcome_channel = get(member.guild.text_channels, name="general")  # Adjust channel name as needed
    if welcome_channel:
        await welcome_channel.send(f"👋 Welcome {member.mention}! Thanks for joining our server!")
    else:
        print(f"Warning: Could not find 'general' channel in {member.guild.name}")

# Command: Display project information
@bot.command()
async def project(ctx):
    embed = discord.Embed(
        title="Project Information",
        description="This is a Discord bot built for our community. It includes features like automated welcomes, message responses, moderation tools, and bad word filtering with auto-mute.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

# Command: List all available commands (admin only)
@bot.command(name='commandlist')
@commands.has_permissions(administrator=True)
async def commandlist(ctx):
    embed = discord.Embed(
        title="Available Commands",
        description="List of all commands available in this bot.",
        color=discord.Color.green()
    )
    embed.add_field(
        name="!project",
        value="Displays information about the bot project.",
        inline=False
    )
    embed.add_field(
        name="!commandlist",
        value="Lists all available commands (admin only).",
        inline=False
    )
    embed.add_field(
        name="!kick <member> [reason]",
        value="Kicks a member from the server (requires kick permissions).",
        inline=False
    )
    embed.add_field(
        name="!ban <member> [reason]",
        value="Bans a member from the server (requires ban permissions).",
        inline=False
    )
    embed.add_field(
        name="!unban <member_name>",
        value="Unbans a member from the server (requires ban permissions).",
        inline=False
    )
    embed.add_field(
        name="!mute <member> [duration_in_seconds] [reason]",
        value="Mutes a member for a specified duration in seconds (default 60) by assigning the Muted role (requires manage roles permissions).",
        inline=False
    )
    embed.add_field(
        name="!unmute <member> [reason]",
        value="Unmutes a member by removing the Muted role (requires manage roles permissions).",
        inline=False
    )
    embed.add_field(
        name="!clear <amount>",
        value="Clears a specified number of messages (1-100) from the channel (requires manage messages permissions).",
        inline=False
    )
    embed.add_field(
        name="!say <message>",
        value="Sends a message as the bot and deletes the command message (admin only).",
        inline=False
    )
    await ctx.send(embed=embed)

# Event: Auto-respond to specific messages and check for bad words
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Check for bad words
    message_content = message.content.lower()
    for word in BAD_WORDS:
        if word in message_content:
            try:
                muted_role = get(message.guild.roles, name="Muted")
                if not muted_role:
                    muted_role = await message.guild.create_role(name="Muted")
                    for channel in message.guild.channels:
                        await channel.set_permissions(muted_role, speak=False, send_messages=False)
                await message.author.add_roles(muted_role, reason="Used a bad word")
                await message.channel.send(f'{message.author.mention} has been muted for 30 seconds for using a bad word.')
                await asyncio.sleep(30)  # Mute duration for bad words
                await message.author.remove_roles(muted_role, reason="Auto unmute after 30 seconds")
                await message.channel.send(f'{message.author.mention} has been unmuted.')
            except Exception as e:
                await message.channel.send(f"Error handling bad word mute: {str(e)}")
            break

    # Auto-respond to greetings
    greetings = ["hello", "hi", "heyyo", "salam", "selam", "sa"]
    if any(greeting in message_content for greeting in greetings):
        await message.channel.send(f"Hey {message.author.mention}! How's it going?")
    
    await bot.process_commands(message)

# Moderation Commands

# Command: Kick a member
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    try:
        await member.kick(reason=reason)
        await ctx.send(f'{member.name} has been kicked. Reason: {reason}')
    except Exception as e:
        await ctx.send(f"Error kicking {member.name}: {str(e)}")

# Command: Ban a member
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    try:
        await member.ban(reason=reason)
        await ctx.send(f'{member.name} has been banned. Reason: {reason}')
    except Exception as e:
        await ctx.send(f"Error banning {member.name}: {str(e)}")

# Command: Unban a member
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member_name):
    try:
        banned_users = await ctx.guild.bans()
        for ban_entry in banned_users:
            user = ban_entry.user
            if user.name == member_name:
                await ctx.guild.unban(user)
                await ctx.send(f'{user.name} has been unbanned.')
                return
        await ctx.send(f'User {member_name} not found in ban list.')
    except Exception as e:
        await ctx.send(f"Error unbanning {member_name}: {str(e)}")

# Command: Mute a member with duration
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, duration: int = 60, *, reason="No reason provided"):
    try:
        muted_role = get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)
        await member.add_roles(muted_role, reason=reason)
        await ctx.send(f'{member.name} has been muted for {duration} seconds. Reason: {reason}')
        await asyncio.sleep(duration)
        if muted_role in member.roles:
            await member.remove_roles(muted_role, reason="Auto unmute after duration")
            await ctx.send(f'{member.name} has been unmuted.')
    except Exception as e:
        await ctx.send(f"Error muting {member.name}: {str(e)}")

# Command: Unmute a member
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member, *, reason="No reason provided"):
    try:
        muted_role = get(ctx.guild.roles, name="Muted")
        if not muted_role:
            await ctx.send("No 'Muted' role found in this server.")
            return
        if muted_role in member.roles:
            await member.remove_roles(muted_role, reason=reason)
            await ctx.send(f'{member.name} has been unmuted. Reason: {reason}')
        else:
            await ctx.send(f'{member.name} is not muted.')
    except Exception as e:
        await ctx.send(f"Error unmuting {member.name}: {str(e)}")

# Command: Clear messages
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    try:
        if amount < 1 or amount > 100:
            await ctx.send("Please specify an amount between 1 and 100.")
            return
        await ctx.channel.purge(limit=amount + 1)  # +1 to include command message
        await ctx.send(f'{amount} messages deleted.', delete_after=5)
    except Exception as e:
        await ctx.send(f"Error clearing messages: {str(e)}")

# Command: Say a message (admin only)
@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx, *, message):
    try:
        await ctx.message.delete()
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"Error sending message: {str(e)}")

# Error handling for missing permissions
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please provide all required arguments.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

# Run the bot
if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: No bot token provided in .env file")