clashBot is a tool to help manage your clan on Clash of Clans.

Prereqs:

- python3
- pip

Create a virtual environment and install the requirements:

```
python3 -m pip install --user virtualenv
python3 -m virtualenv env
source env/bin/activate
python3 -m pip install -r requirements.txt
python3 setup.py develop
`````

Installation:

Install the python dependencies:

```
pip install -r requirements.txt
```

Copy both config examples to the required names:

```
cp config_bot.py.example config_bot.py
```

Fill in config_bot.py

Everything in config_bot.py is from discord or supercell developer center. Follow directions for creating a discord bot, you will need the token, app id, and channel ids.

On your initial setup, you need to have two sets of data.

So:

```
python3 supercell_data_fetcher.py
python3 supercell_data_fetcher.py
```

Then, you need to save it.

```
python3 fetched_data_processor.py
```

If you have filled out your config_bot.py, you can do:

```
python3 discord_bot.py
```

And the discord bot will join and work on your server. Type !help in one of your channels to see what it can do!