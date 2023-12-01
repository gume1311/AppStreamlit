import streamlit as st
import requests
from fpdf import FPDF
import base64
import matplotlib.pyplot as plt
import pandas as pd
import io
import pydeck as pdk 





st.title('Buscador de Información de Negocios y Evaluación de la Competencia')

def map_viz(latitude,longitude): ##FUNCION DE MAPA
    st.title("Visualización de Coordenadas en Mapa")
    view_state = pdk.ViewState(
        latitude=latitude,
        longitude=longitude,
        zoom=12,
        pitch=0,
    )

    layer = pdk.Layer(
        'ScatterplotLayer',
        data={
            'type': 'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [latitude, longitude]
                },
            }],
        },        
        get_position=[longitude, latitude],
        get_radius=70,
        get_fill_color=[255, 0, 0],
        pickable=True,
        filled=True,
    )

    map = pdk.Deck(
        map_style='mapbox://styles/mapbox/streets-v11',
        initial_view_state=view_state,
        layers=[layer],
    )

    st.pydeck_chart(map)



business_name = st.text_input('Nombre del Negocio')
latitude = st.text_input('Latitud')
longitude = st.text_input('Longitud')

radius = st.number_input('Radio de búsqueda (en metros)', min_value=100, max_value=5000, value=1000, key='radius')
search_button = st.button('Buscar')

