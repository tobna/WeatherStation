#!/usr/bin/env python

import Adafruit_DHT
import argparse
from time import time, sleep
import logging as log
import mysql.connector as mariadb
import sys

_LAST_READ = time()
_TABLE_NAME = "weather_data"


def main(temp_data_pin, db_cursor):
    global _LAST_READ
    dht22 = Adafruit_DHT.DHT22
    if time()-_LAST_READ < 2:
        sleep(2.1)
    log.info("Reading data from DHT22")
    hum, temp = Adafruit_DHT.read_retry(dht22, temp_data_pin)
    _LAST_READ = time()
    print(f"read temp={temp:.2f}°C\thum={hum:.2f}%")
    query = f"INSERT INTO {_TABLE_NAME} (temp, hum) VALUES(%s,%s)"
    db_cursor.execute(query, (temp, hum))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-pt', '--pin_temp', type=int, default=2, nargs='?',
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

    main(temp_data_pin, cur)
