#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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
#
#
# Command list for @botfather
# help - Muestra la ayuda
# register - Inicia el proceso de registro (en privado)
# raid - Crea una incursión nueva (en grupo)
# alerts - Configura alertas de incursiones (en privado)
# raids - Muestra incursiones activas (en privado)
# profile - Muestra info de tu perfil (en privado)
# stats - Muestra tus estadísticas semanales (en privado)
#

import os
import sys
import re
import time
import logging
import signal
import random
import urllib.request
from datetime import datetime
from threading import Thread

import telegram
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters
)
from telegram.ext.dispatcher import run_async
from pytz import timezone
from Levenshtein import distance

from config import config
from storagemethods import (
    saveGroup,
    getGroup,
    saveUser,
    saveWholeUser,
    getUser,
    isBanned,
    searchTimezone,
    getCurrentValidation,
    saveValidation,
    getUserByTrainername,
)

from supportmethods import (
    is_admin,
    extract_update_info,
    delete_message_timed,
    send_message_timed,
    error_callback,
    ensure_escaped,
    update_settings_message_timed,
    edit_check_private,
    delete_message,
    parse_profile_image,
    validation_pokemons,
    validation_names,
    update_validations_status
)

def cleanup(signum, frame):
    logging.info("Closing bot!")
    exit(0)


signal.signal(signal.SIGINT, cleanup)

# Logging
logdir = sys.path[0] + "/logs"

if not os.path.exists(logdir):
    os.makedirs(logdir)

logging.basicConfig(
    filename=os.path.join(logdir, 'debug.log'),
    format='%(asctime)s %(message)s', level=logging.DEBUG)
logging.info("--------------------- Starting bot! -----------------------")

updater = Updater(token=config["telegram"]["token"], workers=6)
dispatcher = updater.dispatcher
dispatcher.add_error_handler(error_callback)


@run_async
def start(bot, update):
    logging.debug("nursejoybot:start: %s %s", bot, update)
    chat_id, chat_type, user_id, text, message = extract_update_info(update)

    if chat_type != "private":
        deletion_text = "\n\n<i>(Este mensaje se borrará en 60 segundos)</i>"

        try:
            bot.deleteMessage(chat_id=chat_id, message_id=message.message_id)

        except Exception:
            pass

    else:
        deletion_text = ""

    sent_message = bot.sendMessage(
        chat_id=update.message.chat_id,
        text=(
            "📖 ¡Echa un vistazo a <a href='%s'>la ayuda</a> para enterarte de"
            " todas las funciones!\n\n🆕 <b>Crear incursión</b>\n<code>/raid "
            "Suicune 12:00 Alameda</code>\n\n❄️🔥⚡️ "
            "<b>Registrar nivel/equipo</b>\nEscríbeme por privado en @%s el "
            "comando <code>/register</code>. En vez de eso, puedes preguntar "
            "<code>quién soy?</code> a @profesoroak_bot y reenviarme su "
            "respuesta.\n\n🔔 <b>Configurar alertas</b>\nEscríbeme por privado"
            " en @%s el comando <code>/alerts</code>.%s" % (
                config["telegram"]["bothelp"],
                config["telegram"]["botalias"],
                config["telegram"]["botalias"],
                deletion_text)
        ),
        parse_mode=telegram.ParseMode.HTML,
        disable_web_page_preview=True
    )

    if chat_type != "private":
        Thread(target=delete_message_timed,
               args=(chat_id, sent_message.message_id, 40, bot)).start()


@run_async
def joyping(bot, update):
    logging.debug("nursejoybot:joyping: %s %s", bot, update)
    chat_id, chat_type, user_id, text, message = extract_update_info(update)

    sent_dt = message.date
    now_dt = datetime.now()
    timediff = now_dt - sent_dt

    if chat_type != "private":
        try:
            bot.deleteMessage(chat_id=chat_id, message_id=message.message_id)

        except Exception:
            pass

    sent_message = bot.sendMessage(
        chat_id=update.message.chat_id,
        text=(
            "¿Ves como no era para tanto el pinchazo? Fueron solo %d segundos "
            "🤗" % (timediff.seconds)
        ),
        parse_mode=telegram.ParseMode.HTML,
        disable_web_page_preview=True
    )

    if chat_type != "private":
        Thread(target=delete_message_timed,
               args=(chat_id, sent_message.message_id, 10, bot)).start()


@run_async
def register(bot, update):
    logging.debug("nursejoybot:register: %s %s", bot, update)
    chat_id, chat_type, user_id, text, message = extract_update_info(update)
    user_username = message.from_user.username

    if not edit_check_private(
            chat_id, chat_type, user_username, "register", bot):
        delete_message(chat_id, message.message_id, bot)
        return

    validation = getCurrentValidation(user_id)
    logging.debug(validation)

    if validation is not None:
        bot.sendMessage(
            chat_id=chat_id,
            text=(
                "❌ Ya has iniciado un proceso de validación. Debes completarlo"
                " antes de intentar comenzar de nuevo, o esperar 6 horas a que"
                " caduque."
            ),
            parse_mode=telegram.ParseMode.MARKDOWN
        )
        return

    user = getUser(user_id)
    if user is not None and user["validation"] != "none":
        bot.sendMessage(
            chat_id=chat_id,
            text=(
                "⚠ Ya te has validado anteriormente. *No es necesario* que "
                "vuelvas a validarte, a no ser que quieras cambiar tu nombre "
                "de entrenador, equipo o bajar de nivel. Si solo has subido de"
                " nivel, basta con que envíes una captura de pantalla de tu "
                "nuevo nivel, sin necesidad de hacer el proceso completo.\n\n"
                "Si aún así quieres, puedes continuar con el proceso, o sino "
                "*espera 6 horas* a que caduque."
            ),
            parse_mode=telegram.ParseMode.MARKDOWN
        )

    else:
        user = {"id": user_id, "username": user_username}
        saveUser(user)

    pokemon = random.choice(validation_pokemons)
    name = random.choice(validation_names)
    validation = {"usuario_id": chat_id,
                  "step": "waitingtrainername",
                  "pokemon": pokemon,
                  "pokemonname": name}
    saveValidation(validation)

    bot.sendMessage(
        chat_id=chat_id,
        text=(
            "¿Cómo es el nombre de entrenador que aparece en tu perfil del "
            "juego?\n\n_Acabas de iniciar el proceso de validación. Debes "
            "completarlo antes de 6 horas, o caducará. Si te equivocas y "
            "deseas volver a empezar, debes esperar esas 6 horas._"
        ),
        parse_mode=telegram.ParseMode.MARKDOWN
    )


