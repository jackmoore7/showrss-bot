import os
import discord
import asyncio
import feedparser
from datetime import datetime as dt
from discord.ext import tasks
from discord.ui import Button, View
import sqlite3 as sl
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.all()
intents.members = True

discordClient = discord.Bot(intents=intents)

con = sl.connect('showrss.db', isolation_level=None)
cursor = con.cursor()

@discordClient.event
async def on_ready():
	print(f'{discordClient.user} is now online!')
	await discordClient.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="TV"))
	tv_show_update_bg.start()

@tasks.loop(minutes=30)
async def tv_show_update_bg():
	try:
		user = discordClient.get_user(int(os.getenv('ME')))
		url = os.getenv('SHOWRSS')
		feed = feedparser.parse(url)
		last_guid = cursor.execute("select * from rss").fetchall()[0][0]
		if len(feed['entries']) > 0:
			latest_guid = feed['entries'][0]['guid']
		else:
			print("No recent episode entries. Skipping...")
			return
		if latest_guid != last_guid:
			rssembed = discord.Embed(title = "A new episode just released!")
			rssembed.add_field(name="Name", value=feed['entries'][0]['tv_raw_title'], inline=False)
			rssembed.add_field(name="Released", value=feed['entries'][0]['published'], inline=False)
			cursor.execute("UPDATE rss SET guid = ?", (latest_guid,))
			await user.send(embed = rssembed)
	except Exception as e:
		print("Something went wrong getting the TV show RSS: " + str(repr(e)) + "\nRestarting internal task in 1 minute.")
		await asyncio.sleep(60)
		tv_show_update_bg.restart()