# Detective Yellowcopyrightedrat - A Telegram bot to organize Pokémon GO raids
# Copyright (C) 2017 Jorge Suárez de Lis <hey@gentakojima.me>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import re
from datetime import datetime, timedelta
from pytz import timezone
import time
import html
import logging
from threading import Thread
import telegram
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from Levenshtein import distance
import cv2
import tempfile
import os, sys
import numpy as np
import pytesseract
from PIL import Image, ImageOps
from skimage.measure import compare_ssim as ssim
from unidecode import unidecode
import googlemaps
import math

from config import config
from telegram.error import (TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError)

pokemonlist = ['Bulbasaur','Ivysaur','Venusaur','Charmander','Charmeleon','Charizard','Squirtle','Wartortle','Blastoise','Caterpie','Metapod','Butterfree','Weedle','Kakuna','Beedrill','Pidgey','Pidgeotto','Pidgeot','Rattata','Raticate','Spearow','Fearow','Ekans','Arbok','Pikachu','Raichu','Sandshrew','Sandslash','Nidoran♀','Nidorina','Nidoqueen','Nidoran♂','Nidorino','Nidoking','Clefairy','Clefable','Vulpix','Ninetales','Jigglypuff','Wigglytuff','Zubat','Golbat','Oddish','Gloom','Vileplume','Paras','Parasect','Venonat','Venomoth','Diglett','Dugtrio','Meowth','Persian','Psyduck','Golduck','Mankey','Primeape','Growlithe','Arcanine','Poliwag','Poliwhirl','Poliwrath','Abra','Kadabra','Alakazam','Machop','Machoke','Machamp','Bellsprout','Weepinbell','Victreebel','Tentacool','Tentacruel','Geodude','Graveler','Golem','Ponyta','Rapidash','Slowpoke','Slowbro','Magnemite','Magneton','Farfetch\'d','Doduo','Dodrio','Seel','Dewgong','Grimer','Muk','Shellder','Cloyster','Gastly','Haunter','Gengar','Onix','Drowzee','Hypno','Krabby','Kingler','Voltorb','Electrode','Exeggcute','Exeggutor','Cubone','Marowak','Hitmonlee','Hitmonchan','Lickitung','Koffing','Weezing','Rhyhorn','Rhydon','Chansey','Tangela','Kangaskhan','Horsea','Seadra','Goldeen','Seaking','Staryu','Starmie','Mr.Mime','Scyther','Jynx','Electabuzz','Magmar','Pinsir','Tauros','Magikarp','Gyarados','Lapras','Ditto','Eevee','Vaporeon','Jolteon','Flareon','Porygon','Omanyte','Omastar','Kabuto','Kabutops','Aerodactyl','Snorlax','Articuno','Zapdos','Moltres','Dratini','Dragonair','Dragonite','Mewtwo','Mew','Chikorita','Bayleef','Meganium','Cyndaquil','Quilava','Typhlosion','Totodile','Croconaw','Feraligatr','Sentret','Furret','Hoothoot','Noctowl','Ledyba','Ledian','Spinarak','Ariados','Crobat','Chinchou','Lanturn','Pichu','Cleffa','Igglybuff','Togepi','Togetic','Natu','Xatu','Mareep','Flaaffy','Ampharos','Bellossom','Marill','Azumarill','Sudowoodo','Politoed','Hoppip','Skiploom','Jumpluff','Aipom','Sunkern','Sunflora','Yanma','Wooper','Quagsire','Espeon','Umbreon','Murkrow','Slowking','Misdreavus','Unown','Wobbuffet','Girafarig','Pineco','Forretress','Dunsparce','Gligar','Steelix','Snubbull','Granbull','Qwilfish','Scizor','Shuckle','Heracross','Sneasel','Teddiursa','Ursaring','Slugma','Magcargo','Swinub','Piloswine','Corsola','Remoraid','Octillery','Delibird','Mantine','Skarmory','Houndour','Houndoom','Kingdra','Phanpy','Donphan','Porygon2','Stantler','Smeargle','Tyrogue','Hitmontop','Smoochum','Elekid','Magby','Miltank','Blissey','Raikou','Entei','Suicune','Larvitar','Pupitar','Tyranitar','Lugia','Ho-Oh','Celebi','Treecko','Grovyle','Sceptile','Torchic','Combusken','Blaziken','Mudkip','Marshtomp','Swampert','Poochyena','Mightyena','Zigzagoon','Linoone','Wurmple','Silcoon','Beautifly','Cascoon','Dustox','Lotad','Lombre','Ludicolo','Seedot','Nuzleaf','Shiftry','Taillow','Swellow','Wingull','Pelipper','Ralts','Kirlia','Gardevoir','Surskit','Masquerain','Shroomish','Breloom','Slakoth','Vigoroth','Slaking','Nincada','Ninjask','Shedinja','Whismur','Loudred','Exploud','Makuhita','Hariyama','Azurill','Nosepass','Skitty','Delcatty','Sableye','Mawile','Aron','Lairon','Aggron','Meditite','Medicham','Electrike','Manectric','Plusle','Minun','Volbeat','Illumise','Roselia','Gulpin','Swalot','Carvanha','Sharpedo','Wailmer','Wailord','Numel','Camerupt','Torkoal','Spoink','Grumpig','Spinda','Trapinch','Vibrava','Flygon','Cacnea','Cacturne','Swablu','Altaria','Zangoose','Seviper','Lunatone','Solrock','Barboach','Whiscash','Corphish','Crawdaunt','Baltoy','Claydol','Lileep','Cradily','Anorith','Armaldo','Feebas','Milotic','Castform','Kecleon','Shuppet','Banette','Duskull','Dusclops','Tropius','Chimecho','Absol','Wynaut','Snorunt','Glalie','Spheal','Sealeo','Walrein','Clamperl','Huntail','Gorebyss','Relicanth','Luvdisc','Bagon','Shelgon','Salamence','Beldum','Metang','Metagross','Regirock','Regice','Registeel','Latias','Latios','Kyogre','Groudon','Rayquaza','Jirachi','Deoxys']
egglist = ['N1','N2','N3','N4','N5','EX']
iconthemes = [
    { "Rojo": "🔥", "Azul": "❄️", "Amarillo": "⚡️" },
    { "Rojo": "🔴", "Azul": "🔵", "Amarillo": "🌕" },
    { "Rojo": "❤", "Azul": "💙", "Amarillo": "💛" },
    { "Rojo": "🔴", "Azul": "🔵", "Amarillo": "🔶" },
    { "Rojo": "♨️", "Azul": "🌀", "Amarillo": "🔆" },
    { "Rojo": "🦊", "Azul": "🐳", "Amarillo": "🐥" }
]

