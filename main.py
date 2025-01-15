import streamlit as st
from db_utils import init_db, add_player, search_players
import pulp
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
                st.write(f"Name: {player[1]} {player[2]}, Position: {player[3]}, "
                         f"Agility: {player[4]}, Power: {player[5]}, Speed: {player[6]}")
        else:
            st.warning("No players found matching criteria.")
