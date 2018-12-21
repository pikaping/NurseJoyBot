# -*- coding: utf-8 -*-
#
# NurseJoyBot - A Telegram bot to manage Pokémon GO groups
# Copyright (C) 2018 Marc Rodriguez Garcia <marc@qwert1.es>
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
# Based on Detective Yellowcopyrightedrat
# Copyright (C) 2017 Jorge Suárez de Lis <hey@gentakojima.me>


import json
import logging
import pymysql.cursors
from pymysql.err import IntegrityError
from datetime import datetime, timedelta
from pytz import timezone
from tzlocal import get_localzone
import threading
from config import config


def getDbConnection():
    try:
        globaldb = pymysql.connect(host=config["database"]["host"], user=config["database"]["user"], password=config["database"]["password"], db=config["database"]["schema"], charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
        logging.debug("Connected to database from thread %s " % threading.get_ident())

    except:
        print("No se puede conectar a la base de datos.\nComprueba el fichero de configuración!")
        logging.debug("Can't connect to database!")

    return globaldb

# dbconnections = []
    # def getDbConnection():
    #     global dbconnections
    #     for i in range(0,len(dbconnections)):
    #         if dbconnections[i]["thread_id"] == threading.get_ident():
    #             try:
    #                 logging.debug("DATABASE: Trying to reuse connection from thread %s " % threading.get_ident())
    #                 dbconnections[i]["c"].ping()
    #                 return dbconnections[i]["c"]
    #             except:
    #                 logging.debug("DATABASE: Reconnecting from thread %s " % threading.get_ident())
    #                 dbconnections[i]["c"] = pymysql.connect(host=config["database"]["host"], user=config["database"]["user"], password=config["database"]["password"], db=config["database"]["schema"], charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
    #                 return dbconnections[i]["c"]
    #     try:
    #         logging.debug("DATABASE: Creating new database connection from thread %s " % threading.get_ident())
    #         conn = pymysql.connect(host=config["database"]["host"], user=config["database"]["user"], password=config["database"]["password"], db=config["database"]["schema"], charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
    #         dbconnections.append({"thread_id": threading.get_ident(), "c": conn})
    #     except:
    #         print("No se puede conectar a la base de datos.\nComprueba el fichero de configuración!")
    #         logging.debug("Can't connect to database!")
    #     return conn

def searchTimezone(tz):
    db = getDbConnection()
    logging.debug("storagemethods:searchTimezone: %s" % (tz))
    with db.cursor() as cursor:
        sql = "SELECT `Name` as `name` FROM `mysql`.`time_zone_name` WHERE Name NOT LIKE %s AND Name NOT LIKE %s AND Name LIKE %s"
        cursor.execute(sql, ("posix%", "right%", "%"+tz+"%"))
        result = cursor.fetchone()

    db.close()
    return result

def saveGroup(group):
    db = getDbConnection()
    logging.debug("storagemethods:saveSpreadsheet: %s" % (group))
    if "timezone" not in group.keys():
        group["timezone"] = "Europe/Madrid"
    for k in ["settings_message","spreadsheet","talkgroup","alias"]:
        if k not in group.keys():
            group[k] = None
    for k in ["disaggregated","latebutton","refloat","gotitbuttons","gymcommand","babysitter","timeformat","listorder","icontheme","refloatauto","validationrequired","plusdisaggregated","plusdisaggregatedinline"]:
        if k not in group.keys():
            group[k] = 0
    for k in ["alerts","candelete","locations","raidcommand","snail"]:
        if k not in group.keys():
            group[k] = 1
    if "plusmax" not in group.keys():
        group["plusmax"] = 5

    with db.cursor() as cursor:
        sql = "INSERT INTO grupos (id, title, alias, spreadsheet) VALUES (%s, %s, %s, %s) \
        ON DUPLICATE KEY UPDATE title = %s, alias = %s, spreadsheet = %s, settings_message = %s, alerts = %s, disaggregated = %s, latebutton = %s, refloat = %s, candelete = %s, gotitbuttons = %s, locations = %s, gymcommand = %s, raidcommand = %s, babysitter = %s, timezone = %s, talkgroup = %s, timeformat = %s, listorder = %s, snail = %s, icontheme = %s, plusmax = %s, plusdisaggregated = %s, plusdisaggregatedinline = %s, refloatauto = %s, validationrequired = %s;"
        cursor.execute(sql, (group["id"], group["title"], group["alias"], group["spreadsheet"], group["title"], group["alias"], group["spreadsheet"], group["settings_message"], group["alerts"], group["disaggregated"], group["latebutton"], group["refloat"], group["candelete"], group["gotitbuttons"], group["locations"], group["gymcommand"], group["raidcommand"], group["babysitter"], group["timezone"], group["talkgroup"], group["timeformat"], group["listorder"], group["snail"], group["icontheme"], group["plusmax"], group["plusdisaggregated"], group["plusdisaggregatedinline"], group["refloatauto"], group["validationrequired"]))
    db.commit()
    db.close()

def getGroup(group_id, reconnect=True):
    db = getDbConnection()
    logging.debug("storagemethods:getGroup: %s" % (group_id))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`title`,`alias`,`spreadsheet`,`testgroup`,`alerts`,`disaggregated`,`settings_message`,`latebutton`,`refloat`,`candelete`,`gotitbuttons`, `locations`, `gymcommand`, `raidcommand`, `babysitter`, `timeformat`, `listorder`, `snail`, `talkgroup`, `icontheme`, `timezone`, `plusmax`, `plusdisaggregated`, `plusdisaggregatedinline`, `refloatauto`, `validationrequired` FROM `grupos` WHERE `id`=%s"
        try:
            cursor.execute(sql, (group_id))
            result = cursor.fetchone()
        except:
            if reconnect:
                logging.info("storagemethods:getGroup Error interfacing with the database! Trying to reconnect...")
                result = getGroup(group_id, False)
            else:
                logging.info("storagemethods:getGroup Error interfacing with the database but already tried to reconnect!")
                raise
    db.close()
    return result

def getGroupsByUser(user_id):
    db = getDbConnection()
    logging.debug("storagemethods:getGroupsByUser: %s" % (user_id))
    with db.cursor() as cursor:
        sql = "SELECT `grupos`.`id` as `id`, `title`, `alias`, `spreadsheet`, `testgroup`, `alerts`, `disaggregated`, `latebutton`, `refloat`, `candelete`, `gotitbuttons`, `locations`, `gymcommand`, `raidcommand`, `babysitter`, `timeformat`, `listorder`, `snail`, `talkgroup`, `icontheme`, `timezone`, `plusmax`, `plusdisaggregated`, `plusdisaggregatedinline`, `refloatauto`, `validationrequired` FROM `grupos` \
        LEFT JOIN incursiones ON incursiones.grupo_id = grupos.id \
        RIGHT JOIN voy ON voy.incursion_id = incursiones.id \
        WHERE voy.usuario_id = %s \
        AND voy.addedtime>(DATE_SUB(NOW(),INTERVAL 1 MONTH)) \
		GROUP BY grupos.id"
        cursor.execute(sql, (user_id))
        result = cursor.fetchall()
    db.close()
    return result

def getValidationsByUser(user_id):
    db = getDbConnection()
    logging.debug("storagemethods:getValidationsByUser: %s" % (user_id))
    with db.cursor() as cursor:
        sql = "SELECT `id`, `startedtime`, `step`, `tries`, `pokemon`, `pokemonname`, `usuario_id` FROM `validaciones` \
        WHERE validaciones.usuario_id = %s"
        cursor.execute(sql, (user_id))
        result = cursor.fetchall()
    db.close()
    return result

def getCurrentValidation(user_id):
    db = getDbConnection()
    logging.debug("storagemethods:getCurrentValidation: %s" % (user_id))
    with db.cursor() as cursor:
        sql = "SELECT `id`, `startedtime`, `step`, `tries`, `pokemon`, `pokemonname`, `usuario_id`, `trainername`, `team`, `level` FROM `validaciones` \
        WHERE `validaciones`.`usuario_id` = %s AND (`step` = 'waitingtrainername' OR `step` = 'waitingscreenshot' OR `step` = 'failed')"
        cursor.execute(sql, (user_id))
        result = cursor.fetchone()
    db.close()
    return result

def saveValidation(validation):
    db = getDbConnection()
    logging.debug("storagemethods:saveValidation: %s" % (validation))
    for k in ["id","trainername","team","level"]:
        if k not in validation.keys():
            validation[k] = None
    for k in ["tries"]:
        if k not in validation.keys():
            validation[k] = 0
    with db.cursor() as cursor:
        sql = "INSERT INTO validaciones (id, pokemon, pokemonname, usuario_id) VALUES (%s, %s, %s, %s) \
        ON DUPLICATE KEY UPDATE trainername = %s, step = %s, tries = %s, team = %s, level = %s;"
        cursor.execute(sql, (validation["id"], validation["pokemon"], validation["pokemonname"], validation["usuario_id"], validation["trainername"], validation["step"], validation["tries"], validation["team"], validation["level"]))
    db.commit()
    db.close()
    return True

def getGroupTimezoneOffsetFromServer(group_id):
    db = getDbConnection()
    logging.debug("storagemethods:getGroupTimezoneOffsetFromServer: %s" % (group_id))
    with db.cursor() as cursor:
        sql = "SELECT timezone FROM grupos WHERE id = %s"
        cursor.execute(sql, (group_id))
        result = cursor.fetchone()
        if result is None:
            logging.debug("storagemethods:getGroupTimezoneOffsetFromServer: Unknown offset")
            return 0
        else:
            localtz = get_localzone()
            grouptz = result["timezone"]
            localtz_datetime = datetime.now(timezone(str(localtz)))
            grouptz_datetime = datetime.now(timezone(str(grouptz)))
            localtz_datetime = localtz_datetime.replace(tzinfo=timezone("UTC"))
            grouptz_datetime = grouptz_datetime.replace(tzinfo=timezone("UTC"))
            if grouptz_datetime > localtz_datetime:
                difference = grouptz_datetime - localtz_datetime
                seconds = difference.seconds
            else:
                difference = localtz_datetime - grouptz_datetime
                seconds = -difference.seconds
            offset = round(seconds/3600.0)
            logging.debug("storagemethods:getGroupTimezoneOffsetFromServer: Offset %s" % offset)
            return offset

def savePlaces(group_id, places):
    db = getDbConnection()
    logging.debug("storagemethods:savePlaces: %s %s" % (group_id, places))
    with db.cursor() as cursor:
        params_vars = []
        params_replacements = [group_id]
        for place in places:
            params_vars.append("%s")
            params_replacements.append(place["desc"])
        sql = "UPDATE incursiones SET gimnasio_id=NULL WHERE grupo_id=%s AND gimnasio_text NOT IN ("+(",".join(params_vars))+")"
        cursor.execute(sql, params_replacements)
        sql = "DELETE alertas, gimnasios FROM gimnasios LEFT JOIN alertas ON alertas.gimnasio_id = gimnasios.id WHERE gimnasios.grupo_id=%s AND gimnasios.name NOT IN ("+(",".join(params_vars))+")"
        cursor.execute(sql, params_replacements)
        for place in places:
            if "tags" not in place.keys():
                place["tags"] = {}
            try:
                sql = "INSERT INTO gimnasios (grupo_id,name,latitude,longitude,keywords,tags) \
                VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE latitude=%s, longitude=%s, keywords=%s, tags=%s;"
                cursor.execute(sql, (group_id, place["desc"], place["latitude"], place["longitude"], json.dumps(place["names"]), json.dumps(place["tags"]), place["latitude"], place["longitude"], json.dumps(place["names"]), json.dumps(place["tags"])))
            except IntegrityError:
                db.rollback()
                db.close()
                return False
    db.commit()
    db.close()
    return True

def getPlaces(group_id, ordering="name"):
    db = getDbConnection()
    logging.debug("storagemethods:getPlaces: %s" % (group_id))
    gyms = []
    with db.cursor() as cursor:
        sql = "SELECT `id`,`name`,`latitude`,`longitude`,`keywords`,`tags`,`address` FROM `gimnasios` WHERE `grupo_id`=%s"
        if ordering == "name":
            sql = sql + " ORDER BY name"
        elif ordering == "id":
            sql = sql + " ORDER BY id"
        cursor.execute(sql, (group_id))
        for row in cursor:
            if row["tags"] is None:
                row["tags"] = "[]"
            gyms.append({"id":row["id"], "desc":row["name"], "latitude":row["latitude"], "longitude":row["longitude"], "names":json.loads(row["keywords"]), "tags":json.loads(row["tags"]), "address":row["address"]})
    db.close()
    return gyms

def getPlace(id):
    db = getDbConnection()
    logging.debug("storagemethods:getPlace: %s" % (id))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`name`,`grupo_id`,`latitude`,`longitude`,`keywords`,`tags`,`address` FROM `gimnasios` WHERE `id`=%s"
        cursor.execute(sql, (id))
        for row in cursor:
            if row["tags"] is None:
                row["tags"] = "[]"
            db.close()
            return {"id":row["id"], "group_id":row["grupo_id"], "desc":row["name"], "latitude":row["latitude"], "longitude":row["longitude"], "names":json.loads(row["keywords"]), "tags":json.loads(row["tags"]), "address":row["address"]}
        db.close()
        return None

def savePlace(place):
    db = getDbConnection()
    logging.debug("storagemethods:savePlace: %s" % (place["id"]))
    with db.cursor() as cursor:
        sql = "UPDATE `gimnasios` SET `address`=%s WHERE `id`=%s"
        cursor.execute(sql, (place["address"], place["id"]))
    db.commit()
    db.close()

def getPlacesByLocation(latitude, longitude, distance=100):
    db = getDbConnection()
    logging.debug("storagemethods:getPlacesByLocation: %s %s %s" % (latitude, longitude, distance))
    d = float(distance)/50000.0
    with db.cursor() as cursor:
        sql = "SELECT `id`,`grupo_id`,`latitude`,`longitude`,`name` FROM `gimnasios` WHERE `latitude`> %s AND `latitude` < %s AND `longitude` > %s and `longitude` < %s"
        cursor.execute(sql, (float(latitude)-d,float(latitude)+d,float(longitude)-d,float(longitude)+d))
        result = cursor.fetchall()
    db.close()
    return result

def saveWholeUser(user):
    db = getDbConnection()
    logging.debug("storagemethods:saveWholeUser: %s" % (user))
    with db.cursor() as cursor:
        sql = "INSERT INTO usuarios (id,level,team,username) VALUES (%s, %s, %s, %s) \
        ON DUPLICATE KEY UPDATE level=%s, team=%s, username=%s, banned=%s, trainername=%s, validation=%s;"
        if "validation" not in user.keys():
            user["validation"] = "none"
        if "banned" not in user.keys():
            user["banned"] = 0
        for k in ["trainername","username","team","level"]:
            if k not in user.keys():
                user[k] = None
        cursor.execute(sql, (user["id"], user["level"], user["team"], user["username"], user["level"], user["team"], user["username"], user["banned"], user["trainername"], user["validation"]))
    db.commit()
    db.close()

def saveUser(user):
    db = getDbConnection()
    logging.debug("storagemethods:saveUser: %s" % (user))
    with db.cursor() as cursor:
        sql = "INSERT INTO usuarios (id,username) VALUES (%s, %s) \
        ON DUPLICATE KEY UPDATE username=%s;"
        if "username" not in user.keys():
            user["username"] = None
        cursor.execute(sql, (user["id"], user["username"], user["username"]))
    db.commit()
    db.close()

def refreshUsername(user_id, username):
    db = getDbConnection()
    logging.debug("storagemethods:refreshUsername: %s %s" % (user_id, username))
    thisuser = getUser(user_id)
    if thisuser is None:
        thisuser = {}
        thisuser["id"] = user_id
        thisuser["validation"] = "none"
    if username is not None and username != "None":
        thisuser["username"] = username
    saveUser(thisuser)
    return thisuser

def getUser(user_id, reconnect=True):
    db = getDbConnection()
    logging.debug("storagemethods:getUser: %s" % (user_id))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`level`,`team`,`username`,`banned`,`validation`,`trainername` FROM `usuarios` WHERE `id`=%s"
        try:
            cursor.execute(sql, (user_id))
            result = cursor.fetchone()
        except:
            if reconnect:
                logging.info("storagemethods:getUser Error interfacing with the database! Trying to reconnect...")
                result = getUser(user_id, False)
            else:
                logging.info("storagemethods:getUser Error interfacing with the database but already tried to reconnect!")
                raise
    db.close()
    return result

def getUserByTrainername(trainername, reconnect=True):
    db = getDbConnection()
    logging.debug("storagemethods:getUserByTrainername: %s" % (trainername))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`level`,`team`,`username`,`banned`,`validation`,`trainername` FROM `usuarios` WHERE `trainername`=%s"
        try:
            cursor.execute(sql, (trainername))
            result = cursor.fetchone()
        except:
            if reconnect:
                logging.info("storagemethods:getUser Error interfacing with the database! Trying to reconnect...")
                getDbConnection()
                result = getUserByTrainername(trainername, False)
            else:
                logging.info("storagemethods:getUser Error interfacing with the database but already tried to reconnect!")
                raise
    db.close()
    return result

def isBanned(user_id):
    db = getDbConnection()
    logging.debug("storagemethods:isBanned: %s" % (user_id))
    with db.cursor() as cursor:
        sql = "SELECT `id` FROM `usuarios` WHERE `id`=%s AND banned=1 UNION SELECT `id` FROM `grupos` WHERE `id`=%s AND banned=1"
        cursor.execute(sql, (user_id, user_id))
        result = cursor.fetchone()
        if result is None:
            db.close()
            return False
        else:
            logging.debug("storagemethods:isBanned: Found banned ID %s" % user_id)
            db.close()
            return True
'''
def itsMe(user_id):
    db = getDbConnection()
    logging.debug("storagemethods:isBanned: %s" % (user_id))
    with db.cursor() as cursor:
        sql = "SELECT `id` FROM `usuarios` WHERE `id`=%s AND me=1"
        cursor.execute(sql, (user_id, user_id))
        result = cursor.fetchone()
        if result is None:
            db.close()
            return False
        else:
            logging.debug("storagemethods:itsMe: Found creator ID %s" % user_id)
            db.close()
            return True
'''
#def raidLotengo(grupo_id, message_id, user_id):
    #    db = getDbConnection()
    #    logging.debug("storagemethods:raidLotengo: %s %s %s" % (grupo_id, message_id, user_id))
    #    with db.cursor() as cursor:
    #        raid = getRaidbyMessage(grupo_id, message_id)
    #        if raid is None:
    #            db.close()
    #            return "not_raid"
    #        if raid is None or raid["status"] == "waiting" or raid["status"] == "old":
    #            db.close()
    #            return "old_raid"
    #        sql = "SELECT `novoy` FROM `voy` WHERE `incursion_id`=%s AND `usuario_id`=%s and novoy = 1"
    #        cursor.execute(sql, (raid["id"],user_id))
    #        result = cursor.fetchone()
    #        if result is not None:
    #            db.close()
    #            return "not_going"
    #        sql = "SELECT `plus` FROM `voy` WHERE `incursion_id`=%s AND `usuario_id`=%s"
    #        cursor.execute(sql, (raid["id"],user_id))
    #        result = cursor.fetchone()
    #        if (result is None and raid["status"] == "started") or result is not None:
    #            sql = "INSERT INTO voy (incursion_id, usuario_id, estoy, lotengo) VALUES (%s, %s, 1, 1) ON DUPLICATE KEY UPDATE tarde=0, estoy=1, novoy=0, lotengo=1;"
    #            rows_affected = cursor.execute(sql, (raid["id"], user_id))
    #        else:
    #            db.close()
    #            return "not_now"
    #    db.commit()
    #    db.close()
    #    if rows_affected > 0:
    #        return True
    #    else:
    #        return "no_changes"

def updateValidationsStatus():
    db = getDbConnection()
    logging.debug("storagemethods:updateValidationsStatus")
    validationstoupdate = []
    try:
        with db.cursor() as cursor:
            sql = "SELECT * FROM `validaciones` WHERE (step = 'waitingtrainername' OR step = 'waitingscreenshot' OR step = 'failed') and startedtime < timestamp(DATE_SUB(NOW(), INTERVAL 6 HOUR)) LIMIT 0,2000"
            cursor.execute(sql)
            results = cursor.fetchall()
            for r in results:
                logging.debug(r)
                try:
                    logging.debug("storagemethods:updateValidationsStatus marking validation %s as expired" % (r["id"]))
                    sql = "UPDATE validaciones SET `step`='expired' WHERE id=%s;"
                    cursor.execute(sql, (r["id"]))
                    validationstoupdate.append(r)
                except Exception as e:
                    logging.debug("supportmethods:updateValidationsStatus error: %s" % str(e))
    except Exception as e:
        logging.debug("supportmethods:updateValidationsStatus error: %s" % str(e))
    db.commit()
    db.close()
    return validationstoupdate

