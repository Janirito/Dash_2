import pandas as pd
from dash import Dash, html, dcc
import plotly.express as px
from datetime import datetime
import json
from urllib.request import urlopen
import plotly.graph_objs as go
with urlopen('https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json') as response:
    counties = json.load(response)

def crear_app():

    df = pd.read_excel(r'Anexo4.Covid-19_CE_15-03-23.xlsx')

    ## Ingenieria de Carcateristicas

    def depart(ica):
        if ica == 'ATLÁNTICO':
            return 'ATLANTICO'
        elif ica == 'BOGOTÁ, D.C.':
            return 'SANTAFE DE BOGOTA D.C'
        elif ica == 'BOYACÁ':
            return 'BOYACA'
        elif ica == 'CAQUETÁ' :
            return 'CAQUETA'
        elif ica == 'CHOCÓ':
            return 'CHOCO'
        elif ica == 'CÓRDOBA':
            return 'CORDOBA'
        elif ica == 'GUAINÍA':
            return 'GUAINIA'
        elif ica == 'QUINDÍO':
            return 'QUINDIO'
        elif ica == 'ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA':
            return 'ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA'
        elif ica == 'BOLÍVAR':
            return 'BOLIVAR'
        elif ica == 'VAUPÉS':
            return 'VAUPES'
        else:
            return ica
    df['DEPARTAMENTO'] = df['DEPARTAMENTO'].apply(depart)

    df['FECHA REGISTRO'] = pd.to_datetime(df['FECHA REGISTRO'].str[1:], format='%d/%m/%Y')
    df['FECHA DEFUNCIÓN'] = pd.to_datetime(df['FECHA DEFUNCIÓN'].str[1:], format='%d/%m/%Y')
    df['EDAD FALLECIDO']= df['EDAD FALLECIDO'].str.extract(r'(\d+)')

    df['Año'] = df['FECHA REGISTRO'].dt.year
    df['Mes'] = df['FECHA REGISTRO'].dt.month
    df['Año-Mes'] = df['FECHA REGISTRO'].dt.year.astype(str) + ' - ' + df['FECHA REGISTRO'].dt.month.astype(str)
    df['Muertes'] = df['FECHA DEFUNCIÓN'].apply(lambda x: 1 if pd.notna(x) else 0)

    df_2021 = df[(df['Año'] == 2021) & (df['COVID-19'] == 'CONFIRMADO')]
    df_2021_2 = df[df['Año'] == 2021]
    muertes_departamento = df_2021.groupby('DEPARTAMENTO')['Muertes'].count().reset_index()

    app = Dash()

    ## a) Mapa: número total de muertes por covid-19 confirmadas por departamento para el año 2021.

    df_map = df.groupby('DEPARTAMENTO')['Muertes'].sum().reset_index()

    locs = df_map['DEPARTAMENTO']

    for loc in counties['features']:
        loc['id'] = loc['properties']['NOMBRE_DPT']
    fig = go.Figure(go.Choroplethmapbox(
                        geojson=counties,
                        locations=locs,
                        z=df_map['Muertes'],
                        colorscale='OrRd',
                        colorbar_title="Muertes"))
    fig.update_layout(mapbox_style="carto-positron",
                            mapbox_zoom=3.4,
                            mapbox_center = {"lat": 4.570868, "lon": -74.2973328})


    ## b) Gráfico de barras horizontal: las 5 ciudades con el mayor índice de muertes por casos de covid-19 confirmados para el año 2021.

    muertes_ciudad = df_2021_2.groupby('MUNICIPIO')['Muertes'].sum().nlargest(5).reset_index()

    fig_barras = px.bar(muertes_ciudad, 
                        x='Muertes', 
                        y='MUNICIPIO', 
                        orientation='h',
                        title="Top 5 ciudades con mayor índice de muertes por COVID-19 en 2021",
                        labels={'Muertes': 'Número de muertes', 'Ciudad': 'Ciudad'})
    fig_barras.update_layout(yaxis={'categoryorder': 'total ascending'})

    ## c) Gráfico circular: total de los casos de covid-19 reportados como confirmados, sospechosos y descartados para el año 2021.

    casos_2021 = df_2021_2.groupby('COVID-19')['Muertes'].sum().reset_index()

    fig_circular = px.pie(casos_2021, 
                        values='Muertes', 
                        names='COVID-19', 
                        title="Total de casos de COVID-19 reportados en 2021",
                        labels={'Clasificación': 'Tipo de caso'})
    fig_circular.update_layout()

    ## d) Gráfico de línea: total de muertes covid-19 confirmados por mes para el año 2020 y 2021.

    data_monthly = df.groupby(['Año', 'Mes'])['Muertes'].sum().reset_index()

    fig_linea = px.line(data_monthly, 
                        x='Mes', 
                        y='Muertes', 
                        color='Año', 
                        title="Total de muertes por COVID-19 confirmadas por mes (2020 y 2021)",
                        labels={'Muertes': 'Número de muertes', 'Mes': 'Mes'})
    fig_linea.update_xaxes(type='category', categoryorder='array', categoryarray=[1,2,3,4,5,6,7,8,9,10,11,12])

    ## e) Gráfico de histograma de frecuencias de muertes covid-19 confirmados por edades quinquenales (ejemplo: 0-4, 5-9,.....,85-89, 90 o más) para el año 2020. 

    df_2020 = df[df['Año'] == 2020]
    df_2020['Edad Quinquenal'] = pd.cut(df_2020['EDAD FALLECIDO'].astype(float), 
                                        bins=[0, 4, 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59, 64, 69, 74, 79, 84, 89, 100], 
                                        labels=['0-4', '5-9', '10-14', '15-19', '20-24', '25-29', '30-34', '35-39', '40-44', 
                                                '45-49', '50-54', '55-59', '60-64', '65-69', '70-74', '75-79', '80-84', 
                                                '85-89', '90+'])

    fig_histograma = px.histogram(df_2020, 
                                x='Edad Quinquenal', 
                                y='Muertes', 
                                title="Frecuencia de muertes por COVID-19 confirmadas por edades quinquenales en 2020",
                                labels={'Muertes': 'Número de muertes', 'Edad Quinquenal': 'Rango de edad'})
    fig_histograma.update_layout(bargap=0.2)


    app.layout = html.Div(
        children=[
            html.Div(
            children=html.Img(src="ruta/de/tu_imagen.png", style={'width': '100px', 'height': 'auto'}),
            style={'position': 'absolute', 'top': '10px', 'left': '10px'}
        ),
        
        # Encabezados centrados
            html.H1(children='UNIVERSIDAD DE LA SALLE'),
            html.H2(children='Actividad 4. análisis de la mortalidad de casos de covid-19 en Colombia para el año 2020 y 2021dd.'),
            html.H3(children='Entregado a: Mcs. Cristian Duney Bermudez Quintero'),
            html.H3(children='Entregado por: Janier Hersain Rosero Urbina'),
            
            # Mapa de muertes por departamento
            dcc.Graph(id='mapa-muertes-departamento', figure=fig),

            # Gráfico de barras horizontal de las ciudades con más muertes
            dcc.Graph(id='barras-muertes-ciudad', figure=fig_barras),

            # Gráfico circular de casos confirmados, sospechosos y descartados
            dcc.Graph(id='circular-casos-tipo', figure=fig_circular),

            # Gráfico de línea de muertes por mes en 2020 y 2021
            dcc.Graph(id='linea-muertes-mes', figure=fig_linea),

            # Histograma de frecuencias de muertes por edades quinquenales
            dcc.Graph(id='histograma-muertes-edad', figure=fig_histograma),
        ],
        style={
            'textAlign': 'center',
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center',
            'alignItems': 'center',
            'height': '300vh'
        }
    )

    return app

if __name__ == '__main__':
    app = crear_app()
    app.run(debug=True)
