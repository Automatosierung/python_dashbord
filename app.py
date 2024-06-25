import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px

# Step 1: Read the CSV file
df = pd.read_csv(r'C:\Users\Vadim.Khablov\Downloads\ExportedFiles_8692edf1-0f2f-47de-8ed6-337ee1be6f4e\new_appointments.csv')

# Convert the date columns to datetime
df['new_starttime'] = pd.to_datetime(df['new_starttime'])
df['month'] = df['new_starttime'].dt.month_name()
df['day'] = df['new_starttime'].dt.day

# Step 2: Set up the Dash app
app = dash.Dash(__name__)

# Step 3: Layout of the app
app.layout = html.Div(children=[
    html.H1(children='Dashboard'),

    html.Div(children='Select months to filter the data:'),
    
    dcc.Checklist(
        id='month-checklist',
        options=[{'label': month, 'value': month} for month in df['month'].unique()],
        value=[df['month'].unique()[0]],
        inline=True
    ),
    
    html.Div(id='total-records', style={'margin': '20px 0'}),

    dcc.Store(id='selected-anliegen', storage_type='memory'),
    dcc.Store(id='selected-servicename', storage_type='memory'),
    dcc.Store(id='selected-bezirk', storage_type='memory'),

    # Line chart at the top
    dcc.Graph(id='appointments-line-chart'),

    # Other charts in a row below the line chart
    html.Div(children=[
        dcc.Graph(id='anliegen-bar-chart', style={'width': '33%', 'display': 'inline-block'}),
        dcc.Graph(id='bezirk-pie-chart', style={'width': '33%', 'display': 'inline-block'}),
        dcc.Graph(id='servicename-bar-chart', style={'width': '33%', 'display': 'inline-block'})
    ], style={'display': 'flex', 'flex-wrap': 'wrap'})
])