validation_pokemons = ["chikorita", "machop", "growlithe", "diglett", "spinarak", "ditto", "teddiursa", "cubone", "sentret", "voltorb"]
validation_profiles = ["model1", "model2", "model3", "model4", "model5"]
validation_names = ["Calabaza", "Puerro", "Cebolleta", "Remolacha", "Aceituna", "Pimiento", "Zanahoria", "Tomate", "Guisante", "Coliflor", "Pepino", "Berenjena", "Perejil", "Batata", "Aguacate", "Alcaparra", "Escarola", "Lechuga", "Hinojo"]

def is_admin(chat_id, user_id, bot):
    is_admin = False
    for admin in bot.get_chat_administrators(chat_id):
      if user_id == admin.user.id:
        is_admin = True
    return is_admin

def extract_update_info(update):
    logging.debug("supportmethods:extract_update_info")
    try:
        message = update.message
    except:
        message = update.channel_post
    if message is None:
        message = update.channel_post
    text = message.text
    try:
        user_id = message.from_user.id
    except:
        user_id = None
    chat_id = message.chat.id
    chat_type = message.chat.type
    return (chat_id, chat_type, user_id, text, message)

def send_message_timed(chat_id, text, sleep_time, bot):
    logging.debug("supportmethods:send_message_timed: %s %s %s %s" % (chat_id, text, sleep_time, bot))
    time.sleep(sleep_time)
    bot.sendMessage(chat_id=chat_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)

def delete_message_timed(chat_id, message_id, sleep_time, bot):
    time.sleep(sleep_time)
    delete_message(chat_id, message_id, bot)

def delete_message(chat_id, message_id, bot):
    try:
        bot.deleteMessage(chat_id=chat_id,message_id=message_id)
        return True
    except:
        return False

def update_message(chat_id, message_id, reply_markup, bot):
    logging.debug("supportmethods:update_message: %s %s %s" % (chat_id, message_id, reply_markup))
    raid = getRaidbyMessage(chat_id, message_id)
    text = format_message(raid)
    return bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True, timeout=8)

def ensure_escaped(username):
    if username.find("_") != -1 and username.find("\\_") == -1:
        username = username.replace("_","\\_")
    return username

def extract_time(formatted_datetime, format=0):
    logging.debug("supportmethods:extract_time %s" % formatted_datetime)
    if not isinstance(formatted_datetime,str):
        formatted_datetime = formatted_datetime.strftime("%Y-%m-%d %H:%M:%S")
    m = re.search("([0-9]{1,2}):([0-9]{0,2}):[0-9]{0,2}", formatted_datetime, flags=re.IGNORECASE)
    if m is not None:
        if format == 0:
            extracted_time = "%02d:%02d" % (int(m.group(1)), int(m.group(2)))
        else:
            hour = int(m.group(1))
            if hour >=12:
                ampm = "PM"
                if hour > 12:
                    hour = hour -12
            else:
                ampm = "AM"
            extracted_time = "%d:%02d %s" % (hour, int(m.group(2)), ampm)
        logging.debug("supportmethods::extract_time extracted %s" % extracted_time)
        return extracted_time
    else:
        logging.debug("supportmethods::parse_time failed extracting time from %s" % formatted_datetime)
        return None

def extract_day(timeraid, tzone):
    try:
        raid_datetime = datetime.strptime(timeraid,"%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(tzone))
    except:
        raid_datetime = timeraid.replace(tzinfo=timezone(tzone))
    now_datetime = datetime.now(timezone(tzone))
    difftime = raid_datetime - now_datetime
    if difftime.days > 1:
        return raid_datetime.day
    else:
        return None

def raidend_is_near_raidtime(timeraid, timeend, tzone):
    try:
        raid_datetime = datetime.strptime(timeraid,"%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(tzone))
    except:
        raid_datetime = timeraid.replace(tzinfo=timezone(tzone))
    try:
        raidend_datetime = datetime.strptime(timeend,"%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(tzone))
    except:
        raidend_datetime = timeend.replace(tzinfo=timezone(tzone))
    difftime = raidend_datetime - raid_datetime
    if difftime.seconds < 780:
        return round(difftime.seconds/60)
    else:
        return -1

        
locations_sent = []

def already_sent_location(user_id, location_id):
    logging.debug("supportmethods:already_sent_location")
    global locations_sent
    k = str(user_id)+"+"+str(location_id)
    if k in locations_sent:
        return True
    else:
        locations_sent.append(k)
        return False