if search_button:
    # First, find the specified business
    response = requests.get(
        f'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={business_name}&inputtype=textquery&fields=place_id&locationbias=point:{latitude},{longitude}&key=AIzaSyDf1RiWMDUr6FjxdfNKp6gZNJLcGx_lRHU'
    )
    business_info = response.json()


    if business_info.get('candidates'):
        place_id = business_info['candidates'][0]['place_id']

        # Get details of the specified business
        details_response = requests.get(
            f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,rating,user_ratings_total,types,reviews&key=AIzaSyDf1RiWMDUr6FjxdfNKp6gZNJLcGx_lRHU'
        )
        details_info = details_response.json()

        if details_info.get('result'):
            info = details_info['result']
            business_types = info.get('types', [])
            business_type = st.selectbox('Tipo de Negocio', options=business_types, key='business_type')
            #radius = st.number_input('Radio de búsqueda (en metros)', min_value=100, max_value=5000, value=1000, key='radius')  # Default value is 1000m
            info_queried_business = [info.get('name'),info.get('rating'),info.get('user_ratings_total'),info.get('price_level')] #informacion of the business

            # Display business information
            st.write(f"Nombre: {info.get('name', 'N/A')}")
            #
            st.write(f"Tipo de lugar: {', '.join(business_types)}")
            st.write(f"Puntuación: {info.get('rating', 'N/A')} (0-5)")
            stars = "\u2605"
            printstar=""
            ratin=float(info_queried_business[1])
            for i in range(0,round(ratin)):
                printstar=printstar+stars+" "
            st.write(f" {printstar}")
            st.write(f"Número de reseñas: {info.get('user_ratings_total', 'N/A')}")
            ###################
            
            ###################


            # Now, find other similar businesses nearby
            nearby_response = requests.get(
                f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius={radius}&type={business_type}&key=AIzaSyDf1RiWMDUr6FjxdfNKp6gZNJLcGx_lRHU'
            )
            nearby_info = nearby_response.json()

            if nearby_info.get('results'):
                st.write(f"Negocios similares encontrados: {len(nearby_info['results'])-1}")

                # Collecting names and ratings of nearby businesses for comparison
                businesses = []
                ratings = []
                price_level = []
                total_ratings = []
                for nearby_business in nearby_info['results']:
                    business_name = nearby_business.get('name', 'N/A')
                    business_rating = nearby_business.get('rating', 'N/A')
                    total_ratings.append(nearby_business.get('user_ratings_total')) #added
                    price_level.append(nearby_business.get('price_level'))          #added
                    businesses.append(business_name)
                    ratings.append(business_rating)
                    st.write(f"- {business_name}, Puntuación: {business_rating} (0-5)")
                
                businesses.append(info_queried_business[0]),ratings.append(info_queried_business[1]),price_level.append(info_queried_business[3]),total_ratings.append(info_queried_business[2])

               # print(f'{price_level}\n\n') #test of list print, it is visible in the command line when executing a query
              #  print(total_ratings)

                def define_colors(businesses): #function to change color of the queried business, to highlight it
                    return ['red' if business == info_queried_business[0] else 'blue' for business in businesses]
                
                # Creating a DataFrame for easier plotting
                df = pd.DataFrame({'Business': businesses, 'Rating': ratings,'Price_Level': price_level, 'Total_Ratings': total_ratings})

                # Convert the 'Rating' column to numeric, setting errors='coerce' to handle any conversion issues
                df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
                df['Price_Level'] = pd.to_numeric(df['Price_Level'], errors='coerce')
                df['Total_Ratings'] = pd.to_numeric(df['Total_Ratings'], errors='coerce')
                
                #para desactivar el warning en la visualizacion
                st.set_option('deprecation.showPyplotGlobalUse', False)
                # Creating the bar chart
                df = df.sort_values(by='Rating', ascending=False) #IMPORTANT order of plot
                colors = define_colors(df['Business'])

                #Comparación de rating
                def create_plot1(df, colors):
                    plt.figure(figsize=(10,6))
                    plt.barh(df['Business'], df['Rating'], color = colors)
                    plt.title('Comparativa de Puntuaciones')
                    plt.xlabel('Numero de estrellas')
                #plt.ylabel('Puntuación (0-5)')
                    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
                    #st.pyplot()  # Display the plot in Streamlit

                #Comparación de precios (solo restaurantes)
                def create_plot2(df, colors):
                    if 'restaurant' in business_types:
                        plt.figure()
                        df = df.sort_values(by='Price_Level', ascending=False)
                        plt.figure(figsize=(10,6))
                        colors = define_colors(df['Business'])
                        plt.barh(df['Business'], df['Price_Level'],color = colors)
                        plt.title('Comparativa de niveles de precio')
                        plt.xlabel('Nivel de costo (0-3)')
                    # plt.xlabel('Negocios')
                    # plt.ylabel('Nivel de costo (0-3)')
                        plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
                        #st.pyplot()  # Display the plot in Streamlit

                #Comparación popularidad
                def create_plot3(df, colors):
                    plt.figure()
                    df = df.sort_values(by='Total_Ratings', ascending=False)
                    plt.figure(figsize=(10,6))
                    colors = define_colors(df['Business'])
                    plt.barh(df['Business'], df['Total_Ratings'], color = colors)
                    plt.title('Numero total de usuarios que han calificado los negocios (popularidad)')
                    #plt.xlabel('Negocios')
                    #plt.ylabel('Numero total')
                    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
                    #st.pyplot()  # Display the plot in Streamlit
                
                create_plot1(df, colors)
                st.pyplot()
                if 'restaurant' in business_types:
                    create_plot2(df, colors)
                    st.pyplot()
                create_plot3(df, colors)
                st.pyplot()
                map_viz((float(latitude)),float(longitude)) ##AQUI ESTA LA FUNCION DEL MAPA
                ################################################
      

                def save_matplotlib_plot_as_image(df, create_plot, filename):
                    colors = define_colors(df['Business'])
                    r=create_plot(df, colors)
                    # Save the plot as a PNG image
                    plot_buffer = io.BytesIO()
                    plt.savefig(plot_buffer, format='png')
                    plt.close()
                    # Save the plot to a file
                    with open(filename, 'wb') as file:
                       return file.write(plot_buffer.getvalue())
                    

                

                def create_pdf_report(business_name, info_queried_business):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font('Arial', 'B', 16)
                    # Title
                    pdf.cell(200, 10, txt=f'Reporte', ln=True, align='C')
                    pdf.ln(10)  # Move down 10 units

                    # Business Info
                    pdf.set_font('Arial', '', 12)
                    pdf.multi_cell(0, 10, txt=f"Nombre del Negocio: {info_queried_business[0]}")
                    #TEST
                    pdf.multi_cell(0, 10, txt=f"Puntuación: {info_queried_business[1]}")
                

                    pdf.multi_cell(0, 10, txt=f"Número de Reseñas: {info_queried_business[2]}")
                    pdf.multi_cell(0, 10, txt=f"Tipo de lugar: {', '.join(business_types)}")
                    
                    # Columnas de comparación
                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(60, 10, "Name", border=1, align="C")
                    pdf.cell(30, 10, "Rating", border=1, align="C")
                    pdf.cell(30, 10, "Price Level", border=1, align="C")
                    pdf.cell(30, 10, "Total Ratings", border=1, align="C")
                    pdf.ln()

                    pdf.set_font('Arial', '', 8)
                    for i in range(0, len(businesses)):
                        pdf.cell(60, 10, txt=f"{businesses[i]}", border=1,align="C")
                        pdf.cell(30, 10, txt=f" {ratings[i]}",border=0,align="C")
                        pdf.cell(30, 10, txt=f" {price_level[i]}",border=0,align="C")
                        pdf.cell(30, 10, txt=f" {total_ratings[i]}",border=0,align="C")
                        pdf.ln()

                    pdf.ln(10)  # Move down 10 units
             

                    # Gráficas
                    pdf.add_page()
                    pdf.set_font('Arial', 'B', 14)
                    pdf.cell(200, 10, txt='Comparison', ln=True, align='L')
                    pdf.ln(10)  # Move down 10 units
          
                    rating_plot1=save_matplotlib_plot_as_image(df, create_plot1, 'rating_plot1.png')
                    rating_plot2=save_matplotlib_plot_as_image(df, create_plot2, 'rating_plot2.png')
                    rating_plot3=save_matplotlib_plot_as_image(df, create_plot3, 'rating_plot3.png')

                    pdf.image("rating_plot1.png", x=30, y=pdf.get_y() + 10, w=0, h=80)  # Adjust the position and size as needed
                    if 'restaurant' in business_types:
                        pdf.image("rating_plot2.png", x=30, y=pdf.get_y() + 10, w=0, h=80)  # Adjust the position and size as needed
                        pdf.add_page()
                        pdf.image("rating_plot3.png", x=30, y=pdf.get_y() + 100, w=0, h=80)  # Adjust the position and size as needed
                    else:
                        pdf.image("rating_plot3.png", x=30, y=pdf.get_y() + 100, w=0, h=80)



                    return pdf

                def create_download_link(val, filename):
                    b64 = base64.b64encode(val)  # val looks like b'...'
                    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Download file</a>'
                #####

                pdf = create_pdf_report(business_name, info_queried_business)

                html = create_download_link(pdf.output(dest="S").encode("latin-1"), "test")
                st.markdown(html, unsafe_allow_html=True)
     
            else:
                st.write("No se encontraron negocios similares.")
        else:
            st.write("No se encontraron detalles.")
    else:
        st.write("No se encontraron resultados.")