# Step 4: Create callbacks to update charts based on selected months, selected anliegen, and selected servicename
@app.callback(
    [Output('total-records', 'children'),
     Output('anliegen-bar-chart', 'figure'),
     Output('bezirk-pie-chart', 'figure'),
     Output('servicename-bar-chart', 'figure'),
     Output('appointments-line-chart', 'figure')],
    [Input('month-checklist', 'value'),
     Input('selected-anliegen', 'data'),
     Input('selected-servicename', 'data'),
     Input('selected-bezirk', 'data')]
)
def update_charts(selected_months, selected_anliegen, selected_servicename, selected_bezirk):
    filtered_df = df[df['month'].isin(selected_months)]

    # Filter by selected anliegen
    if selected_anliegen:
        filtered_df = filtered_df[filtered_df['new_anliegen'] == selected_anliegen]

    # Filter by selected servicename
    if selected_servicename:
        filtered_df = filtered_df[filtered_df['new_servicename'] == selected_servicename]

    # Filter by selected bezirk
    if selected_bezirk:
        filtered_df = filtered_df[filtered_df['new_bezirk'] == selected_bezirk]

    total_records = len(filtered_df)

    # Display total number of records
    total_records_display = f'Total records for selected filters: {total_records}'

    # Calculate counts for new_anliegen and sort from highest to lowest
    anliegen_counts = filtered_df['new_anliegen'].value_counts().reset_index()
    anliegen_counts.columns = ['new_anliegen', 'count']
    anliegen_order = anliegen_counts['new_anliegen']

    # Merge counts back into filtered_df for anliegen
    filtered_df = filtered_df.merge(anliegen_counts, on='new_anliegen', how='left')

    # Calculate counts for new_servicename and sort from highest to lowest
    servicename_counts = filtered_df['new_servicename'].value_counts().reset_index()
    servicename_counts.columns = ['new_servicename', 'count']

    # Merge counts back into filtered_df for servicename
    filtered_df = filtered_df.merge(servicename_counts, on='new_servicename', how='left', suffixes=('', '_servicename_count'))

    # Calculate counts for new_bezirk and sort from highest to lowest
    bezirk_counts = filtered_df['new_bezirk'].value_counts().reset_index()
    bezirk_counts.columns = ['new_bezirk', 'count']

    # Merge counts back into filtered_df for bezirk
    filtered_df = filtered_df.merge(bezirk_counts, on='new_bezirk', how='left', suffixes=('', '_bezirk_count'))

    # Adjust text position for Anliegen
    filtered_df['text_position'] = filtered_df['count'] + 0.5

    # Customized Bar chart for new_anliegen
    anliegen_fig = px.bar(filtered_df, x='new_anliegen', y='count', title=f'New Anliegen in {", ".join(selected_months)}',
                          category_orders={'new_anliegen': anliegen_order}, text='count')
    anliegen_fig.update_traces(marker=dict(color='#DA003E', line=dict(color='black', width=1.5)),
                               texttemplate='%{text}', textposition='outside')
    anliegen_fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='black'),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
        barmode='overlay',
        height=600  # Increase the height of the chart
    )

    # Modern Pie chart for new_bezirk showing counts
    bezirk_fig = px.pie(bezirk_counts, names='new_bezirk', values='count', 
                        title=f'{len(bezirk_counts)} Bezirke ',
                        color_discrete_sequence=['#DA003E', '#FF1F57', '#FF3366', '#FF4775', '#FF5C85', '#FF7094', '#FF85A3', '#FF99B3', '#FFADC2', '#FFC2D1', '#FFD6E0'])
    bezirk_fig.update_traces(textinfo='label+value', hovertemplate='<b>%{label}</b>: %{value}', 
                             textposition='inside', textfont_size=14)

    # Modern Bar chart for new_servicename
    servicename_fig = px.bar(filtered_df, x='new_servicename', y='count_servicename_count', title=f'New Servicename in {", ".join(selected_months)}',
                             text='count_servicename_count')
    servicename_fig.update_traces(marker=dict(color='#DA003E', line=dict(color='black', width=1.5)),
                                  texttemplate='%{text}', textposition='outside')
    servicename_fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='black'),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
        barmode='overlay',
        height=600  # Increase the height of the chart
    )

    # Modern Line chart for number of appointments per day
    daily_appointments = filtered_df.groupby(['month', 'day']).size().reset_index(name='appointments')
    appointments_fig = px.line(daily_appointments, x='day', y='appointments', color='month',
                               title=f'Number of Appointments per Day in {", ".join(selected_months)}',
                               color_discrete_sequence=px.colors.qualitative.Plotly)
    appointments_fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='black'),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )
    appointments_fig.update_traces(mode='lines+markers', line_shape='spline', 
                                   marker=dict(size=8, symbol='circle', line=dict(width=1)))

    return total_records_display, anliegen_fig, bezirk_fig, servicename_fig, appointments_fig

# Callback to update the selected anliegen
@app.callback(
    Output('selected-anliegen', 'data'),
    [Input('anliegen-bar-chart', 'clickData')],
    [Input('selected-anliegen', 'data')]
)
def update_selected_anliegen(clickData, current_selection):
    if clickData:
        selected_value = clickData['points'][0]['x']
        if selected_value == current_selection:
            return None
        else:
            return selected_value
    return None

# Callback to update the selected servicename
@app.callback(
    Output('selected-servicename', 'data'),
    [Input('servicename-bar-chart', 'clickData')],
    [Input('selected-servicename', 'data')]
)
def update_selected_servicename(clickData, current_selection):
    if clickData:
        selected_value = clickData['points'][0]['x']
        if selected_value == current_selection:
            return None
        else:
            return selected_value
    return None

# Callback to update the selected bezirk
@app.callback(
    Output('selected-bezirk', 'data'),
    [Input('bezirk-pie-chart', 'clickData')],
    [Input('selected-bezirk', 'data')]
)
def update_selected_bezirk(clickData, current_selection):
    if clickData:
        selected_value = clickData['points'][0]['label']
        if selected_value == current_selection:
            return None
        else:
            return selected_value
    return None

if __name__ == '__main__':
    app.run_server(debug=True)
