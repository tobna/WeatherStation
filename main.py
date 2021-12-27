import Adafruit_DHT
import argparse
from time import time, sleep
import logging as log
import mysql.connector as mariadb
import sys

_LAST_READ = time()


def main(temp_data_pin):
    global _LAST_READ
    dht22 = Adafruit_DHT.DHT22
    if time()-_LAST_READ < 2:
        sleep(2.1)
    log.info("Reading data from DHT22")
    hum, temp = Adafruit_DHT.read_retry(dht22, temp_data_pin)
    _LAST_READ = time()
    print(f"read temp={temp}°C\thum={hum}%")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-pt', '--pin_temp', type=int, default=2, nargs='?',
                        help="GPIO pin number for data of DHT22 sensor")
    parser.add_argument('--logfile', type=str, default='weather.log', nargs='?', help="Logfile")
    parser.add_argument('--loglevel', type=str, default='info', nargs='?', help="Loglevel")
    parser.add_argument('--force_new_table', type=bool, default=False, const=True, nargs='?',
                        help="Create a new Table in DB")
    args = parser.parse_args()
    temp_data_pin = args.pin_temp
    logfile = args.logfile
    level_map = {'info': log.INFO, 'debug': log.DEBUG, 'warning': log.WARNING, 'error': log.ERROR}
    loglevel = level_map[args.loglevel.lower()]
    log.basicConfig(filename=logfile, encoding='utf-8', level=loglevel,
                    format='%(asctime)s; %(levelname)s: \t%(message)s', datefmt='%d.%m.%Y %H:%M:%S')
    try:
        conn = mariadb.connect(
            user="pi",
            # password="wetterBbP/W",
            host="localhost",
            port=3306,
            database="weather"
        )
    except mariadb.Error as e:
        log.error(f"Error connecting to MariaDB: {e}")
        sys.exit(-1)
    cur = conn.cursor()

    if args.force_new_table:
        pass

    main(temp_data_pin)
