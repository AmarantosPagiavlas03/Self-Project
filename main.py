# filepath: /c:/Users/amara/Documents/Python/self_project/main.py
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("SoccerScoutDB").sheet1  # Open the first sheet

# Initialize database (Google Sheets)
def init_db():
    # Check if the header row is unique
    try:
        sheet.get_all_records()
    except gspread.exceptions.GSpreadException:
        # Clear the sheet and set the header row
        sheet.clear()
        sheet.append_row(["First Name", "Last Name", "Position", "Agility", "Power", "Speed"])

def add_player(first_name, last_name, position, agility, power, speed):
    sheet.append_row([first_name, last_name, position, agility, power, speed])

def search_players(position, min_agility, min_power, min_speed):
    players = sheet.get_all_records()
    filtered_players = []
    for player in players:
        if (position is None or player["Position"] == position) and \
           player["Agility"] >= min_agility and \
           player["Power"] >= min_power and \
           player["Speed"] >= min_speed:
            filtered_players.append(player)
    return filtered_players

# Initialize database
init_db()

# App UI
st.title("Soccer Scout App")
menu = st.sidebar.selectbox("Menu", ["Register Player", "Scout Players"])

if menu == "Register Player":
    st.header("Register a New Player")
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    position = st.selectbox("Position", ["Goalkeeper", "Defender", "Midfielder", "Forward"])
    agility = st.slider("Agility", 0, 100, 50)
    power = st.slider("Power", 0, 100, 50)
    speed = st.slider("Speed", 0, 100, 50)
    
    if st.button("Add Player"):
        add_player(first_name, last_name, position, agility, power, speed)
        st.success("Player added successfully!")

elif menu == "Scout Players":
    st.header("Scout for Players")
    position = st.selectbox("Position", ["All", "Goalkeeper", "Defender", "Midfielder", "Forward"])
    min_agility = st.slider("Min Agility", 0, 100, 0)
    min_power = st.slider("Min Power", 0, 100, 0)
    min_speed = st.slider("Min Speed", 0, 100, 0)

    if st.button("Search"):
        position_filter = None if position == "All" else position
        players = search_players(position_filter, min_agility, min_power, min_speed)
        if players:
            for player in players:
                st.write(f"Name: {player['First Name']} {player['Last Name']}, Position: {player['Position']}, "
                         f"Agility: {player['Agility']}, Power: {player['Power']}, Speed: {player['Speed']}")
        else:
            st.warning("No players found matching criteria.")