import streamlit as st
from PIL import Image
import folium
import pandas as pd
import zipfile
import io
import os
import time
from streamlit_folium import st_folium
from folium.plugins import Geocoder
from math import radians, sin, cos, sqrt, atan2


def display_image(image, current_index):
    try:
        img = Image.open(image)
        st.image(img, caption='Image', use_column_width=True, width=400)  # Adjust the width as needed
    except:
        current_index += 1
        # Update session state
        st.session_state.current_index = current_index
        # Reload the page
        st.rerun()

def calculate_distance(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = 6371 * c  # Radius of the Earth in km
    return distance

def main():


    # Display start page to get user's name
    st.set_page_config(layout="wide")
    st.title("Guess the Location")
    user_name = st.text_input("Please enter your name to continue:", key="name")

    # Initialize DataFrame for storing user's selections
    if 'user_selections' not in st.session_state:
        st.session_state.user_selections = pd.DataFrame(columns=['Image', 'Latitude', 'Longitude', 'Distance'])

    # Check if the name is provided
    if user_name:
        st.session_state.name_input_hidden = True
        csv_filename = f"results_{user_name}.csv"

        df_csv = pd.read_csv(r"flickr_images_metadata.csv", sep=",")

        st.markdown('**These pictures are from all around the world. Guess the location by simply clicking on the map and pressing "Submit". You can end the app by clicking "End".**')

        # Upload the zip file containing images
        uploaded_file = st.file_uploader("Upload a zip file containing images", type="zip")

        temp_folder = os.path.join(os.getcwd(), "temp_images")

        if uploaded_file is not None:
            # Extract images from the zip file
            with zipfile.ZipFile(uploaded_file, "r") as zip_ref:
                if not os.path.exists(temp_folder):
                    os.mkdir(temp_folder)
                zip_ref.extractall(temp_folder)

            # Load the extracted images
            images = [os.path.join(temp_folder, f) for f in os.listdir(temp_folder) if f.endswith((".jpg", ".jpeg", ".png"))]

            # Retrieve or initialize current index
            current_index = st.session_state.get("current_index", 0)


            if current_index >= len(images):
                st.write('All images processed. Thank you! Please download the CSV and send it to sebastian.schmidt@plus.ac.at :)')

                # Save DataFrame to CSV file
                csv = st.session_state.user_selections.to_csv(index=False).encode('utf-8')

                st.download_button(
                    "Download CSV",
                    csv,
                    csv_filename,
                    "text/csv",
                    key='download-csv'
                    )
                
                # Stop the Streamlit app
                st.stop()

            # Display the image
            col1, col2 = st.columns(2)
            with col1:
                display_image(images[current_index], current_index)

            # Create the map
            map_center = [0, 0] 
            m = folium.Map(location=map_center, zoom_start=2)
            Geocoder().add_to(m)
            # Add a popup to display latitude and longitude
            m.add_child(folium.LatLngPopup())

            # Display the map
            with col2:
                f_map = st_folium(m, width=800, height=400) 

            # Initialize selected latitude and longitude
            selected_latitude = 0
            selected_longitude = 0

            # Retrieve last clicked position if available
            if f_map.get("last_clicked"):
                selected_latitude = f_map["last_clicked"]["lat"]
                selected_longitude = f_map["last_clicked"]["lng"]

            # Create a form for position entry
            form = st.form("Position Entry Form")

            # Add a submit button to the form
            submit = form.form_submit_button("Submit")

            # Add a skip button
            skip = form.form_submit_button("Skip")


            csv = st.session_state.user_selections.to_csv(index=False).encode('utf-8')
            st.download_button(
                    "Download CSV",
                    csv,
                    csv_filename,
                    "text/csv",
                    key='download-csv'
                    )

            # Handle form submission
            if submit:
                # Check if the selected position is default
                if selected_latitude == 0 and selected_longitude == 0:
                    st.warning("Selected position has default values!")
                else:
                    st.success(f"Stored position: {selected_latitude}, {selected_longitude}")

                # Calculate distance from pre-defined coordinates
                filename = str(images[current_index]).split("/")[-1]
            
                for index, row in df_csv.iterrows():
                    if str(row['filename']).split("\\")[-1] == filename:
                        try:
                            distance = calculate_distance(selected_latitude, selected_longitude, row['lat'], row['lon'])
                            st.info(f"Distance from ({row['lat']},{row['lon']}): {round(distance, 2)} km")
                        except:
                            distance=None
                            st.info(f"Error in distance calculation.")
                        st.info(f"Labelled {current_index+1} / {len(images)} images")


                # Store the user's selection in the session state DataFrame
                user_selections = st.session_state.user_selections
                user_selections.loc[current_index] = [filename, selected_latitude, selected_longitude, distance]
                time.sleep(3) 

                # Move to the next image
                current_index += 1

                # Update session state
                st.session_state.current_index = current_index

                # Display the next image
                if current_index < len(images):
                    if st.button("Show Next Image"):
                        with col1:
                            display_image(images[current_index])
                else:
                    st.write('All images processed. Thank you!')
            
            if skip:
                # Move to the next image without storing the selection
                current_index += 1
                # Update session state
                st.session_state.current_index = current_index
                # Reload the page
                st.rerun()

            # Add an "End" button
            if st.button("End"):
                st.write("Thank you for your help! Please download the CSV and send it to sebastian.schmidt@plus.ac.at :)")
                # Save DataFrame to CSV file
                csv = st.session_state.user_selections.to_csv(index=False).encode('utf-8')

                st.download_button(
                    "Download CSV",
                    csv,
                    csv_filename,
                    "text/csv",
                    key='download-csv'
                    )
                
                # Stop the Streamlit app
                st.stop()


# Run the main function
if __name__ == '__main__':
    main()
