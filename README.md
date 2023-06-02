# **Parkour Bot**

[![](https://dcbadge.vercel.app/api/server/YKWzC9Vxxv?)](https://discord.gg/YKWzC9Vxxv)
[![Discord](https://img.shields.io/discord/793172726767550484?style=for-the-badge&color=5865F2&logo=discord&logoColor=white)](https://discord.gg/YKWzC9Vxxv)


**NOTE:** This version of parkour bot is still in relatively early development, so many of the features listed below have not yet been implemented.

**TODO:** Add pictures so its not so boring

**TODO:** Finish writing out the other stuff

## **Summary**

**Parkour Bot** is a Discord bot created using the [interactions.py](https://github.com/interactions-py/interactions.py) framework for the Minecraft Parkour Central discord server, which is the largest and most active discord server for the technical parkour community. Parkour Bot primarily handles the XP/Point/Levelling system, but also contains some games and other fun and useful features.

### **XP/Point System**
Parkour Bot's XP system is based on the completion of parkour courses and jumps. The harder a course/jump is, the more XP a user gets. These courses and jumps can be found on multiplayer servers, so that legitimate completion can be verified. When users surpass certain XP thresholds, they gain access to new perks on the discord server.

There are three types of parkour you can do to get XP. These are **Endurance**, **Onejump** and **Segmented**. In all of these types, difficulty ranges from very easy to extremely difficult to cater to players of all skill-levels.

<p align="center">
  <img src="https://cdn.discordapp.com/attachments/794260795408121926/1101495139244970004/11.png" alt="animated" height=300 style="border-radius:8px"/>
</p>

**Endurance** (also known as Rankup) is a parkour gamemode in which the player will progress through parkour that is part of a larger build. Common themes include scaled up arcades, household rooms, significant real world locations or structures, cities, and landscapes. This gamemode has no checkpoints and often contains so called "life/death" sections of parkour in which the player will lose significant progress if they fall. Endurance maps normally conclude with a "sky" section, which is life/death parkour right before the end of the map, which if failed will sometimes cause the player to fall all the way back to the start of the course.

<p align="center">
  <img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExODJkOWU2ZDI1ZmYwZjJkZDViYzYzZDBmMGM2ZGI4MmYwNzZmZjM1OSZlcD12MV9pbnRlcm5hbF9naWZzX2dpZklkJmN0PWc/jNsvVJB4Ke0oxCdecG/giphy.gif" alt="animated" height=300  style="border-radius:8px"/>
</p>

**Onejump** is a gamemode in which the player will attempt to land a single jump once. In most cases, the player will have a checkpoint set at specific coordinates at the start of the jump that they will perform a specific strategy from. The mouse movements and keyboard inputs become extremely precise and complex at the more difficult levels of this gamemode, which requires the player to have great consistency and control. The hardest of onejumps are possible by fractions of millimeters.

<p align="center">
  <img src="https://cdn.discordapp.com/attachments/794260795408121926/1101496748842688632/134.png" alt="animated"  height=300 style="border-radius:8px"/>
</p>

**Segmented** courses are much like endurance courses, but they are sectioned into smaller portions using checkpoints. As such, segmented courses rarely contain "life/death" sections. These courses are often built in hallway or tower like structures, but sometimes in builds similar to endurance courses. The style and difficulty of the parkour in segmented courses usually lies somewhere between onejump and endurance.

### **Economy System**
For each XP point a user gains, they also gain one coin (or more?) in the economy system. Coins can then be spent on the server for bounties, cosmetics, perks, etc. Perhaps users will also be able to gain coins through games and the luck system. If this happens, then they should probably gain multiple coins per xp so that fractions of coins can be avoided and smaller rewards can be given for winning games.

Could also get coins for participating in the server, every n messages or x minutes in a voice chat, etc.

This system has not yet been fully thought through, so will likely change a lot.

Make reacting to a message with a coin emoji give the person who sent it 10/100 of your coins?

Also have an economy leaderboard

The current plan:
- Bounties can be placed on jump / map completions / strat finds
    - #Bounties channel that lists all bounties in embeds. below each is a button to "Add to this bounty" Which brings up a modal where the user can enter a number of coins they want to add to it
    - Maybe allow them to be placed on other unrelated things too?
    - Any user can contribute some of their coins to a bounty, to increase the reward for whoever completes it.
    - Allow custom non-coin bounties? like nitro, irl money, hypixel rank, etc if people want to offer those things
    - Bounties may need to be approved by staff to avoid spam or just bad ones
- Users can 'purchase' role icons as a cosmetic.
    - they would be able to equip an icon with some command `/equip <icon-name>`, `/unequip`
    - This is needed because if they have all roles for the purchased icons simultaneously it would always show the one from the top role.
    - So it would give/take relevant roles when the command is used
- Maybe they can 'purchase' adding or removing an emoji

Need to think of other cosmetics.

## **Main Bot Features**
Here are the main features of the bot!

### **Minecraft Account Verification**
Parkour bot is run alongside a socket server, which mimicks the data sent and received by real Minecraft servers when a player joins them. When joined, the player is provided with a sentence which is their verification code. Inputting this code into the bot's verification command allows the bot to link a discord user with a minecraft player UUID. Once a user/player is verified, they gain the ability to participate in the XP/Point system.

Unfortunately this system is still flawed and the socket server does not consistently retrieve the players username or UUID, and will simply send an error message upon attempting to join. If you are having trouble with this, ask a staff member to manually verify you.

### **Auto-Sync**
New to this version of Parkour Bot is auto-sync. Auto-sync is a feature which sends HTTP requests to affiliated parkour servers using a RESTful API companion plugin which responds with information about the courses and jumps that players have completed. This means that Parkour Bot can automatically detect when a player has completed a new course / jump, and add it to their completed list.

### **Parkour Dictionary and FAQ**
Parkour Bot features a dictionary and FAQ system. Staff can add parkour terms, their aliases and their definition to the dictionary, which users can then search for. If a term or alias that exists in the dictionary appears in the definition for another term, it is underlined to indicate that they can also check the definition for it.

The FAQ system similarly allows staff to add and remove frequently asked questions that can then be searhed for by anyone, using a slash command.

### **Leaderboards**
Parkour Bot can send leaderboards of users based on their XP/Point score. The leaderboard can also be set to filter for one specific parkour type or one specific server.

There are also leaderboards for each game and the luck system.

### **Player Profiles**
Every user / player has three profiles. Their main profile, which contains information about the maps and jumps they've completed, and their total / divided XP. There's also their luck profile which contains information about their rank, luck points, luck score, their rarest luck and hyperlinks to each of their lucky messages.

### **Ticket System**
The ticket system is primarily for users to claim completion of maps through. However, with auto-sync it will become much less common as users will only need to claim maps that arent on servers compatible with auto sync, or maps that cant be synced properly if a server has not recorded that map as having been completed.

Tickets are also used for staff applications and event submissions.

## **Games**
Parkour Bot contains some games you can play to pass the time.

### **Minesweeper**
With parkour bot you can play a simple 5x5 version of minesweeper. When you start a game it starts with an unknown number of mines and looks like this: 

<p align="center">
  <img src="https://cdn.discordapp.com/attachments/794260795408121926/1102049980056871032/Screenshot_2023-04-30_at_11.53.03_am.png" height=300 style="border-radius:8px"/>
</p>

The first tile you choose will never contain a mine. Once you have chosen it the total number of mines will be revealed.

<p align="center">
  <img src="https://cdn.discordapp.com/attachments/794260795408121926/1102050147476713492/Screenshot_2023-04-30_at_11.53.44_am.png" height=300 style="border-radius:8px"/>
</p>

When you lose a game, all unexplored tiles will be revealed in gray, and the explored tiles will appear blue. You can click on the mine that blew you up to start a new game.

<p align="center">
  <img src="https://cdn.discordapp.com/attachments/794260795408121926/1102050448728412190/Screenshot_2023-04-30_at_11.54.57_am.png"height=300 style="border-radius:8px"/>
</p>

When you win a game, the mines you avoided will all appear green, and you can click any of them to start a new game.

<p align="center">
  <img src="https://cdn.discordapp.com/attachments/794260795408121926/1102051846757027900/Screenshot_2023-04-30_at_12.00.30_pm.png"height=300 style="border-radius:8px"/>
</p>

The Minesweeper leaderboard is based on the total number of mines avoided. It also shows what each users largest number of avoided mines in a single game was.

### **2048**
With Parkour Bot you can also play 2048. When you start a new game it looks like this: 

<p align="center">
  <img src="https://cdn.discordapp.com/attachments/794260795408121926/1102052971946188850/Screenshot_2023-04-30_at_12.04.58_pm.png"height=300 style="border-radius:8px"/>
</p>

The four arrow buttons at the bottom let you choose your next move. When two tiles of the same value collide, they combine and form a single tile of their combined value. The goal is to get the largest tile you can. To end the game at any time, press the big red "End Game" button.

Like Minesweeper, there is also a 2048 leaderboard which is ranked based on high score.

### **45 Strafe**
45

## **Other Fun Stuff**

### **Polls**

### **Lucky Messages**

### **Jump Idea Generator**

### **Spirit Animals**

### **Love Calculator**

### **Mimicking**

## **Utility Features**
Parkour Bot also contains some useful features that arent relevant to parkour.

### **Todo Lists**

### **Time Checker**

## Administrative Features
Parkour Bot contains several useful administrative features

### **Event Manager**
Parkour bot has an integrated system for managing server events. 

### **Bot Manager**

### **Logging System**

### **Staff Application Handler**

### **Master Config & Data Storage System**

### **Dynamic Help Command**
The help command should show users only the commands they have permission to perform.