@run_async
def setzone(bot, update, args=None):
    logging.debug("nursejoybot:settimezone: %s %s %s", bot, update, args)
    chat_id, chat_type, user_id, text, message = extract_update_info(update)
    chat_title = message.chat.title
    group_alias = None

    if hasattr(message.chat, 'username') and message.chat.username is not None:
        group_alias = message.chat.username

    if chat_type != "channel" and (
            not is_admin(chat_id, user_id, bot) or isBanned(user_id)):
        return

    if chat_type == "private":
        bot.sendMessage(
            chat_id=chat_id,
            text="❌ Este comando solo funciona en canales y grupos"
        )
        return

    try:
        bot.deleteMessage(
            chat_id=chat_id,
            message_id=message.message_id
        )

    except Exception:
        pass

    if args is None or len(args) != 1 or len(args[0]) < 3 or len(args[0]) > 60:
        bot.sendMessage(
            chat_id=chat_id,
            text=(
                "❌ Debes pasarme un nombre de zona horaria en inglés, por "
                "ejemplo, `America/Montevideo` o `Europe/Madrid`."
            ),
            parse_mode=telegram.ParseMode.MARKDOWN)
        return

    tz = searchTimezone(args[0])

    if tz is not None:
        group = getGroup(chat_id)
        group["timezone"] = tz["name"]
        group["title"] = chat_title
        group["alias"] = group_alias
        saveGroup(group)
        bot.sendMessage(
            chat_id=chat_id,
            text="👌 Establecida zona horaria *%s*." % group["timezone"],
            parse_mode=telegram.ParseMode.MARKDOWN
        )
        now = datetime.now(timezone(group["timezone"])).strftime("%H:%M")
        bot.sendMessage(
            chat_id=chat_id,
            text="🕒 Comprueba que la hora sea correcta: %s" % now,
            parse_mode=telegram.ParseMode.MARKDOWN)

    else:
        bot.sendMessage(
            chat_id=chat_id,
            text="❌ No se ha encontrado ninguna zona horaria válida con ese nombre.",
            parse_mode=telegram.ParseMode.MARKDOWN
        )


@run_async
def talkgroup(bot, update, args=None):
    logging.debug("nursejoybot:settalkgroup: %s %s %s", bot, update, args)
    chat_id, chat_type, user_id, text, message = extract_update_info(update)
    chat_title = message.chat.title
    group_alias = None

    if hasattr(message.chat, 'username') and message.chat.username is not None:
        group_alias = message.chat.username

    if not is_admin(chat_id, user_id, bot) or isBanned(user_id):
        return

    if chat_type == "private":
        bot.sendMessage(
            chat_id=chat_id,
            text="❌ Este comando solo funciona en canales y grupos"
        )
        return

    try:
        bot.deleteMessage(
            chat_id=chat_id,
            message_id=message.message_id
        )

    except Exception:
        pass

    if (args is None or len(args) != 1 or
        (args[0] != "-" and
         (len(args[0]) < 3 or len(args[0]) > 60 or
          re.match(
              "@?[a-zA-Z]([a-zA-Z0-9_]+)$|"
              "https://t\.me/joinchat/[a-zA-Z0-9_]+$", args[0]
          ) is None))):  # revisar - & _

        bot.sendMessage(
            chat_id=chat_id,
            text=(
                "❌ Debes pasarme por parámetro un alias de grupo o un enlace "
                "de `t.me` de un grupo privado, por ejemplo "
                "`@pokemongobadajoz` o "
                "`https://t.me/joinchat/XXXXERK2ZfB3ntXXSiWUx`."
            ),
            parse_mode=telegram.ParseMode.MARKDOWN
        )
        return

    group = getGroup(chat_id)
    group["alias"] = group_alias

    if args[0] != "-":
        group["title"] = chat_title
        group["talkgroup"] = args[0].replace("@", "")
        saveGroup(group)

        if re.match("@?[a-zA-Z]([a-zA-Z0-9_]+)$", args[0]) is not None:
            bot.sendMessage(
                chat_id=chat_id,
                text=(
                    "👌 Establecido grupo de charla a @{}.".format(
                        ensure_escaped(group["talkgroup"]))
                ),
                parse_mode=telegram.ParseMode.MARKDOWN
            )

        else:
            bot.sendMessage(
                chat_id=chat_id,
                text=(
                    "👌 Establecido grupo de charla a {}.".format(
                        ensure_escaped(group["talkgroup"]))
                ),
                parse_mode=telegram.ParseMode.MARKDOWN
            )
    else:
        group["talkgroup"] = None
        saveGroup(group)
        bot.sendMessage(
            chat_id=chat_id,
            text="👌 Eliminada la referencia al grupo de charla.",
            parse_mode=telegram.ParseMode.MARKDOWN
        )


