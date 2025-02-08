# filepath: /c:/Users/amara/Documents/Python/self_project/main.py
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import matplotlib.pyplot as plt

# Load custom CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

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

# Example of adding a chart
def plot_player_stats(players):
    names = [f"{player['First Name']} {player['Last Name']}" for player in players]
    agility = [player['Agility'] for player in players]
    power = [player['Power'] for player in players]
    speed = [player['Speed'] for player in players]

    fig, ax = plt.subplots()
    ax.barh(names, agility, label='Agility')
    ax.barh(names, power, left=agility, label='Power')
    ax.barh(names, speed, left=[i+j for i,j in zip(agility, power)], label='Speed')
    ax.set_xlabel('Stats')
    ax.set_title('Player Stats')
    ax.legend()

    st.pyplot(fig)

# Load custom CSS
load_css("style.css")

# Initialize database
init_db()

# App UI
st.title("Soccer Scout App")
menu = st.sidebar.selectbox("Menu", ["Register Player", "Scout Players", "Player Statistics", "About"])

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
            plot_player_stats(players)
            for player in players:
                st.write(f"Name: {player['First Name']} {player['Last Name']}, Position: {player['Position']}, "
                         f"Agility: {player['Agility']}, Power: {player['Power']}, Speed: {player['Speed']}")
        else:
            st.warning("No players found matching criteria.")

elif menu == "Player Statistics":
    st.header("Player Statistics")
    players = sheet.get_all_records()
    if players:
        plot_player_stats(players)
    else:
        st.warning("No players found.")

elif menu == "About":
    st.header("About")
    st.write("This app helps you scout and manage soccer players efficiently.")
    st.write("Developed by [Your Name].")