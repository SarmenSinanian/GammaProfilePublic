import pandas as pd
import numpy as np
import scipy
from scipy.stats import norm
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from datetime import datetime, timedelta, date
import base64
import io

pd.options.display.float_format = '{:,.4f}'.format

app = dash.Dash(__name__)

app.layout = html.Div(
    children=[
        html.H1('Spot Gamma Exposure Analysis'),

        dcc.Upload(
            id='upload-csv',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select CSV File')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            },
            multiple=False
        ),

        html.Div(id='output-csv-upload'),

        html.Div(children='Select Start Date:'),
        dcc.Dropdown(
            id='start-date-dropdown',
        ),

        html.Div(children='Select End Date:'),
        dcc.Dropdown(
            id='end-date-dropdown',
        ),

        dcc.Store(id='df-store'),
        dcc.Store(id='spot-price-store'),

        html.Div(id='output')
    ]
)


@app.callback(
    Output('output-csv-upload', 'children'),
    Output('start-date-dropdown', 'options'),
    Output('start-date-dropdown', 'value'),
    Output('end-date-dropdown', 'options'),
    Output('end-date-dropdown', 'value'),
    Output('df-store', 'data'),
    Output('spot-price-store', 'data'),
    Input('upload-csv', 'contents'),
    State('upload-csv', 'filename')
)
def upload_csv(contents, filename):
    spotPrice = None
    if contents is not None:
        content_type, content_string = contents.split(',')

        decoded = base64.b64decode(content_string)

        if 'csv' in filename:
            # optionsFileData = io.StringIO(decoded.decode('utf-8')).readlines()
            
            # This assumes the CBOE file format hasn't been edited, i.e. table begins at line 4
            # optionsFile = open(filename)
            # optionsFileData = optionsFile.readlines()
            # optionsFile.close()
            optionsFileData = io.StringIO(decoded.decode('utf-8')).readlines()

            # Get SPX Spot
            spotLine = optionsFileData[1]
            spotPrice = float(spotLine.split('Last:')[1].split(',')[0])

            # Get Today's Date
            dateLine = optionsFileData[2]
            todayDate = dateLine.split('Date: ')[1].split(',')
            monthDay = todayDate[0].split(' ')

            # Handling of US/EU date formats
            if len(monthDay) == 2:
                year = int(todayDate[0].split()[1])
                month = monthDay[0]
                day = int(monthDay[1])
            else:
                year = int(monthDay[2])
                month = monthDay[1]
                day = int(monthDay[0])

            todayDate = datetime.strptime(month, '%B')
            todayDate = todayDate.replace(day=day, year=year)

            # Get SPX Options Data
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=",", header=None, skiprows=4)
            df.columns = ['ExpirationDate', 'Calls', 'CallLastSale', 'CallNet', 'CallBid', 'CallAsk', 'CallVol',
                          'CallIV', 'CallDelta', 'CallGamma', 'CallOpenInt', 'StrikePrice', 'Puts', 'PutLastSale',
                          'PutNet', 'PutBid', 'PutAsk', 'PutVol', 'PutIV', 'PutDelta', 'PutGamma', 'PutOpenInt']

            df['ExpirationDate'] = pd.to_datetime(df['ExpirationDate'], format='%a %b %d %Y')
            df['ExpirationDate'] = df['ExpirationDate'] + timedelta(hours=16)
            df['StrikePrice'] = df['StrikePrice'].astype(float)
            df['CallIV'] = df['CallIV'].astype(float)
            df['PutIV'] = df['PutIV'].astype(float)
            df['CallGamma'] = df['CallGamma'].astype(float)
            df['PutGamma'] = df['PutGamma'].astype(float)
            df['CallOpenInt'] = df['CallOpenInt'].astype(float)
            df['PutOpenInt'] = df['PutOpenInt'].astype(float)

            df_json = df.to_json(date_format='iso', orient='split')

            unique_dates = df['ExpirationDate'].dt.date.unique()
            unique_dates = sorted(unique_dates)

            options = [{'label': str(date), 'value': str(date)} for date in unique_dates]

            return f'Successfully loaded {filename}', options, str(unique_dates[0]), options, str(unique_dates[1]), df_json, spotPrice

    return None, [], None, [], None, None, None  # Return None for data when no CSV file uploaded


