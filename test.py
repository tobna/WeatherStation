import plotly.express as px
import plotly.graph_objects as go


_HTML_FOLDER = './html/'


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


make_temp_gauge(16, 'tmp_gauge_test.html', 0, 30)