@run_async
def setstops(bot, update, args=None):
    logging.debug("nursejoybot:setspreadsheet: %s %s %s", bot, update, args)
    chat_id, chat_type, user_id, text, message = extract_update_info(update)
    chat_title = message.chat.title
    group_alias = None

    if hasattr(message.chat, 'username') and message.chat.username is not None:
        group_alias = message.chat.username

    if chat_type == "private":
        bot.sendMessage(
            chat_id=chat_id,
            text="❌ Este comando solo funciona en canales y grupos.")
        return

    if (chat_type != "channel" and
            (not is_admin(chat_id, user_id, bot) or isBanned(user_id))):
        return

    try:
        bot.deleteMessage(chat_id=chat_id, message_id=message.message_id)

    except Exception:
        pass

    if args is None or len(args) != 1:
        bot.sendMessage(
            chat_id=chat_id,
            text=(
                "❌ Debes pasarme la URL de la Google Spreadsheet como un único "
                "parámetro."
            )
        )
        return

    m = re.search(
        'docs.google.com/.*spreadsheets/d/([a-zA-Z0-9_-]+)',
        args[0], flags=re.IGNORECASE
    )

    if m is None:
        bot.sendMessage(
            chat_id=chat_id,
            text="❌ Vaya, no he reconocido esa URL... %s" % args[0]
        )

    else:
        spreadsheet_id = m.group(1)
        group = getGroup(chat_id)

        if group is None:
            if chat_type == "channel":
                bot.sendMessage(
                    chat_id=chat_id,
                    text=(
                        "No tengo información de este canal. Un administrador "
                        "debe utilizar al menos una vez el comando `/settings`"
                        " antes de poder utilizarme en un canal. Si estaba "
                        "funcionando hasta ahora y he dejado de hacerlo, avisa"
                        " en @detectivepikachuayuda."
                    ),
                    parse_mode=telegram.ParseMode.MARKDOWN
                )

            else:
                bot.sendMessage(
                    chat_id=chat_id,
                    text=(
                        "No consigo encontrar la información de este grupo. "
                        "¿He saludado al entrar? Prueba a echarme y a meterme "
                        "de nuevo. Si lo has promocionado a supergrupo después"
                        " de entrar yo, esto es normal. Si estaba funcionando "
                        "hasta ahora y he dejado de hacerlo, avisa en "
                        "@detectivepikachuayuda."
                    ),
                    parse_mode=telegram.ParseMode.MARKDOWN
                )

            return

        group["title"] = chat_title
        group["spreadsheet"] = spreadsheet_id
        group["alias"] = group_alias
        saveGroup(group)
        bot.sendMessage(
            chat_id=chat_id,
            text=(
                "👌 Establecido hoja de cálculo con identificador `{}`.\n\n"
                "Debes usar `/refresh` ahora para hacer la carga inicial de "
                "los gimnasios y cada vez que modifiques el documento para "
                "recargarlos.".format(ensure_escaped(spreadsheet_id))
            ),
            parse_mode=telegram.ParseMode.MARKDOWN
        )

# @run_async
# def refresh(bot, update, args=None):
#   logging.debug("nursejoybot:refresh: %s %s %s" % (bot, update, args))
#   (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
#   chat_title = message.chat.title
#   group_alias = None
#   if hasattr(message.chat, 'username') and message.chat.username is not None:
#       group_alias = message.chat.username

#   if chat_type == "private":
#     bot.sendMessage(chat_id=chat_id, text="❌ Este comando solo funciona en canales y grupos.")
#     return

#   if chat_type != "channel" and (not is_admin(chat_id, user_id, bot) or isBanned(user_id)):
#     return

#   try:
#       bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
#   except:
#       pass

#   grupo = getGroup(chat_id)
#   if grupo is None or grupo["spreadsheet"] is None:
#     bot.sendMessage(chat_id=chat_id, text="❌ Debes configurar primero la hoja de cálculo de las ubicaciones con el comando `/setspreadsheet`", parse_mode=telegram.ParseMode.MARKDOWN)
#     return

#   sent_message = bot.sendMessage(chat_id=chat_id, text="🌎 Refrescando lista de gimnasios...\n\n_Si no recibes una confirmación tras unos segundos, algo ha ido mal. Este mensaje se borrará en unos segundos._", parse_mode=telegram.ParseMode.MARKDOWN)
#   Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot)).start()

#   response = requests.get("https://docs.google.com/spreadsheet/ccc?key=%s&output=csv" % grupo["spreadsheet"] )
#   if response.status_code == 200:
#     places = []
#     f = StringIO(response.content.decode('utf-8'))
#     csvreader = csv.reader(f, delimiter=',', quotechar='"')
#     counter = 0
#     incomplete_rows = []
#     for row in csvreader:
#       if counter > 3000:
#           bot.sendMessage(chat_id=chat_id, text="❌ ¡No se permiten más de 3000 gimnasios por grupo!")
#           return
#       if counter == 0 and len(row) == 0:
#           bot.sendMessage(chat_id=chat_id, text="❌ ¡No se han encontrado datos! ¿La hoja de cálculo es pública?")
#       elif len(row) < 4:
#           rownumber = counter + 1
#           bot.sendMessage(chat_id=chat_id, text="❌ ¡No se han podido cargar los gimnasios! La fila %s no tiene las 4 columnas requeridas." % rownumber)
#           return
#       names = row[3].split(",")
#       latitude = str(row[1]).replace(",",".")
#       longitude = str(row[2]).replace(",",".")
#       m = re.search('^-?[0-9]+.[0-9]+$', latitude, flags=re.IGNORECASE)
#       m2 = re.search('^-?[0-9]+.[0-9]+$', longitude, flags=re.IGNORECASE)
#       if m is None or m2 is None:
#         rownumber = counter + 1
#         bot.sendMessage(chat_id=chat_id, text="❌ ¡No se han podido cargar los gimnasios! El formato de las coordenadas en la fila %s es incorrecto. Recuerda que deben tener un único separador decimal. Si tienes problemas, elimina el formato de las celdas numéricas." % (rownumber))
#         return
#       for i,r in enumerate(names):
#         names[i] = names[i].strip()
#         if len(names[i]) < 2:
#           del names[i]
#       if len(names)==0:
#         incomplete_rows.append(counter)
#       if len(row) > 4:
#           tags = row[4].split(",")
#           for i,r in enumerate(tags):
#               tags[i] = tags[i].strip()
#       else:
#           tags = []
#       places.append({"desc":row[0],"latitude":latitude,"longitude":longitude,"names":names, "tags":tags});
#       counter = counter + 1

