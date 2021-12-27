#!/usr/bin/env python

from matplotlib import pyplot as plt
from matplotlib import dates
import mpld3
import argparse
import logging as log
import mysql.connector as mariadb
import sys
from read_sensors import _TABLE_NAME


_HTML_FOLDER = '/home/pi/WeatherStation/html/'


def make_plot(dates, data, title, ylabel, filename):
    fig = plt.figure()
    plt.plot(dates, data)
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel(ylabel)
    html_str = mpld3.fig_to_html(fig)
    with open(_HTML_FOLDER + filename, 'w+') as f:
        f.write(html_str)


def main(cur):
    cur.execute(f"SELECT time, temp, hum FROM {_TABLE_NAME};")
    times, temps, hums = zip(*cur)
    make_plot(times, temps, "Temperature", "Temperature [°C]", "temp.html")
    make_plot(times, hums, "Humidity", "Humidity [%]", "hum.html")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-pt', '--pin_temp', type=int, default=4, nargs='?',
                        help="GPIO pin number for data of DHT22 sensor")
    parser.add_argument('--logfile', type=str, default='/home/pi/WeatherStation/weather_website.log', nargs='?',
                        help="Logfile")
    parser.add_argument('--loglevel', type=str, default='info', nargs='?', help="Loglevel")

    args = parser.parse_args()

    logfile = args.logfile
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
    main(cur)
    conn.close()
