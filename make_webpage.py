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


def make_plot(dates, data, title, unit, filename):
    fig = plt.figure()
    l, = plt.plot(dates, data, label=[f"{date}; {datum} {unit}" for date, datum in zip(dates, data)])
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel(f"{title} [{unit}]")

    annot = plt.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points",
                         bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
    annot.set_visible(False)

    def hover(event):
        vis = annot.get_visible()
        cont, ind = l.contains(event)
        idx = ind['ind'][0]
        if cont:
            posx, posy = [l.get_xdata()[idx], l.get_ydata()[idx]]
            annot.xy = (posx, posy)
            text = f'{l.get_label()}: {posx:.2f}-{posy:.2f}'
            annot.set_text(text)
            # annot.get_bbox_patch().set_facecolor(cmap(norm(c[ind["ind"][0]])))
            annot.get_bbox_patch().set_alpha(0.4)
            annot.set_visible(True)
            fig.canvas.draw_idle()
        else:
            if vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()
    fig.canvas.mpl_connect("motion_notify_event", hover)

    html_str = mpld3.fig_to_html(fig)
    with open(_HTML_FOLDER + filename, 'w+') as f:
        f.write(html_str)


def main(cur):
    cur.execute(f"SELECT time, temp, hum FROM {_TABLE_NAME};")
    times, temps, hums = zip(*cur)
    make_plot(times, temps, "Temperature", "°C", "temp.html")
    make_plot(times, hums, "Humidity", "%", "hum.html")


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