#     if counter > 1:
#       grupo["title"] = chat_title
#       grupo["alias"] = group_alias
#       saveGroup(grupo)
#       if savePlaces(chat_id, places):
#           places = getPlaces(grupo["id"])
#           if len(incomplete_rows) > 0:
#               bot.sendMessage(chat_id=chat_id, text="👌 ¡Cargados %i gimnasios correctamente!\n⚠️ %i gimnasios no tienen palabras clave. Recuerda que son obligatorias para que puedan ser encontrados." % (len(places), len(incomplete_rows)))
#           else:
#               bot.sendMessage(chat_id=chat_id, text="👌 ¡Cargados %i gimnasios correctamente!" % len(places))
#           # Warn users with removed alerts due to deleted/replaced gyms
#       else:
#           bot.sendMessage(chat_id=chat_id, text="❌ ¡No se han podido refrescar los gimnasios! Comprueba que no haya dos gimnasios con el mismo nombre.")
#     else:
#       bot.sendMessage(chat_id=chat_id, text="❌ ¡No se han podido cargar los gimnasios! ¿Seguro que está en el formato correcto? Ten en cuenta que para que funcione, debe haber al menos 2 gimnasios en el documento.")
#   else:
#     bot.sendMessage(chat_id=chat_id, text="❌ Error cargando la hoja de cálculo. ¿Seguro que es pública?")


@run_async
def registerOak(bot, update):
    logging.debug("nursejoybot:registerOak: %s %s", bot, update)
    chat_id, chat_type, user_id, text, message = extract_update_info(update)
    this_date = message.date
    user_username = message.from_user.username

    try:
        forward_date = message.forward_date
        forward_id = message.forward_from.id

    except Exception:
        forward_id = None
        forward_date = None

    if isBanned(user_id):
        return

    m = re.search(
        "([a-zA-Z0-9]{2,16}), eres (Rojo|Azul|Amarillo) L([0-9]{1,2})[.]",
        text, flags=re.IGNORECASE
    )

    if m is not None:
        if forward_id == 201760961:
            if (this_date - forward_date).total_seconds() < 120:
                m2 = re.search("✅", text, flags=re.IGNORECASE)

                if m2 is not None:
                    fuser = getUserByTrainername(text)

                    if fuser is None or fuser["trainername"] == m.group(1):
                        thisuser = {}
                        thisuser["id"] = user_id
                        thisuser["team"] = m.group(2)
                        thisuser["level"] = m.group(3)
                        thisuser["username"] = user_username
                        thisuser["trainername"] = m.group(1)
                        user = getUser(user_id)

                        if (user is not None and
                                user["validation"] == "internal"):
                            thisuser["validation"] = "internal"

                        else:
                            thisuser["validation"] = "oak"

                        bot.sendMessage(
                            chat_id=chat_id,
                            text=(
                                "👌 ¡De acuerdo! He reconocido que tu nombre de"
                                " entrenador es *{}*, eres del equipo *{}* y "
                                "de *nivel {}*.\n\nA partir de ahora aparecerá"
                                " tu equipo y nivel en las incursiones en las "
                                "que participes. Si subes de nivel o te "
                                "cambias el nombre de entrenador, repite esta "
                                "operación para que pueda reflejarlo bien en "
                                "las incursiones.".format(
                                    ensure_escaped(
                                        thisuser["trainername"]),
                                    thisuser["team"],
                                    thisuser["level"])
                            ),
                            parse_mode=telegram.ParseMode.MARKDOWN
                        )
                        saveWholeUser(thisuser)

                    else:
                        bot.sendMessage(
                            chat_id=chat_id,
                            text=(
                                "❌ Ese nombre de entrenador ya está asociado "
                                " a otra cuenta de Telegram. Envía un correo a"
                                " `{}` indicando tu alias en telegram y tu "
                                "nombre de entrenador en el juego para que "
                                "revisemos el caso manualmente.".format(
                                    config["telegram"]["validationsmail"])
                            ),
                            parse_mode=telegram.ParseMode.MARKDOWN
                        )
                        return

                else:
                    bot.sendMessage(
                        chat_id=chat_id,
                        text=(
                            "❌ Parece que tu cuenta aún no está completamente "
                            "validada con @profesoroak\_bot. No puedo aceptar "
                            "tu nivel y equipo hasta que te valides."
                        ),
                        parse_mode=telegram.ParseMode.MARKDOWN
                    )

            else:
                bot.sendMessage(
                    chat_id=chat_id,
                    text=(
                        "❌ Ese mensaje es demasiado antiguo. ¡Debes reenviarme"
                        " un mensaje más reciente!"
                    ),
                    parse_mode=telegram.ParseMode.MARKDOWN
                )

        else:
            bot.sendMessage(
                chat_id=chat_id,
                text=(
                    "❌ ¿Has copiado y pegado el mensaje del @profesoroak\_bot?"
                    " Tienes que usar la opción de *reenviar*, no sirve "
                    "copiando y pegando."
                ),
                parse_mode=telegram.ParseMode.MARKDOWN
            )

    else:
        if forward_id == 201760961:
            bot.sendMessage(
                chat_id=chat_id,
                text=(
                    "❌ No he reconocido ese mensaje de @profesoroak\_bot. "
                    "¿Seguro que le has preguntado `Quién soy?` y no otra "
                    "cosa?"
                ),
                parse_mode=telegram.ParseMode.MARKDOWN
            )


