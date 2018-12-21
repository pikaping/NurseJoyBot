#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

import configparser
from os.path import expanduser
import os

configdir = expanduser("~") + "/.config/detectivepikachu"
configfile = configdir + "/config.ini"

if not os.path.exists(configdir):
    os.makedirs(configdir)

if not os.path.exists(configfile):
    with open(configfile, "w") as f:
        f.write("""[database]
host=localhost
port=3306
user=###
password=###
schema=nursejoy
[telegram]
token=###
botalias=nursejoybot
bothelp=#
validationsmail=###
[googlemaps]
key=###""")

    print("Se acaba de crear el fichero de configuración en «{}».\nComprueba"
          " la configuración y vuelve a ejecutarme.".format(configfile))
    exit(0)


config = configparser.ConfigParser()
config.read(configfile)
