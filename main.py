# filepath: /c:/Users/amara/Documents/Python/self_project/main.py
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import bcrypt
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

# Load custom CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
spreadsheet = client.open("SoccerScoutDB")

# Initialize worksheets
try:
    players_sheet = spreadsheet.worksheet("Players")
except gspread.exceptions.WorksheetNotFound:
    players_sheet = spreadsheet.add_worksheet(title="Players", rows=100, cols=20)
    players_sheet.append_row(["UserID", "First Name", "Last Name", "Position", "Age", "Height (cm)", "Weight (kg)", "Email", "Agility", "Power", "Speed", "Bio", "Video Links"])

try:
    users_sheet = spreadsheet.worksheet("Users")
except gspread.exceptions.WorksheetNotFound:
    users_sheet = spreadsheet.add_worksheet(title="Users", rows=100, cols=10)
    users_sheet.append_row(["UserID", "Email", "PasswordHash", "Role", "DateJoined"])

# Auth functions
def register_user(email, password, role):
    users = users_sheet.get_all_records()
    if any(user['Email'] == email for user in users):
        return False, "Email exists!"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    user_id = len(users) + 1
    users_sheet.append_row([user_id, email, hashed.decode(), role, datetime.now().strftime("%Y-%m-%d")])
    return True, "Registered!"

def login_user(email, password):
    users = users_sheet.get_all_records()
    for user in users:
        if user['Email'] == email and bcrypt.checkpw(password.encode(), user['PasswordHash'].encode()):
            return True, user
    return False, "Invalid credentials!"

# Player profile management
def update_player_profile(user_id, data):
    records = players_sheet.get_all_records()
    row_num = next((i+2 for i, r in enumerate(records) if r['UserID'] == user_id), None)
    if row_num:
        players_sheet.update(f'A{row_num}', [[user_id] + list(data.values())])
    else:
        players_sheet.append_row([user_id] + list(data.values()))

# Search with advanced filters
def search_players(position, min_age, max_age, min_height, max_height, min_agility, min_power, min_speed):
    players = players_sheet.get_all_records()
    filtered = []
    for p in players:
        # if (position == 'All' or p['Position'] == position) and \
        #    min_age <= p['Age'] <= max_age and \
        #    min_height <= p['Height (cm)'] <= max_height and \
        #    p['Agility'] >= min_agility and \
        #    p['Power'] >= min_power and \
        #    p['Speed'] >= min_speed:
        filtered.append(p)
    return filtered

# Radar chart visualization
def plot_radar_chart(player):
    categories = ['Agility', 'Power', 'Speed']
    values = [player[c] for c in categories]
    angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]
    
    fig, ax = plt.subplots(subplot_kw={'polar': True})
    ax.fill(angles, values, alpha=0.25)
    ax.plot(angles, values, marker='o')
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_yticks([25, 50, 75, 100])
    return fig

# UI Configuration
load_css("style.css")
st.title("⚽ Next-Gen Soccer Scout")

# Session state initialization
if 'user' not in st.session_state:
    st.session_state.user = None