@run_async
def joinedChat(bot, update):
    logging.debug("nursejoybot:joinedChat: %s %s", bot, update)
    chat_id, chat_type, user_id, text, message = extract_update_info(update)

    try:
        new_chat_member = message.new_chat_member

        if (new_chat_member.username == 'nursejoybot' and
                chat_type != "private"):
            chat_title = message.chat.title
            chat_id = message.chat.id
            group = getGroup(chat_id)

            if group is None:
                saveGroup({"id": chat_id, "title": message.chat.title})

            message_text = """¡Hola a todos los miembros de *{}*!

Antes de poder utilizarme, un administrador tiene que configurar algunas cosas. Comenzad viendo la ayuda con el comando `/help` para enteraros de todas las funciones. Aseguraos de ver la *ayuda para administradores*, donde se explica en detalle todos los pasos que se deben seguir.""".format(ensure_escaped(chat_title))

            Thread(
                target=send_message_timed,
                args=(chat_id, message_text, 3, bot)
            ).start()

    except Exception:
        pass


@run_async
def processMessage(bot, update):
    chat_id, chat_type, user_id, text, message = extract_update_info(update)

    if chat_type == "channel":
        return

    if chat_type == "group" or chat_type == "supergroup":
        group = getGroup(chat_id)

        if group is None or group["babysitter"] == 0:
            logging.debug("nursejoybot:processMessage ignoring message")
            return

    user_username = message.from_user.username

    if isBanned(user_id) or isBanned(chat_id):
        return

    if chat_type == "private":
        # Are we in a validation process?
        validation = getCurrentValidation(user_id)
        user = getUser(user_id)
        if validation is not None:
            # Expecting username
            if validation["step"] == "waitingtrainername" and text is not None:
                m = re.match(r'[a-zA-Z0-9]{2,20}$', text)
                if m is not None:
                    fuser = getUserByTrainername(text)

                    if fuser is None or fuser["id"] == user["id"]:
                        validation["trainername"] = text
                        validation["step"] = "waitingscreenshot"
                        saveValidation(validation)
                        bot.sendMessage(
                            chat_id=chat_id,
                            text=(
                                "Así que tu nombre de entrenador es *{}*.\n\n"
                                "Para completar el registro, debes enviarme "
                                "una captura de pantalla de tu perfil del "
                                "juego. En la captura de pantalla debes tener "
                                "un *{}* llamado *{}* como compañero. Si no "
                                "tienes ninguno, o no te apetece cambiar ahora"
                                " de compañero, puedes volver a comenzar el "
                                "registro en cualquier otro momento.\n\n*"
                                "Recuerda que mandar imagenes que no sean de "
                                "Pokémon GO es motivo de baneo*".format(
                                    validation["trainername"],
                                    validation["pokemon"].capitalize(),
                                    validation["pokemonname"])
                            ),
                            parse_mode=telegram.ParseMode.MARKDOWN)

                    else:
                        bot.sendMessage(
                            chat_id=chat_id,
                            text=(
                                "❌ Ese nombre de entrenador ya está asociado a"
                                " otra cuenta de Telegram. Si realmente es "
                                "tuyo, entra a @enfermerajoyayuda indicando tu"
                                " alias de Telegram y tu nombre de entrenador "
                                "para que revisemos el caso manualmente.\n\nSi"
                                " lo has escrito mal y realmente no era ese el"
                                " nombre, dime entonces, ¿cómo es el nombre de"
                                " entrenador que aparece en tu perfil del "
                                "juego?"
                            ),
                            parse_mode=telegram.ParseMode.MARKDOWN
                        )
                        return
                else:
                    bot.sendMessage(
                        chat_id=chat_id,
                        text=(
                            "❌ No te entiendo. Pon únicamente el nombre de "
                            "entrenador que aparece en tu perfil del juego. No"
                            " puede tener espacios y debe tener entre 2 y 20 "
                            "caracteres de longitud."
                        ),
                        parse_mode=telegram.ParseMode.MARKDOWN
                    )
                    return

            # Expecting screenshot
            elif (validation["step"] == "waitingscreenshot" and
                      hasattr(message, 'photo') and message.photo is not None
                      and len(message.photo) > 0):

                photo = bot.get_file(update.message.photo[-1]["file_id"])
                logging.debug("Downloading file %s", photo)

                filename = os.path.join(
                    sys.path[0], "photos",
                    "profile-{}-{}-{}.jpg".format(
                        user_id, validation["id"], int(time.time())
                    )
                )

                urllib.request.urlretrieve(photo["file_path"], filename)

                try:
                    trainer_name, level, chosen_color, chosen_pokemon, \
                        pokemon_name, chosen_profile = parse_profile_image(
                            filename,
                            validation["pokemon"],
                            inspect=True,
                            inspectFilename=inspectFilename
                        )

                    # output = "Información reconocida:\n - Nombre de entrenador: %s\n - Nivel: %s\n - Equipo: %s\n - Pokémon: %s\n - Nombre del Pokémon: %s" % (trainer_name, level, chosen_color, chosen_pokemon, pokemon_name)
                    # bot.sendMessage(chat_id=chat_id, text=text,parse_mode=telegram.ParseMode.MARKDOWN)
                    output = None

                except Exception as e:
                    logging.debug("Exception validating: %s", str(e))
                    output = (
                        "❌ Ha ocurrido un error procesando la imagen. "
                        "Asegúrate de enviar una captura de pantalla completa "
                        "del juego en un teléfono móvil. No son válidas las "
                        "capturas en tablets ni otros dispositivos ni capturas"
                        " recortadas o alteradas. Puedes volver a intentarlo "
                        "enviando otra captura. Si no consigues que la "
                        "reconozca, envía un correo a `{0}` indicando tu alias "
                        "de Telegram y tu nombre de entrenador para que "
                        "revisemos el caso manualmente.".format(
                            config["telegram"]["validationsmail"])
                    )
                    bot.sendMessage(
                        chat_id=chat_id,
                        text=output,
                        parse_mode=telegram.ParseMode.MARKDOWN
                    )
                    return

                if chosen_profile is None:
                    output = (
                        "❌ La captura de pantalla no parece válida. Asegúrate "
                        "de enviar una captura de pantalla completa del juego "
                        "en un teléfono móvil. No son válidas las capturas en "
                        "tablets ni otros dispositivos ni capturas recortadas "
                        "o alteradas. Puedes volver a intentarlo enviando otra"
                        " captura. Si no consigues que la reconozca, envía un "
                        "correo a `{0}` indicando tu alias de Telegram y tu "
                        "nombre de entrenador para que revisemos el caso "
                        "manualmente."
                    )

                elif (trainer_name.lower() != validation["trainername"].lower()
                      and distance(
                          trainer_name.lower(),
                          validation["trainername"].lower()
                      ) > 2):

                    output = (
                        "❌ No he reconocido correctamente el *nombre del "
                        "entrenador*. ¿Seguro que lo has escrito bien? Puedes "
                        "volver a enviar otra captura. Si te has equivocado, "
                        "espera 6 horas a que caduque la validación y vuelve a"
                        " comenzar de nuevo. Si lo has escrito bien y no "
                        "consigues que lo reconozca, envía un correo a `{0}` "
                        "indicando tu alias de Telegram y tu nombre de "
                        "entrenador para que revisemos el caso manualmente."
                    )

                elif level is None:
                    output = (
                        "❌ No he reconocido correctamente el *nivel*. Puedes "
                        "volver a intentar completar la validación enviando "
                        "otra captura. Si no consigues que la reconozca, envía"
                        " un correo a `{0}` indicando tu alias de Telegram y "
                        "tu nombre de entrenador para que revisemos el caso "
                        "manualmente."
                    )

                elif chosen_color is None:
                    output = (
                        "❌ No he reconocido correctamente el *equipo*. Puedes "
                        "volver a intentar completar la validación enviando "
                        "otra captura. Si no consigues que la reconozca, envía"
                        "un correo a `{0}` indicando tu alias de Telegram y tu"
                        " nombre de entrenador para que revisemos el caso "
                        "manualmente."
                    )

                elif (pokemon_name.lower() != validation["pokemonname"].lower()
                      and distance(
                          pokemon_name.lower(),
                          validation["pokemonname"].lower()
                      ) > 2):

                    output = (
                        "❌ No he reconocido correctamente el *nombre del "
                        "Pokémon*. ¿Le has cambiado el nombre a *{1}* como te "
                        "dije? Puedes volver a intentar completar la "
                        "validación enviando otra captura. Si no consigues que"
                        " la reconozca, envía un correo a `{0}` indicando tu "
                        "alias de Telegram y tu nombre de entrenador para que "
                        "revisemos el caso manualmente."
                    )

                elif chosen_pokemon != validation["pokemon"]:
                    output = (
                        "❌ No he reconocido correctamente el *Pokémon*. "
                        "¿Has puesto de compañero a *{2}* como te dije? Puedes"
                        " volver a intentarlo enviando otra captura. Si no "
                        "consigues que la reconozca, al tercer intento nuestro"
                        "equipo de validadores se encargará de ello."
                    )

                if output is not None:
                    validation["tries"] = validation["tries"] + 1
                    if validation["tries"] > 3:
                        validation["step"] = "failed"

                    saveValidation(validation)
                    output.format(
                        config["telegram"]["validationsmail"],
                        validation["pokemonname"],
                        validation["pokemon"])
                    bot.sendMessage(
                        chat_id=chat_id,
                        text=output,
                        parse_mode=telegram.ParseMode.MARKDOWN
                    )
                    return

                # Validation ok!
                user["level"] = level
                user["team"] = chosen_color
                user["trainername"] = validation["trainername"]
                user["validation"] = "internal"
                saveWholeUser(user)
                validation["level"] = level
                validation["team"] = chosen_color
                validation["step"] = "completed"
                saveValidation(validation)

                output = (
                    "👌 Has completado el proceso de validación correctamente."
                    "Se te ha asignado el equipo *{0}* y el nivel *{1}*.\n\nA "
                    "partir de ahora aparecerán tu nivel y equipo reflejados "
                    "en las incursiones en las que participes.\n\nSi subes de "
                    "nivel en el juego y quieres que se refleje en tu perfil, "
                    "puedes enviarme en cualquier momento otra captura de tu "
                    "perfil del juego, no es necesario que cambies tu Pokémon "
                    "acompañante."
                )
                bot.sendMessage(
                    chat_id=chat_id,
                    text=output.format(
                        validation["team"], validation["level"]
                    ),
                    parse_mode=telegram.ParseMode.MARKDOWN
                )

            elif validation["step"] == "failed":
                output = (
                    "❌ Has excedido el número máximo de intentos para esta "
                    "validación. Nuestro equipo de validadores, se encargará "
                    "de ello"
                )

                bot.sendMessage(
                    chat_id=chat_id,
                    text=output,
                    parse_mode=telegram.ParseMode.MARKDOWN
                )
                bot.send_photo(chat_id=-1001338263961, photo=open(
                    filename, 'rb'))  # sendphoto

                # FIXME: This var names are not defined
                output = "{}, es {} nivel {} {} {}".format(
                    text_trainername, text_team, text_level,
                    text_validationstatus, text_admin)

                bot.sendMessage(
                    chat_id=-1001338263961,
                    text=output,
                    parse_mode=telegram.ParseMode.MARKDOWN
                )

        # Not expecting validation, probably screenshot to update level
        elif (user is not None and
              (user["validation"] == "internal" or user["validation"] == "oak")
              and hasattr(message, 'photo') and message.photo is not None
              and len(message.photo) > 0):

            photo = bot.get_file(update.message.photo[-1]["file_id"])
            logging.debug("Downloading file %s", photo)
            filename = os.path.join(
                sys.path[0], "photos",
                "profile-%s-updatelevel-%s.jpg" % (user_id, int(time.time()))
            )
            urllib.request.urlretrieve(photo["file_path"], filename)

            try:
                trainer_name, level, chosen_color, chosen_pokemon, \
                    pokemon_name, chosen_profile = parse_profile_image(
                        filename, None
                    )

                # output = "Información reconocida:\n - Nombre de entrenador: %s\n - Nivel: %s\n - Equipo: %s\n - Pokémon: %s\n - Nombre del Pokémon: %s" % (trainer_name, level, chosen_color, chosen_pokemon, pokemon_name)
                # bot.sendMessage(chat_id=chat_id, text=text,parse_mode=telegram.ParseMode.MARKDOWN)
                output = None

            except Exception as e:
                bot.sendMessage(
                    chat_id=chat_id,
                    text=(
                        "❌ Ha ocurrido un error procesando la imagen. "
                        "Asegúrate de enviar una captura de pantalla completa"
                        " del juego en un teléfono móvil. No son válidas las "
                        "capturas en tablets ni otros dispositivos ni capturas"
                        " recortadas o alteradas. Si no consigues que la "
                        "reconozca, entra en @enfermerajoyayuda y nuestro "
                        "equipo de administradores revisará tu caso "
                        "manualmente."
                    ),
                    parse_mode=telegram.ParseMode.MARKDOWN)
                return

            if chosen_profile is None:
                output = (
                    "❌ La captura de pantalla no parece válida. Asegúrate de "
                    "enviar una captura de pantalla completa del juego en un "
                    "teléfono móvil. No son válidas las capturas en tablets ni"
                    "otros dispositivos ni capturas recortadas o alteradas. "
                    "Puedes volver a intentarlo enviando otra captura. Si no "
                    "consigues que la reconozca, entra en @enfermerajoyayuda y"
                    " nuestro equipo de administradores revisará tu caso "
                    "manualmente."
                )

            elif (trainer_name.lower() != user["trainername"].lower() and
                  distance(
                      trainer_name.lower(),
                      user["trainername"].lower()
                  ) > 2):

                output = (
                    "❌ No he reconocido correctamente el *nombre del "
                    "entrenador*. Si no consigues que la reconozca, entra en "
                    "@enfermerajoyayuda y nuestro equipo de validadores "
                    "revisará tu caso manualmente."
                )

            elif level is None:
                output = (
                    "❌ No he reconocido correctamente el *nivel*. Si no "
                    "consigues que la reconozca, entra en @enfermerajoyayuda "
                    "y nuestro equipo de administradores revisará tu caso "
                    "manualmente."
                )

            elif int(user["level"]) == int(level):
                output = (
                    "❌ En la captura pone que eres *nivel {0}*, pero yo ya "
                    "sabía que tenías ese nivel.".format(user["level"])
                )

            elif int(user["level"]) > int(level):
                output = (
                    "❌ En la captura pone que eres *nivel {0}*, pero ya eras "
                    "*nivel {1}*. ¿Cómo has bajado de nivel?".format(
                        level, user["level"]
                    )
                )

            elif chosen_color != user["team"]:
                output = (
                    "❌ No he reconocido correctamente el *equipo*. Si no "
                    "consigues que la reconozca, entra en @enfermerajoyayuda y"
                    " nuestro equipo de administradores revisará tu caso "
                    "manualmente."
                )

                if output is not None:
                    bot.sendMessage(
                        chat_id=chat_id,
                        text=output,
                        parse_mode=telegram.ParseMode.MARKDOWN
                    )

                return

            # Validation ok!
            user["level"] = level
            saveWholeUser(user)

            output = (
                "👌 Se ha actualizado tu nivel al *{0}*.\n\nSi vuelves a subir"
                " de nivel en el juego y quieres que se refleje en tu ficha de"
                " entrenador, puedes enviarme en cualquier momento otra "
                "captura de tu perfil del juego.".format(user["level"])
            )

            bot.sendMessage(
                chat_id=chat_id,
                text=output,
                parse_mode=telegram.ParseMode.MARKDOWN
            )

        # Is this a forwarded message from Oak?
        if text is not None and len(text) > 0:
            logging.debug(text)
            registerOak(bot, update)

    else:
        if (group is not None and group["babysitter"] == 1 and
                not is_admin(chat_id, user_id, bot)):

            delete_message(chat_id, message.message_id, bot)

            if group["talkgroup"] is not None:
                if (re.match("@?[a-zA-Z]([a-zA-Z0-9_]+)$", group["talkgroup"])
                        is not None):
                    talkgroup = "@".join(ensure_escaped(group["talkgroup"]))

                else:
                    talkgroup = ensure_escaped(group["talkgroup"])

                text_talkgroup = (
                    "\n\nPara hablar puedes utilizar el grupo {}.".format(
                        talkgroup)
                )
    
            else:
                text_talkgroup = ""

            if user_username is not None:
                text = (
                    "@{} en este canal solo se pueden crear incursiones y "
                    "participar en ellas, pero no se puede hablar.{}\n\n_(Este"
                    " mensaje se borrará en unos segundos)_".format(
                        ensure_escaped(user_username), text_talkgroup
                    )
                )

            else:
                text = (
                    "En este canal solo se pueden crear incursiones y "
                    "participar en ellas, pero no se puede hablar.{}\n\n_(Este"
                    " mensaje se borrará en unos segundos)_".format(
                        text_talkgroup
                    )
                )

            sent_message = bot.sendMessage(
                chat_id=chat_id, text=text,
                parse_mode=telegram.ParseMode.MARKDOWN
            )

            Thread(
                target=delete_message_timed,
                args=(chat_id, sent_message.message_id, 13, bot)
            ).start()


