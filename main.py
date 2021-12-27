#!/usr/bin/env python

import Adafruit_DHT
import adafruit_ccs811
import busio
import board
import argparse
from time import time, sleep
import logging as log
import mysql.connector as mariadb
import sys

_LAST_READ = time()
_TABLE_NAME = "weather_data"


def add_to_db(temp, hum, db_cursor, bd_connection):
    query = f"INSERT INTO {_TABLE_NAME} (temp, hum) VALUES(%s,%s)"
    db_cursor.execute(query, (temp, hum))
    if db_cursor.lastrowid:
        log.info(f"Added enrty with id {db_cursor.lastrowid}")
    else:
        log.warning("Last insert id not found.")
    bd_connection.commit()


def read_dht22(temp_data_pin):
    global _LAST_READ
    dht22 = Adafruit_DHT.DHT22
    if time() - _LAST_READ < 2:
        sleep(2.1)
    log.info("Reading data from DHT22")
    Adafruit_DHT.read_retry(dht22, temp_data_pin)
    sleep(2.1)
    hum, tmp = Adafruit_DHT.read_retry(dht22, temp_data_pin)
    _LAST_READ = time()
    return tmp, hum


def read_ccs811():
    i2c_bus = busio.I2C(board.SCL, board.SDA)
    ccs811 = adafruit_ccs811.CCS811(i2c_bus)
    first = True
    while not ccs811.data_ready:
        if first:
            print("Waiting for data.", end='')
            first = False
        else:
            print(".", end='')
        sleep(0.5)
    if not first:
        print("")
    co2 = ccs811.eco2
    tvoc = ccs811.tvoc
    return tvoc, co2


def main(temp_data_pin, db_cursor, bd_connection):
    tvoc, co2 = read_ccs811()
    print(f"ccs811: co2={co2:.2f}PPM\ttvoc={tvoc:.2f}PPM")

    tmp, hum = read_dht22(temp_data_pin)

    print(f"read temp={tmp:.2f}°C\thum={hum:.2f}%")
    add_to_db(tmp, hum, db_cursor, bd_connection)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-pt', '--pin_temp', type=int, default=4, nargs='?',
                        help="GPIO pin number for data of DHT22 sensor")
    parser.add_argument('--logfile', type=str, default='weather.log', nargs='?', help="Logfile")
    parser.add_argument('--loglevel', type=str, default='info', nargs='?', help="Loglevel")
    parser.add_argument('--force_new_table', type=bool, default=False, const=True, nargs='?',
                        help="Create a new Table in DB")
    parser.add_argument('--dump_table', type=bool, default=False, const=True, nargs='?',
                        help="Dump table data to console on startup")
    args = parser.parse_args()
    temp_data_pin = args.pin_temp
    logfile = args.logfile
    level_map = {'info': log.INFO, 'debug': log.DEBUG, 'warning': log.WARNING, 'error': log.ERROR}
    loglevel = level_map[args.loglevel.lower()]
    log.basicConfig(filename=logfile, encoding='utf-8', level=loglevel,
                    format='%(asctime)s; %(levelname)s: \t%(message)s', datefmt='%d.%m.%Y %H:%M:%S')
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
                "PRIMARY KEY (id)"
                ");")

    main(temp_data_pin, cur, conn)
