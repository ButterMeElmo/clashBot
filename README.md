Installation:

Currently there is some javascript used to get data from the Clash of Clans API. This requires 2 dependencies:

npm install --save xmlhttprequest
npm install --save clash-of-clans-api

Copy the empty db to be populated shortly:

cp clashData.db.empty clashData.db

Copy both config examples to the required names:

cp config_bot.json.example config_bot.json
cp config_bot.py.example config_bot.py

Fill in both data files with the necessary information.

In config_bot.json, the token comes from the supercell developer center api.

Everything in config_bot.py is from discord.

On your initial setup, you need to have two sets of data.

So:

python3 getDataFromServer.py
python3 getDataFromServer.py

Then, you need to save it. There is currently an error on the first save when there is limited data, so run the save function twice.

python3 clashSaveData.py
python3 clashSaveData.py

In the future, you can just run each command once and it will work as expected :)

Also, if you run python3 clashDiscordBot the bot will join your server, where you can interact with it.
