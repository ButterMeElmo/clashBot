clashBot is a tool to help manage your clan on Clash of Clans.

Prereqs:

-nodejs

-python3

-pip

Create a virtual environment and install the requirements:

```
python3 -m pip install --user virtualenv
python3 -m virtualenv env
source env/bin/activate
python3 -m pip install -r requirements.txt
python3 setup.py develop
`````

Installation:

Currently there is some javascript used to get data from the Clash of Clans API. This requires 2 dependencies:

```
npm install --save xmlhttprequest
npm install --save clash-of-clans-api
```

Install the python dependencies:

```
pip install -r requirements.txt
```

Copy the empty db to be populated shortly:

```
cp clashData.db.empty clashData.db
```

Copy both config examples to the required names:

```
cp config_bot.json.example config_bot.json
cp config_bot.py.example config_bot.py
```

Fill in both data files with the necessary information.

In config_bot.json, the token comes from the supercell developer center api.

Everything in config_bot.py is from discord. Follow directions for creating a discord bot, you will need the token, app id, and channel ids.

On your initial setup, you need to have two sets of data.

So:

```
python3 getDataFromServer.py
python3 getDataFromServer.py
```

Then, you need to save it. There is currently an error on the first save when there is limited data, so run the save function twice.

```
python3 clashSaveData.py
python3 clashSaveData.py
```

In the future, you can just run each command once and it will work as expected :)

If you have filled out your config_bot.py, you can do:

```
python3 clashDiscordBot.py
```

And the discord bot will join and work on your server. Type !help in one of your channels to see what it can do!

To run tests:

```
python3 -m pytest -k test_add_clan_to_db_unique
```