import nextcord
from nextcord.ext import commands

from loguru import logger

import webscraper
import config

import json
import time
import threading

import datetime
import asyncio

intents = nextcord.Intents().all()
bot = commands.Bot(intents=intents)

data = {}
update_queue = []


class ActivityUpdateTimer(threading.Thread):
    def __init__(self):
        super().__init__()
        self._stopped = threading.Event()
        self._initial = True
        self.runs = 0
        logger.debug("activity update timer ready")
    def run(self):
        if self._initial:
            time.sleep(10)
            logger.debug("activity update timer started")
        while not self._stopped.wait(1):
            self.runs += 1
            #try:
            self.update_activity()
            #except:
            #    print('owned')
            print(self.runs)
            # debug
    def stop(self):
        self._stopped.set()
        logger.debug("activity update timer stopped")
    def update_activity(self):
        for guild in data.keys():
            for user in data[guild]['users'].keys():
                logger.debug(f"checking user {user} in guild {guild}")                
                user_recent_activity = webscraper.scrape_activity('https://osu.ppy.sh/u/' + user)

                end_index = 0
                for i in range(len(user_recent_activity)):
                    if user_recent_activity[i] == data[guild]['users'][user][0]:
                        break
                    end_index += 1

                current_index = 0
                while end_index != current_index:
                    action = user_recent_activity[current_index]
                    activity_type = action['type']
                    if activity_type == "beatmapsetUpdate":
                        # maybe somehow dont hardcode the emoji
                        embed=nextcord.Embed(title="<:beatmapupdate:994458917180559401>  Updated Beatmap", description=f"[{action['beatmapset']['title']}](https://osu.ppy.sh{action['beatmapset']['url']})")
                        embed.set_author(name=f"{action['user']['username']}", icon_url=f"https://a.ppy.sh/{user}", url=f"https://osu.ppy.sh/users/{user}")
                        embed.set_image(url=f"https://assets.ppy.sh/beatmaps/{action['beatmapset']['url'][3:]}/covers/cover.jpg")
                        embed.timestamp = datetime.datetime.fromisoformat(f"{action['created_at']}")
                        channel = nextcord.utils.get(bot.get_all_channels(), id=data[guild]['channel'])
                        update_queue.append([channel, embed])
                    elif activity_type == "beatmapsetRevive":
                        # get right emoji
                        embed=nextcord.Embed(title="<:beatmaprevive:>  Revived Beatmap", description=f"[{action['beatmapset']['title']}](https://osu.ppy.sh{action['beatmapset']['url']})")
                        embed.set_author(name=f"{action['user']['username']}", icon_url=f"https://a.ppy.sh/{user}", url=f"https://osu.ppy.sh/users/{user}")
                        embed.set_image(url=f"https://assets.ppy.sh/beatmaps/{action['beatmapset']['url'][3:]}/covers/cover.jpg")
                        embed.timestamp = datetime.datetime.fromisoformat(f"{action['created_at']}")
                        channel = nextcord.utils.get(bot.get_all_channels(), id=data[guild]['channel'])
                        update_queue.append([channel, embed])
                    elif activity_type == "beatmapsetUpload":
                        # get right emoji
                        embed=nextcord.Embed(title="<:beatmapupload:>  Beatmap Upload", description=f"[{action['beatmapset']['title']}](https://osu.ppy.sh{action['beatmapset']['url']})")
                        embed.set_author(name=f"{action['user']['username']}", icon_url=f"https://a.ppy.sh/{user}", url=f"https://osu.ppy.sh/users/{user}")
                        embed.set_image(url=f"https://assets.ppy.sh/beatmaps/{action['beatmapset']['url'][3:]}/covers/cover.jpg")
                        embed.timestamp = datetime.datetime.fromisoformat(f"{action['created_at']}")
                        channel = nextcord.utils.get(bot.get_all_channels(), id=data[guild]['channel'])
                        update_queue.append([channel, embed])
                    elif activity_type == "beatmapsetApprove":
                        embed=nextcord.Embed(description=f"[{action['beatmapset']['title']}](https://osu.ppy.sh{action['beatmapset']['url']})")
                        embed.set_author(name=f"{action['user']['username']}", icon_url=f"https://a.ppy.sh/{user}", url=f"https://osu.ppy.sh/users/{user}")
                        embed.set_image(url=f"https://assets.ppy.sh/beatmaps/{action['beatmapset']['url'][3:]}/covers/cover.jpg")
                        embed.timestamp = datetime.datetime.fromisoformat(f"{action['created_at']}")
                        channel = nextcord.utils.get(bot.get_all_channels(), id=data[guild]['channel'])

                        # get right emoji
                        approval = action['approval']
                        if approval == "qualified":
                            embed.set_title("<:beatmapqualify:>  Qualified Beatmap")
                        elif approval == "ranked":
                            embed.set_title("<:beatmaprank:>  Ranked Beatmap")
                        # idk if this is real
                        elif approval == "loved":
                            embed.set_title("<:beatmaplove:>  Loved Beatmap")
                        else:
                            embed.set_title("breh")
                        
                        update_queue.append([channel, embed])
                    elif activity_type == "rank":
                        pass
                    elif activity_type == "rankLost":
                        pass
                    elif activity_type == "achievement":
                        pass
                    # add one for supporter

                    current_index += 1
                    
                if end_index != 0:
                    data[guild]['users'][user] = user_recent_activity
                    with open('data.json', 'w') as f:
                        json.dump(data, f)