@app.callback(
    Output('output', 'children'),
    Input('start-date-dropdown', 'value'),
    Input('end-date-dropdown', 'value'),
    Input('df-store', 'data'),
    Input('spot-price-store', 'data')
)
def update_graph(start_date, end_date, df_json, spotPrice):
    if start_date is None or end_date is None or df_json is None:
        return []
    df = pd.read_json(df_json, orient='split')  # Convert JSON data to DataFrame
    df['ExpirationDate'] = pd.to_datetime(df['ExpirationDate'])
    # Filter the data based on selected dates. 
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    filtered_df = df.loc[(df['ExpirationDate'].dt.date >= start_date) & (df['ExpirationDate'].dt.date <= end_date)].copy()

    # Calculate gamma exposure for each option
    filtered_df.loc[:, 'CallGEX'] = filtered_df['CallGamma'] * filtered_df['CallOpenInt'] * 100 * spotPrice * spotPrice * 0.01
    filtered_df.loc[:, 'PutGEX'] = filtered_df['PutGamma'] * filtered_df['PutOpenInt'] * 100 * spotPrice * spotPrice * 0.01 * -1

    filtered_df.loc[:, 'TotalGamma'] = (filtered_df['CallGEX'] + filtered_df['PutGEX']) / 10**9

    # Exclude datetime64 columns from grouping and summing
    numeric_columns = filtered_df.select_dtypes(include=[np.number]).columns
    dfAgg = filtered_df.groupby(['StrikePrice'])[numeric_columns].sum()
    strikes = dfAgg.index.values

    # Chart 1: Absolute Gamma Exposure
    data1 = go.Bar(
        x=strikes,
        y=dfAgg['TotalGamma'].to_numpy(),
        width=6,
        marker=dict(
            line=dict(
                color='black',
                width=0.1
            )
        ),
        name='Gamma Exposure'
    )

    layout1 = go.Layout(
        title="Total Gamma: $" + str("{:.2f}".format(filtered_df['TotalGamma'].sum())) + " Bn per 1% SPX Move",
        xaxis=dict(
            title='Strike',
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            title='Spot Gamma Exposure ($ billions/1% move)',
            showgrid=True,
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        annotations=[
            dict(
                x=spotPrice,
                y=filtered_df['TotalGamma'].sum() * 0.5,
                xref="x",
                yref="y",
                text="SPX Spot: " + str("{:,.0f}".format(spotPrice)),
                showarrow=True,
                arrowhead=7,
                ax=0,
                ay=-40
            ),
            dict(
                x=strikes.min(),
                y=filtered_df['TotalGamma'].sum() * 0.45,
                xref="x",
                yref="y",
                text="Beginning of Window: " + str(start_date),
                showarrow=False,
                font=dict(
                    size=10,
                    color="gray"
                )
            ),
            dict(
                x=strikes.max(),
                y=filtered_df['TotalGamma'].sum() * 0.45,
                xref="x",
                yref="y",
                text="End of Window: " + str(end_date),
                showarrow=False,
                font=dict(
                    size=10,
                    color="gray"
                )
            )
        ]
    )

    fig1 = go.Figure(data=[data1], layout=layout1)

    # Chart 2: Absolute Gamma Exposure by Calls and Puts
    data2 = [
        go.Bar(
            x=strikes,
            y=dfAgg['CallGEX'].to_numpy() / 10**9,
            width=6,
            marker=dict(
                line=dict(
                    color='black',
                    width=0.1
                )
            ),
            name='Call Gamma'
        ),
        go.Bar(
            x=strikes,
            y=dfAgg['PutGEX'].to_numpy() / 10**9,
            width=6,
            marker=dict(
                line=dict(
                    color='black',
                    width=0.1
                )
            ),
            name='Put Gamma'
        )
    ]

    layout2 = go.Layout(
        title="Total Gamma: $" + str("{:.2f}".format(filtered_df['TotalGamma'].sum())) + " Bn per 1% SPX Move",
        xaxis=dict(
            title='Strike',
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            title='Spot Gamma Exposure ($ billions/1% move)',
            showgrid=True,
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        annotations=[
            dict(
                x=spotPrice,
                y=filtered_df['TotalGamma'].sum() * 0.5,
                xref="x",
                yref="y",
                text="SPX Spot: " + str("{:,.0f}".format(spotPrice)),
                showarrow=True,
                arrowhead=7,
                ax=0,
                ay=-40
            )
        ],
        barmode='group'
    )

    fig2 = go.Figure(data=data2, layout=layout2)

    return [
        dcc.Graph(
            id='gamma-exposure-chart1',
            figure=fig1
        ),

        dcc.Graph(
            id='gamma-exposure-chart2',
            figure=fig2
        )
    ]


if __name__ == '__main__':
    app.run_server(debug=True)
