#!/usr/bin/env python

import argparse
import logging as log
import mysql.connector as mariadb
import sys
from read_sensors import _TABLE_NAME
from math import ceil, floor
import plotly.express as px
import plotly.graph_objects as go
from pandas import DataFrame
from time import sleep


def down_to(x, base):
    return base * floor(x / base)


def up_to(x, base):
    return base * ceil(x / base)


_HTML_FOLDER = '/home/pi/WeatherStation/html/'


def make_temp_gauge(temp, filename, min_data=0, max_data=30):
    fig = go.Figure(go.Indicator(
        domain={'x': [0, 1], 'y': [0, 1]},
        value=temp,
        number={'valueformat': ".1f", 'suffix': "°C"},
        title={"text": "Temperature", 'font': {'size': 24}},
        mode="gauge+number",
        gauge={'axis': {'range': [min_data, max_data], 'tickformat': ".1f", 'ticksuffix': "°C"},
               'steps': [{'range': [-30, 10], 'color': 'blue'}, {'range': [10, 18], 'color': 'lightblue'},
                         {'range': [18, 23], 'color': 'green'}, {'range': [23, 27], 'color': 'orange'},
                         {'range': [27, 60], 'color': 'red'}],
               'bar': {'color': 'dimgrey'}}
    ))
    fig.update_layout(template='plotly_dark')
    fig.write_html(_HTML_FOLDER + filename, config={"displayModeBar": False, "showTips": False})


def make_hum_gauge(hum, filename):
    fig = go.Figure(go.Pie(
        values=[hum, 100-hum],
        hole=.6,
        marker={'colors': ['darkblue', 'lightblue']}
    ))
    fig.update_layout(template='plotly_dark', annotations=[{'text': f"{hum}%", 'showarrow': False, 'font_size': 24}],
                      title={"text": "Humidity", 'font': {'size': 24}, 'yanchor': 'top'},
                      showlegend=False)
    fig.update_traces(hoverinfo='percent', textinfo='none')
    fig.write_html(_HTML_FOLDER + filename, config={"displayModeBar": False, "showTips": False})


def make_co2_gauge(co2, filename, min_data=0, max_data=3000):
    fig = go.Figure(go.Indicator(
        domain={'x': [0, 1], 'y': [0, 1]},
        value=co2,
        number={'suffix': "PPM"},
        title={"text": "CO2 concentration", 'font': {'size': 24}},
        mode="gauge+number",
        gauge={'axis': {'range': [min_data, max_data], 'ticksuffix': "PPM"},
               'steps': [{'range': [0, 1000], 'color': 'green'}, {'range': [1000, 2000], 'color': 'orange'},
                         {'range': [2000, 8000], 'color': 'red'}],
               'bar': {'color': 'dimgrey'}}
    ))
    fig.update_layout(template='plotly_dark')
    fig.write_html(_HTML_FOLDER + filename, config={"displayModeBar": False, "showTips": False})


def make_plot(dates, data, title, unit, filename):
    df = DataFrame(data=[dates, data]).transpose()
    df.columns = ['Date', title]
    fig = px.line(df, x='Date', y=title, title=title, template='plotly_dark', hover_data={"Date": "|%d.%m. %H:%M"})

    fig.update_traces(hovertemplate="%{y}" + unit + " @ %{x|%d.%m. %H:%M}")
    fig.update_layout(hoverdistance=1000, hovermode='x')
    fig.update_xaxes(rangeslider={"visible": True, "bgcolor": "#0d0d0d"}, rangeselector={
        "buttons": [{"label": "all time", "step": "all"},
                    {"count": 1, "label": "year", "step": "year", "stepmode": "backward"},
                    {"count": 1, "label": "month", "step": "month", "stepmode": "backward"},
                    {"count": 7, "label": "week", "step": "day", "stepmode": "backward"},
                    {"count": 1, "label": "day", "step": "day", "stepmode": "backward"}],
        "bgcolor": "#888", "activecolor": "#444"},
                     showspikes=True, spikesnap="cursor", spikemode="across",
                     tickformatstops=[{"dtickrange": [None, 60000], "value": "%H:%M:%S"},
                                      {"dtickrange": [60000, 36000000], "value": "%H:%M\n%d.%m.%Y"},
                                      {"dtickrange": [36000000, "M1"], "value": "%d.%m.%Y"},
                                      {"dtickrange": ["M1", "M12"], "value": "%m.%Y"},
                                      {"dtickrange": ["M12", None], "value": "%Y"}])
    fig.update_yaxes(range=[down_to(min(data), 5), up_to(max(data), 5)])
    fig.write_html(_HTML_FOLDER + filename, config={"displayModeBar": False, "showTips": False})


def make_tvoc_gauge(tvoc, filename, min_data=0, max_data=1500):
    fig = go.Figure(go.Indicator(
        domain={'x': [0, 1], 'y': [0, 1]},
        value=tvoc,
        number={'suffix': "PPB"},
        title={"text": "CO2 concentration", 'font': {'size': 24}},
        mode="gauge+number",
        gauge={'axis': {'range': [min_data, max_data], 'ticksuffix': "PPB"},
               'steps': [{'range': [0, 400], 'color': 'green'}, {'range': [400, 1300], 'color': 'orange'},
                         {'range': [1300, 8000], 'color': 'red'}],
               'bar': {'color': 'dimgrey'}}
    ))
    fig.update_layout(template='plotly_dark')
    fig.write_html(_HTML_FOLDER + filename, config={"displayModeBar": False, "showTips": False})


def update_plots(cur, db_connection):
    log.info("Updating plots ...")
    cur.execute(f"SELECT time, temp, hum, co2, tvoc FROM {_TABLE_NAME} ORDER BY time ASC;")
    times, temps, hums, co2s, tvocs = zip(*cur)
    db_connection.commit()
    make_plot(times, temps, "Temperature", "°C", "temp.html")
    make_plot(times, hums, "Humidity", "%", "hum.html")
    make_plot(times, co2s, "CO2", "PPM", "co2.html")
    make_plot(times, tvocs, "TVOC", "PPB", "tvoc.html")
    make_temp_gauge(temps[-1], 'temp_gauge.html', min(int(1.1 * min(temps)), 0), int(1.1 * max(temps)))
    make_hum_gauge(hums[-1], "hum_gauge.html")
    make_co2_gauge(co2s[-1], "co2_gauge.html", max_data=ceil(1.1 * max(co2s)))
    make_tvoc_gauge(tvocs[-1], "tvoc_gauge.html", max_data=ceil(1.1 * max(tvocs)))


def main(cur, db_connection):
    cur.execute(f"SELECT MAX(id) FROM {_TABLE_NAME};")
    for row in cur:
        last_time = row[0]
    db_connection.commit()
    if not last_time:
        log.error("Last time is still None.")
    log.info(f"Last DB entry is {last_time}")
    current = last_time
    while True:
        # wait for new measurement
        while last_time == current:
            sleep(60)
            cur.execute(f"SELECT MAX(id) FROM {_TABLE_NAME};")
            for row in cur:
                current = row[0]
                log.info(f"current is {current}")
            db_connection.commit()

        update_plots(cur, db_connection)
        last_time = current


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--logfile', type=str, default='/home/pi/WeatherStation/weather_website.log', nargs='?',
                        help="Logfile")
    parser.add_argument('--loglevel', type=str, default='info', nargs='?', help="Loglevel")
    parser.add_argument('--continuous', type=bool, default=False, const=True, nargs='?',
                        help="Check sensors every 5 min and save to DB.")

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
    if not args.continuous:
        update_plots(cur, conn)
    else:
        main(cur, conn)
    conn.close()