@bot.event
async def on_ready():
    global data

    with open('data.json', 'r') as f:
        data = json.load(f)
    
    logger.debug("bot ready")

    while True:
        await asyncio.sleep(2)
        if update_queue:
            await update_queue[0][0].send(embed=update_queue[0][1])
            update_queue.pop(0)

@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return

    msgargs = msg.content.split(' ')
    if msg.content.startswith('stalker adduser') and len(msgargs) >= 3:
        the_user = " ".join(msgargs[i] for i in range(2, len(msgargs)))
        if not str(msg.guild.id) in data:
            data[str(msg.guild.id)] = {'channel': msg.channel.id, 'users': {}}

        try:
            data[str(msg.guild.id)]['users'][the_user] = webscraper.scrape_activity('https://osu.ppy.sh/u/' + the_user)    
            await msg.channel.send("user added successfully")
        except:
            await msg.channel.send("that person does not exist (try using their uid  !!! )")

        with open('data.json', 'w') as f:
            json.dump(data, f)

    elif msg.content.startswith('stalker removeuser') and len(msgargs) >= 3:
        the_user = " ".join(msgargs[i] for i in range(2, len(msgargs)))
        if not str(msg.guild.id) in data:
            data[str(msg.guild.id)] = {'channel': msg.channel.id, 'users': {}}

        remove_key = data[str(msg.guild.id)]['users'].pop(the_user, None)

        if remove_key is None:
            await msg.channel.send("that person dont exist man")
        else:
            with open('data.json', 'w') as f:
                json.dump(data, f)
                
            await msg.channel.send("user removed from stalk list")
            
    elif msg.content.startswith('stalker setchannel') and len(msg.raw_channel_mentions) == 1:
        if nextcord.utils.get(msg.guild.text_channels, id=msg.raw_channel_mentions[0]) is None:
            await msg.channel.send("mention a text channel !")
            return

        if msg.guild.id not in data:
            data[str(msg.guild.id)] = {'channel': msg.raw_channel_mentions[0], 'users': {}}
        else:
            data[str(msg.guild.id)]['channel'] = msg.raw_channel_mentions[0]
        
        with open('data.json', 'w') as f:
            json.dump(data, f)

        await msg.channel.send("channel set successfully")
    elif msg.content == 'stalker debug':
        print(data)
    elif msg.content == 'stalker noemoji':
        config.NOEMOJI = not config.NOEMOJI
        if config.NOEMOJI:
            await msg.channel.send("emojis turned on")
        else:
            await msg.channel.send("emojis turned off")
    elif msg.content == 'fuck you potatoritos':
        embed=nextcord.Embed(title="<:beatmapupdate:994458917180559401>  Beatmap Update", description="[HoneyWorks - Akatsuki Zukuyo](https://osu.ppy.sh/s/1730403)")
        embed.set_author(name="PotatoDew", icon_url="https://a.ppy.sh/10814653?1612987577.png", url="https://osu.ppy.sh/users/10964252")
        embed.set_image(url='https://assets.ppy.sh/beatmaps/1730403/covers/cover.jpg')
        embed.timestamp = datetime.datetime.fromisoformat("2022-07-03T00:24:50+00:00")
        await msg.channel.send(embed=embed)

if __name__ == '__main__':
    activity_thread = ActivityUpdateTimer()
    activity_thread.start()
    
    bot.run(config.TOKEN)

    activity_thread.stop()