@run_async
def settings(bot, update):
    logging.debug("nursejoybot:settings: %s %s", bot, update)
    chat_id, chat_type, user_id, text, message = extract_update_info(update)
    chat_title = message.chat.title

    if chat_type == "private":
        bot.sendMessage(
            chat_id=chat_id,
            text="Solo funciono en canales y grupos"
        )
        return

    if (chat_type != "channel" and
            (not is_admin(chat_id, user_id, bot) or isBanned(user_id))):

        return

    try:
        bot.deleteMessage(chat_id=chat_id, message_id=message.message_id)

    except Exception:
        pass

    group = getGroup(chat_id)

    if group is None and chat_type == "channel":
        saveGroup({"id": chat_id, "title": message.chat.title})
        group = getGroup(chat_id)

    elif group is None:
        bot.sendMessage(
            chat_id=chat_id,
            text=(
                "No consigo encontrar la información de este grupo. ¿He "
                "saludado al entrar? Prueba a echarme y a meterme de nuevo. Si"
                " lo has promocionado a supergrupo después de entrar yo, esto "
                "es normal. Si estaba funcionando hasta ahora y he dejado de "
                "hacerlo, avisa en @nursejoyhelp."
            ),
            parse_mode=telegram.ParseMode.MARKDOWN
        )
        return

    if group["settings_message"] is not None:
        try:
            bot.deleteMessage(
                chat_id=chat_id, message_id=group["settings_message"]
            )

        except Exception:
            pass

    group_alias = None

    if hasattr(message.chat, 'username') and message.chat.username is not None:
        group_alias = message.chat.username

    group["alias"] = group_alias
    group["title"] = chat_title

    message = bot.sendMessage(
        chat_id=chat_id,
        text="Cargando preferencias del grupo. Un momento..."
    )
    group["settings_message"] = message.message_id
    saveGroup(group)
    Thread(
        target=update_settings_message_timed,
        args=(chat_id, 1, bot)
    ).start()


