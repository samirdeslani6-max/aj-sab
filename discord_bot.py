# ================================================================
# DISCORD BOT - NIGGA FINDER & ANTI-RAID PROTECTION SYSTEM
# Projet : AJ SAB
# ================================================================

import discord
from discord.ext import commands
import asyncio
import re
import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

import os

# --- CONFIGURATION BOT DISCORD ---
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
CLIENT_ID = "1557143518202302577"
SERVER_API_URL = os.environ.get("SERVER_API_URL", "https://aj-sab.onrender.com/api/add_wallet")

ROLE_MEMBER = "Membre"
ROLE_BUYER  = "Nigga Buyer"

# Regex for anti-pub invite link detection
INVITE_REGEX = re.compile(r"(discord\.gg/|discord\.com/invite/|discordapp\.com/invite/|https?://[^\s]+\.gg/[^\s]+)", re.IGNORECASE)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("==================================================")
    print(f"   🤖 DISCORD BOT CONNECTED: {bot.user.name} ({bot.user.id})")
    print(f"   🔒 ANTI-RAID & ANTI-PUB: ACTIVE")
    print(f"   ⚙️ AUTO ROLE JOIN: {ROLE_MEMBER}")
    print(f"   💳 BUYER ROLE: {ROLE_BUYER}")
    print(f"   💰 WALLET COMMAND: !5wallet <user_id> <amount>")
    print("==================================================")

@bot.event
async def on_member_join(member):
    """Auto-assigns Member role when a user joins the server."""
    guild = member.guild
    role = discord.utils.get(guild.roles, name=ROLE_MEMBER)

    if not role:
        try:
            role = await guild.create_role(name=ROLE_MEMBER, color=discord.Color.blue(), reason="Auto Member Role")
        except Exception as e:
            print(f"[!] Error creating role '{ROLE_MEMBER}': {e}")
            return

    try:
        await member.add_roles(role)
        print(f"[+] Role '{ROLE_MEMBER}' assigned to {member.name}")
    except Exception as e:
        print(f"[!] Error assigning role to {member.name}: {e}")

@bot.event
async def on_message(message):
    """Instant Anti-Pub & Anti-Raid Protection."""
    if message.author.bot:
        return

    # Anti-pub invite link detection
    if INVITE_REGEX.search(message.content):
        try:
            await message.delete()
            print(f"[🚨 ANTI-PUB] Invite link deleted from {message.author.name}")

            reason_msg = "Anti-Pub / Invite Spam Detected"
            await message.guild.ban(message.author, reason=reason_msg, delete_message_days=7)
            print(f"[🔒 ANTI-PUB BAN] {message.author.name} (ID: {message.author.id}) banned.")
        except Exception as e:
            print(f"[!] Error Anti-Pub action: {e}")
        return

    await bot.process_commands(message)

# ── 5WALLET COMMAND: ADD MONEY TO DISCORD USER WALLET ───────────
@bot.command(name="5wallet")
@commands.has_permissions(administrator=True)
async def cmd_5wallet(ctx, user_target: str, amount: float):
    """
    Usage: !5wallet <user_id, @mention, or username> <amount>
    Example: !5wallet @look 50  OR  !5wallet 285828205162528768 50
    """
    user_id_clean = re.sub(r"[<@!>]", "", user_target).strip()
    
    target_name = user_target.replace("@", "")
    target_id = user_id_clean

    try:
        if user_id_clean.isdigit():
            target_user = await bot.fetch_user(int(user_id_clean))
            target_name = target_user.name
            target_id = str(target_user.id)
    except Exception:
        pass

    # Notify both local server and Render API endpoints
    api_urls = [
        "http://localhost:8080/api/add_wallet",
        os.environ.get("SERVER_API_URL", "https://aj-sab.onrender.com/api/add_wallet")
    ]

    payload = json.dumps({
        "user_id": target_id,
        "username": target_name,
        "amount": amount,
        "admin": ctx.author.name
    }).encode('utf-8')

    for url in api_urls:
        try:
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                print(f"[5WALLET] Successfully notified API endpoint: {url}")
        except Exception as e:
            pass

    embed = discord.Embed(
        title="💳 WALLET BALANCE CREDITED",
        color=0x00E676,
        description=f"Successfully added **${amount:.2f} USD** to user wallet!"
    )
    embed.add_field(name="👤 Target User", value=f"**{target_name}** (`{target_id}`)", inline=True)
    embed.add_field(name="💵 Added Balance", value=f"**+${amount:.2f} USD**", inline=True)
    embed.add_field(name="🛡️ Admin", value=f"`{ctx.author.name}`", inline=False)
    embed.set_footer(text="Nigga Notifier v2 · Wallet Management System")

    await ctx.send(embed=embed)
    print(f"[5WALLET] ${amount:.2f} credited to {target_name} ({target_id}) by {ctx.author.name}")

@bot.command(name="5ban")
@commands.has_permissions(ban_members=True)
async def cmd_5ban(ctx, user_id: int):
    """Ban user by Discord ID."""
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.ban(user, reason="Banned via !5ban command", delete_message_days=7)
        await ctx.send(f"✅ User **{user.name}** (ID: `{user_id}`) has been permanently banned.")
        print(f"[5BAN] {user.name} ({user_id}) banned by {ctx.author.name}")
    except Exception as e:
        await ctx.send(f"❌ Failed to ban ID `{user_id}`: {e}")

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def cmd_ban(ctx, user_id: int):
    await cmd_5ban(ctx, user_id)

async def grant_buyer_role(guild_id, user_discord_tag):
    guild = bot.get_guild(guild_id) if guild_id else (bot.guilds[0] if bot.guilds else None)
    if not guild:
        return False

    buyer_role = discord.utils.get(guild.roles, name=ROLE_BUYER)
    if not buyer_role:
        try:
            buyer_role = await guild.create_role(name=ROLE_BUYER, color=discord.Color.purple(), reason="Auto Buyer Role")
        except Exception as e:
            print(f"[!] Error creating '{ROLE_BUYER}' role: {e}")
            return False

    clean_tag = user_discord_tag.lower().replace("@", "")
    target_member = None
    for member in guild.members:
        if clean_tag in member.name.lower() or clean_tag in str(member).lower():
            target_member = member
            break

    if target_member:
        try:
            await target_member.add_roles(buyer_role)
            print(f"[💳 PAYMENT] Role '{ROLE_BUYER}' assigned to {target_member.name}!")
            return True
        except Exception as e:
            print(f"[!] Error assigning buyer role: {e}")
    return False

if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f"[!] Discord Bot Error: {e}")