# Authentication flow
if not st.session_state.user:
    auth_action = st.sidebar.selectbox("Menu", ["Login", "Register"])
    
    if auth_action == "Login":
        with st.form("Login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                success, result = login_user(email, password)
                if success:
                    st.session_state.user = result
                    st.rerun(scope="app")
                else:
                    st.error(result)
    
    elif auth_action == "Register":
        with st.form("Register"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["Player", "Scout"])
            if st.form_submit_button("Create Account"):
                success, result = register_user(email, password, role)
                if success:
                    st.success("Account created! Please login.")
                else:
                    st.error(result)

else:
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun(scope="app")
    
    menu = st.sidebar.selectbox("Menu", ["Dashboard", "My Profile", "Find Players"])

    if menu == "Dashboard":
        st.header(f"Welcome {st.session_state.user['Role']} {st.session_state.user['Email']}!")
        if st.session_state.user['Role'] == "Player":
            st.write("Manage your profile and get discovered by scouts!")
        else:
            st.write("Discover talented players and build your dream team!")

    elif menu == "My Profile" and st.session_state.user['Role'] == "Player":
        st.header("Player Profile")
        existing_data = next((p for p in players_sheet.get_all_records() if p['UserID'] == st.session_state.user['UserID']), None)
        
        with st.form("ProfileForm"):
            cols = st.columns(3)
            first_name = cols[0].text_input("First Name", value=existing_data['First Name'] if existing_data else "")
            last_name = cols[1].text_input("Last Name", value=existing_data['Last Name'] if existing_data else "")
            position = cols[2].selectbox("Position", ["Goalkeeper", "Defender", "Midfielder", "Forward"], 
                                       index=3 if not existing_data else ["Goalkeeper", "Defender", "Midfielder", "Forward"].index(existing_data['Position']))
            
            cols = st.columns(3)
            age = cols[0].number_input("Age", 16, 40, value=existing_data['Age'] if existing_data else 18)
            height = cols[1].number_input("Height (cm)", 150, 220, value=existing_data['Height (cm)'] if existing_data else 175)
            weight = cols[2].number_input("Weight (kg)", 50, 120, value=existing_data['Weight (kg)'] if existing_data else 70)
            
            agility = st.slider("Agility", 0, 100, value=existing_data['Agility'] if existing_data else 50)
            power = st.slider("Power", 0, 100, value=existing_data['Power'] if existing_data else 50)
            speed = st.slider("Speed", 0, 100, value=existing_data['Speed'] if existing_data else 50)
            
            bio = st.text_area("Bio", value=existing_data['Bio'] if existing_data else "")
            video_links = st.text_input("Highlight Video Links (comma-separated)", value=existing_data['Video Links'] if existing_data else "")
            
            if st.form_submit_button("Save Profile"):
                profile_data = {
                    'First Name': first_name,
                    'Last Name': last_name,
                    'Position': position,
                    'Age': age,
                    'Height (cm)': height,
                    'Weight (kg)': weight,
                    'Email': st.session_state.user['Email'],
                    'Agility': agility,
                    'Power': power,
                    'Speed': speed,
                    'Bio': bio,
                    'Video Links': video_links
                }
                update_player_profile(st.session_state.user['UserID'], profile_data)
                st.success("Profile saved!")

    elif menu == "Find Players":
        st.header("🔍 Advanced Player Search")
        with st.expander("Search Filters"):
            cols = st.columns(3)
            position_filter = cols[0].selectbox("Position", ["All", "Goalkeeper", "Defender", "Midfielder", "Forward"])
            min_age, max_age = cols[1].slider("Age Range", 16, 40, (18, 30))
            min_height, max_height = cols[2].slider("Height (cm)", 150, 220, (160, 200))
            
            st.subheader("Performance Metrics")
            cols = st.columns(3)
            min_agility = cols[0].slider("Min Agility", 0, 100, 30)
            min_power = cols[1].slider("Min Power", 0, 100, 30)
            min_speed = cols[2].slider("Min Speed", 0, 100, 30)

        if st.button("Search Players"):
            st.session_state.search_results = search_players(
                position_filter if position_filter != "All" else None,
                min_age, max_age,
                min_height, max_height,
                min_agility, min_power, min_speed
            )
        
        if 'search_results' in st.session_state and st.session_state.search_results:
            results = st.session_state.search_results
            st.subheader(f"🎯 Found {len(results)} Players")
            sort_by = st.selectbox("Sort By", ["Agility", "Power", "Speed", "Age"], index=0)
            results = sorted(results, key=lambda x: x[sort_by], reverse=True)
            
            for player in results:
                with st.container():
                    cols = st.columns([1,3])
                    with cols[0]:
                        fig = plot_radar_chart(player)
                        st.pyplot(fig)
                    with cols[1]:
                        st.markdown(f"**{player['First Name']} {player['Last Name']}** ({player['Age']} yrs)")
                        st.caption(f"**Position:** {player['Position']} | **Height:** {player['Height (cm)']}cm")
                        st.write(player['Bio'])
                        if player['Video Links']:
                            st.video(player['Video Links'].split(",")[0])
                        if st.button("Contact", key=player['UserID']):
                            st.write(f"📧 Contact at: {player['Email']}")
        else:
            st.warning("No players found matching criteria.")