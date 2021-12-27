#!/usr/bin/env python

import Adafruit_DHT
import adafruit_ccs811
import busio
import board
import argparse
from time import sleep
from datetime import datetime
import logging as log
import mysql.connector as mariadb
import sys

_TABLE_NAME = "weather_data"


def add_to_db(temp, hum, co2, tvoc, db_cursor, db_connection):
    query = f"INSERT INTO {_TABLE_NAME} (temp, hum, co2, tvoc) VALUES(%s,%s,%s,%s)"
    db_cursor.execute(query, (temp, hum, co2, tvoc))
    if db_cursor.lastrowid:
        log.info(f"Added entry with id {db_cursor.lastrowid}")
    else:
        log.warning("Last insert id not found.")
    db_connection.commit()


def read_dht22(temp_data_pin):
    dht22 = Adafruit_DHT.DHT22
    Adafruit_DHT.read_retry(dht22, temp_data_pin)
    sleep(2.5)
    hum, tmp = Adafruit_DHT.read_retry(dht22, temp_data_pin)
    return tmp, hum


def read_ccs811():
    try:
        i2c_bus = busio.I2C(board.SCL, board.SDA)
        ccs811 = adafruit_ccs811.CCS811(i2c_bus)
    except IOError as err:
        log.error(f"Got IOError: {e}")
        exit(-1)
    while not ccs811.data_ready:
        sleep(1)
    co2 = ccs811.eco2
    tvoc = ccs811.tvoc
    return tvoc, co2


def once(temp_data_pin, db_cursor, db_connection, p=False):
    tvoc, co2 = read_ccs811()
    tmp, hum = read_dht22(temp_data_pin)
    if p:
        print(f"temp={tmp}°C\thum={hum}%\tco2={co2}PPM\ttvoc={tvoc}PPB")
    add_to_db(tmp, hum, co2, tvoc, db_cursor, db_connection)


def main(temp_data_pin, db_cursor, db_connection, p=False):
    once(temp_data_pin, db_cursor, db_connection, p)
    sleep(20)
    log.info("Starting main loop.")
    while True:
        now = datetime.now()
        s_to_next_five = max([(now.minute % 5) * 60 - now.second, 0])
        sleep(s_to_next_five)
        once(temp_data_pin, db_cursor, db_connection, False)
        sleep(60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-pt', '--pin_temp', type=int, default=4, nargs='?',
                        help="GPIO pin number for data of DHT22 sensor")
    parser.add_argument('--logfile', type=str, default='/home/pi/WeatherStation/weather.log', nargs='?', help="Logfile")
    parser.add_argument('--loglevel', type=str, default='info', nargs='?', help="Loglevel")
    parser.add_argument('--force_new_table', type=bool, default=False, const=True, nargs='?',
                        help="Create a new Table in DB")
    parser.add_argument('--dump_table', type=bool, default=False, const=True, nargs='?',
                        help="Dump table data to console on startup")
    parser.add_argument('-p', '--print', type=bool, default=False, const=True, nargs='?',
                        help="Print sensor vals to console")
    parser.add_argument('--continuous', type=bool, default=False, const=True, nargs='?',
                        help="Check sensors every 5 min and save to DB.")

    args = parser.parse_args()

    temp_data_pin = args.pin_temp
    logfile = args.logfile
    print_vals = args.print
    level_map = {'info': log.INFO, 'debug': log.DEBUG, 'warning': log.WARNING, 'error': log.ERROR}
    loglevel = level_map[args.loglevel.lower()]
    log.basicConfig(filename=logfile, encoding='utf-8', level=loglevel,
                    format='%(asctime)s; %(levelname)s: \t%(message)s', datefmt='%d.%m.%Y %H:%M:%S')
    log.info("Initializing DB connection")
    try:
        conn = mariadb.connect(
            user="WeatherAgent",
            password="wetterDbP/W",
            host="localhost",
            port=3306,
            database="weather"
        )
    except mariadb.Error as e:
        log.error(f"Error connecting to MariaDB: {e}")
        sys.exit(-1)
    cur = conn.cursor()

    if args.dump_table:
        cur.execute(f"SELECT * FROM {_TABLE_NAME};")
        has_print = False
        for row in cur:
            has_print = True
            print(row)
        if not has_print:
            print(f"No data in table {_TABLE_NAME}")

    if args.force_new_table:
        log.warning("Resetting the Database. All data will be lost!")
        cur.execute(f"DROP TABLE IF EXISTS {_TABLE_NAME};")

    cur.execute(f"CREATE TABLE IF NOT EXISTS {_TABLE_NAME}("
                "id INT AUTO_INCREMENT,"
                "time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
                "temp FLOAT NOT NULL,"
                "hum FLOAT NOT NULL,"
                "co2 INT NOT NULL,"
                "tvoc INT NOT NULL,"
                "PRIMARY KEY (id)"
                ");")

    if not args.continuous:
        once(temp_data_pin, cur, conn, p=print_vals)
    else:
        main(temp_data_pin, cur, conn, p=print_vals)
    conn.close()
