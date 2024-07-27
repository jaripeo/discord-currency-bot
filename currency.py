from nextcord.ext import commands
import nextcord
import asyncio
import aiosqlite
import random

from typing import Final
from dotenv import load_dotenv
import os

class ShopView(nextcord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.bot = bot

    @nextcord.ui.button(
        label="Laptop", style=nextcord.ButtonStyle.blurple, custom_id="laptop"
    )
    async def laptop(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        async with self.bot.db.cursor() as cursor:
            await cursor.execute("SELECT laptop from inv WHERE user = ?", (interaction.user.id,))
            item = await cursor.fetchone()
            if item is None:
                await cursor.execute("INSERT INTO inv VALUES (?, ?, ?, ?)", (1,0,0, interaction.user.id,))
            else:
                await cursor.execute("UPDATE inv SET laptop = ? WHERE user = ?", (item[0] + 1, interaction.user.id,))
            await self.bot.db.commit()
            await interaction.send("Laptop Bought!")

    @nextcord.ui.button(
        label = "Phone", style=nextcord.ButtonStyle.blurple, custom_id="phone"
    )
    async def phone(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        async with self.bot.db.cursor() as cursor:
            await cursor.execute("SELECT phone from inv WHERE user = ?", (interaction.user.id,))
            item = await cursor.fetchone()
            if item is None:
                await cursor.execute("INSERT INTO inv VALUES (?, ?, ?, ?)", (1,0,0, interaction.user.id,))
            else:
                await cursor.execute("UPDATE inv SET phone = ? WHERE user = ?", (item[0] + 1, interaction.user.id,))
            await self.bot.db.commit()
            await interaction.send("Phone Bought!")

    @nextcord.ui.button(
        label = "FakeID", style=nextcord.ButtonStyle.blurple, custom_id="fakeid"
    )
    async def fakeid(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        async with self.bot.db.cursor() as cursor:
            await cursor.execute("SELECT fakeid from inv WHERE user = ?", (interaction.user.id,))
            item = await cursor.fetchone()
            if item is None:
                await cursor.execute("INSERT INTO inv VALUES (?, ?, ?, ?)", (1,0,0, interaction.user.id,))
            else:
                await cursor.execute("UPDATE inv SET fakeid = ? WHERE user = ?", (item[0] + 1, interaction.user.id,))
            await self.bot.db.commit()
            await interaction.send("FakeID Bought!")

# step 0: load token  
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!', intents = nextcord.Intents.all())

@bot.event
async def on_ready():
    print("Bot is up and running!")
    bot.db = await aiosqlite.connect("bank.db")
    await asyncio.sleep(3)
    async with bot.db.cursor() as cursor:
        await cursor.execute("CREATE TABLE IF NOT EXISTS bank(wallet INTEGER, bank INTEGER, maxbank INTEGER, user INTEGER)")
        await cursor.execute("CREATE TABLE IF NOT EXISTS inv(laptop INTEGER, phone INTEGER, fakeid INTEGER, user INTEGER)")
        await cursor.execute("CREATE TABLE IF NOT EXISTS shop(name TEXT, id TEXT, desc TEXT, cost INTEGER)")
    
    await bot.db.commit()
    print("Database Ready!")

async def create_balance(user):
    async with bot.db.cursor() as cursor:
        await cursor.execute("INSERT INTO bank VALUES(?, ?, ?, ?)", (0, 100, 500, user.id))
    await bot.db.commit()
    return

async def create_inv(user):
    async with bot.db.cursor() as cursor:
        await cursor.execute("INSERT INTO inv VALUES(?, ?, ?, ?)", (0, 0, 0, user.id))
    await bot.db.commit()
    return

async def get_balance(user):
    async with bot.db.cursor() as cursor:
        await cursor.execute("SELECT wallet, bank, maxbank FROM bank WHERE user = ?", (user.id,))
        data = await cursor.fetchone()
        if data is None:
            await create_balance(user)
            return 0, 100, 500
        wallet, bank, maxbank = data[0], data[1], data[2]
        return wallet, bank, maxbank
    
async def get_inv(user):
    async with bot.db.cursor() as cursor:
        await cursor.execute("SELECT laptop, phone, fakeid FROM inv WHERE user = ?", (user.id,))
        data = await cursor.fetchone()
        if data is None:
            await create_inv(user)
            return 0, 0, 0
        laptop, phone, fakeid = data[0], data[1], data[2]
        return laptop, phone, fakeid

async def update_wallet(user, amount: int):
    async with bot.db.cursor() as cursor:
        await cursor.execute("SELECT wallet FROM bank WHERE user = ?", (user.id,))
        data = await cursor.fetchone()
        if data is None:
            await create_balance(user)
            return 0
        await cursor.execute("UPDATE bank SET wallet = ? WHERE user = ?", (data[0] + amount, user.id))
    await bot.db.commit()

async def update_bank(user, amount, trans=1):
    async with bot.db.cursor() as cursor:
        await cursor.execute("SELECT wallet, bank, maxbank FROM bank WHERE user = ?", (user.id,))
        data = await cursor.fetchone()
        if data is None:
            await create_balance(user)
            return 0
        capacity = int(data[2] - data[1]) #max bank minus currBank
        if amount > capacity:
            await update_wallet(user, amount)
            return 1
        elif abs(amount) > int(data[1]) and trans == 2:
            await update_wallet(user, amount)
            print(f"{amount} then there is {data[2]} then {data[1]}")
            return 2
        
        await cursor.execute("UPDATE bank SET bank = ? WHERE user = ?", (data[1] + amount, user.id))
    await bot.db.commit()

async def update_maxbank(user, amount):
    async with bot.db.cursor() as cursor:
        await cursor.execute("SELECT maxbank FROM bank WHERE user = ?", (user.id,))
        data = await cursor.fetchone()
        if data is None:
            await create_balance(user)
            return 0
        await cursor.execute("UPDATE bank SET maxbank = ? WHERE user = ?", (data[0] + amount, user.id))
    await bot.db.commit()

async def update_shop(name: str, id: str, desc: str, cost: int):
    async with bot.db.cursor() as cursor:
        await cursor.execute("INSERT INTO shop VALUES(?, ?, ?, ?)", (name, id, desc, cost))
    await bot.db.commit()
    return 

# ******************    COMMANDS **********************

@bot.command()
@commands.is_owner()
async def add_items(ctx: commands.Context, name: str, id: str, desc: str, cost: int):
    await update_shop(name, id, desc, cost)
    await ctx.send("Item added!", delete_after=5)

@bot.command()
async def balance(ctx: commands.Context, member: nextcord.Member = None):
    if not member:
        member = ctx.author
    wallet, bank, maxbank = await get_balance(member)
    em = nextcord.Embed(title=f"{member.name}'s Balance")
    em.add_field(name="Wallet", value=wallet)
    em.add_field(name="Bank", value=f"{bank}/{maxbank}")
    await ctx.send(embed = em)

@bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def beg(ctx: commands.Context):
    chances = random.randint(1, 4)
    if chances == 1:
        return await ctx.send("You got nothing")
    amount = random.randint(5, 300) #min to win is 5 and max is 300
    res = await update_wallet(ctx.author, amount)
    if res == 0:
        return await ctx.send("No account found so one has been created for you. Please run the command again!")
    await ctx.send(f"You got {amount} coins!")

@bot.command()
@commands.cooldown(1,5, commands.BucketType.user)
async def withdraw(ctx: commands.Context, amount):
    wallet, bank, maxbank = await get_balance(ctx.author)
    try:
        amount = int(amount)
    except ValueError:
        pass
    if type(amount) == str:
        if amount.lower() == "max" or amount.lower() == "all":
            amount = int(bank)
    else:
        amount = int(amount)
    
    bank_res = await update_bank(ctx.author, -amount, 2) #this 2 means that its "trans" or transaction is a withdrawal
    wallet_res = await update_wallet(ctx.author, amount)
    if bank_res == 0 or wallet_res == 0:
        return await ctx.send("No account found so no one has been created for you. Please run the commands again!")
    elif bank_res == 2:
        return await ctx.send("You cannot withdraw more than what you have! Please try again!")

    wallet, bank, maxbank = await get_balance(ctx.author)
    em = nextcord.Embed(title=f"{amount} coins have been withdrawn")
    em.add_field(name="New Wallet", value=wallet)
    em.add_field(name="New Bank", value=f"{bank}/{maxbank}")
    await ctx.send(embed=em)

@bot.command()
@commands.cooldown(1,5, commands.BucketType.user)
async def deposit(ctx: commands.Context, amount):
    wallet, bank, maxbank = await get_balance(ctx.author)
    try:
        amount = int(amount)
    except ValueError:
        pass
    if type(amount) == str:
        if amount.lower() == "max" or amount.lower() == "all":
            amount = int(wallet)
    else:
        amount = int(amount)
    bank_res = await update_bank(ctx.author, amount)
    wallet_res = await update_wallet(ctx.author, -amount)
    if bank_res == 0 or wallet_res == 0:
        return await ctx.send("No account found so no one has been created for you. Please run the commands again!")
    elif bank_res == 1:
        return await ctx.send("You don't have enough storage in your bank!")

    wallet, bank, maxbank = await get_balance(ctx.author)
    em = nextcord.Embed(title=f"{amount} coins have been deposited")
    em.add_field(name="New Wallet", value=wallet)
    em.add_field(name="New Bank", value=f"{bank}/{maxbank}")
    await ctx.send(embed=em)

@bot.command()
@commands.cooldown(1,10, commands.BucketType.user)
async def give(ctx: commands.Context, member: nextcord.Member, amount):
    wallet, bank, maxbank = await get_balance(ctx.author)
    try:
        amount = int(amount)
    except ValueError:
        pass
    if type(amount) == str:
        if amount.lower() == "max" or amount.lower() == "all":
            amount = int(wallet)
    else:
        amount = int(amount)

    wallet_res = await update_wallet(ctx.author, -amount)
    wallet_res2 = await update_wallet(member, amount)
    if wallet_res == 0 or wallet_res2 == 0:
        return await ctx.send("No account found so no one has been created for you. Please run the commands again!")

    wallet, bank, maxbank = await get_balance(member) #added this part myself c:
    wallet2, bank2, maxbank2 = await get_balance(member)

    em = nextcord.Embed(title=f"Gave {amount} coins to {member.name}")
    em.add_field(name=f"{ctx.author.name}'s Wallet", value=wallet)
    em.add_field(name=f"{member.name}'s Wallet", value=wallet2)
    await ctx.send(embed=em)

@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def shop(ctx: commands.Context):
    embed = nextcord.Embed(title="Drome Shop")
    async with bot.db.cursor() as cursor:
        await cursor.execute("SELECT name, desc, cost FROM shop")
        shop = await cursor.fetchall()
        for item in shop:
            embed.add_field(name=item[0], value=f"{item[1]} | Cost: {item[2]}", inline=False)
    await ctx.send(embed=embed, view=ShopView(bot))

@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def secret(ctx: commands.Context):
    amount = 300
    res = await update_wallet(ctx.author, amount)
    if res == 0:
        return await ctx.send("No account found so one has been created for you. Please run the command again!")
    await ctx.send(f"You got {amount} coins! (secretly...)")

@bot.command()
@commands.cooldown(1, 1, commands.BucketType.user)
async def gamble(ctx: commands.Context, amount):
    wallet, bank, maxbank = await get_balance(ctx.author)
    try:
        amount = int(amount)
    except ValueError:
        pass
    if type(amount) == str:
        if amount.lower() == "max" or amount.lower() == "all":
            amount = int(wallet)
    else:
        amount = int(amount)

    chances = random.randint(1, 3)
    
    if chances == 1:
        wallet_res = await update_wallet(ctx.author, amount)
        if wallet_res == 0:
            return await ctx.send("No account found so no one has been created for you. Please run the commands again!")
        await ctx.send(f"You got {amount}! 🎉")
    else:
        wallet_res = await update_wallet(ctx.author, -amount)
        if wallet_res == 0:
            return await ctx.send("No account found so no one has been created for you. Please run the commands again!")
        await ctx.send(f"You lost {amount}...😞")
    
    wallet, bank, maxbank = await get_balance(ctx.author)
    em = nextcord.Embed(title=f"Gambled {amount} coins.")
    em.add_field(name="New Wallet", value=wallet)
    em.add_field(name="New Bank", value=f"{bank}/{maxbank}")
    await ctx.send(embed=em)


bot.run(TOKEN)