@run_async
def profile(bot, update):  # add admin and me 👩‍⚕️👨‍⚕️
    logging.debug("nursejoybot:profile: %s %s", bot, update)
    chat_id, chat_type, user_id, text, message = extract_update_info(update)
    user_username = message.from_user.username

    if isBanned(chat_id):
        return

    if not edit_check_private(chat_id, chat_type, user_username, "profile", bot):
        delete_message(chat_id, message.message_id, bot)
        return

    user = getUser(chat_id)

    if user is not None:
        text_alias = ("*%s*" % user["username"]) if user["username"] is not None else "_Desconocido_"
        text_trainername = ("*%s*" % user["trainername"]) if user["trainername"] is not None else "_Desconocido_"
        text_team = ("*%s*" % user["team"]) if user["team"] is not None else "_Desconocido_"
        text_level = ("*%s*" % user["level"]) if user["level"] is not None else "_Desconocido_"

        if user["banned"] == "1":
            text_validationstatus = "⛔️"

        elif user["validation"] == "internal" or user["validation"] == "oak":
            text_validationstatus = "✅"

        else:
            text_validationstatus = "⚠️"

        if user["admin"] == "1": 
            text_admin = "👩‍⚕️"

        output = "%s, eres %s nivel %s %s %s" % (text_trainername, text_team, text_level, text_validationstatus, text_admin)

    else:
        output = "❌ No tengo información sobre ti."

    bot.sendMessage(
        chat_id=user_id,
        text=output,
        parse_mode=telegram.ParseMode.MARKDOWN
    )


# Basic and register commands
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('joyping', joyping))
dispatcher.add_handler(CommandHandler('help', start))
dispatcher.add_handler(CommandHandler('register', register))
dispatcher.add_handler(CommandHandler('profile', profile))
dispatcher.add_handler(CommandHandler('verdurita', verdurita))
# Admin commands
dispatcher.add_handler(CommandHandler('setstops', setstops, pass_args=True))
dispatcher.add_handler(CommandHandler('settzone', setzone, pass_args=True))
dispatcher.add_handler(CommandHandler('talkgroup', talkgroup, pass_args=True))
#dispatcher.add_handler(CommandHandler('refresh', refresh))
dispatcher.add_handler(CommandHandler('settings', settings))
# Channel support and unknown commands
# Text and welcome message
dispatcher.add_handler(MessageHandler(Filters.text | Filters.photo | Filters.voice | Filters.sticker | Filters.audio | Filters.video | Filters.contact, processMessage))
dispatcher.add_handler(MessageHandler(Filters.status_update, joinedChat))


j = updater.job_queue


def callback_update_validations_status(bot, job):
    Thread(target=update_validations_status, args=(bot,)).start()


job1 = j.run_repeating(callback_update_validations_status, interval=60, first=18)

updater.start_polling()

exit(0)
