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

# 1. Initialize worksheets ----------------------------------------------------
try:
    players_sheet = spreadsheet.worksheet("Players")
except gspread.exceptions.WorksheetNotFound:
    players_sheet = spreadsheet.add_worksheet(title="Players", rows=100, cols=20)
    players_sheet.append_row(["UserID", "First Name", "Last Name", "Position", "Age", "Height (cm)", "Weight (kg)",
                              "Email", "Agility", "Power", "Speed", "Bio", "Video Links"])

try:
    users_sheet = spreadsheet.worksheet("Users")
except gspread.exceptions.WorksheetNotFound:
    users_sheet = spreadsheet.add_worksheet(title="Users", rows=100, cols=10)
    users_sheet.append_row(["UserID", "Email", "PasswordHash", "Role", "DateJoined"])

# Create/Initialize a "Chats" sheet for messages
try:
    chats_sheet = spreadsheet.worksheet("Chats")
except gspread.exceptions.WorksheetNotFound:
    chats_sheet = spreadsheet.add_worksheet(title="Chats", rows=100, cols=5)
    chats_sheet.append_row(["ChatID", "SenderID", "ReceiverID", "Message", "Timestamp"])


# 2. Authentication and Data Functions ---------------------------------------
def register_user(email, password, role):
    users = users_sheet.get_all_records()
    if any(user['Email'] == email for user in users):
        return False, "Email already exists!"
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

def update_player_profile(user_id, data):
    records = players_sheet.get_all_records()
    # Because get_all_records returns a list of dicts, we find the row offset by +2 (1-based indexing plus header)
    row_num = next((i + 2 for i, r in enumerate(records) if str(r['UserID']) == str(user_id)), None)
    if row_num:
        players_sheet.update(f'A{row_num}', [[user_id] + list(data.values())])
    else:
        players_sheet.append_row([user_id] + list(data.values()))

def search_players(position, min_age, max_age, min_height, max_height, min_agility, min_power, min_speed):
    players = players_sheet.get_all_records()
    filtered = []
    for p in players:
        # Example actual filtering (uncomment for real usage):
        # if (
        #     (position is None or p['Position'] == position) and
        #     min_age <= p['Age'] <= max_age and
        #     min_height <= p['Height (cm)'] <= max_height and
        #     p['Agility'] >= min_agility and
        #     p['Power'] >= min_power and
        #     p['Speed'] >= min_speed
        # ):
        #     filtered.append(p)
        
        # For now, always adding to demonstrate
        filtered.append(p)
    return filtered

# 3. Chat (Messages) Functions -----------------------------------------------
def send_message(sender_id, receiver_id, message):
    """Store a new message in the 'Chats' sheet."""
    all_chats = chats_sheet.get_all_records()
    new_id = len(all_chats) + 1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chats_sheet.append_row([new_id, sender_id, receiver_id, message, timestamp])

def get_chat_between_users(user_a_id, user_b_id):
    """Fetch messages between two users, sorted by timestamp ascending."""
    all_chats = chats_sheet.get_all_records()
    # Filter only messages where (sender == user_a and receiver == user_b) OR (sender == user_b and receiver == user_a)
    chat_records = [
        c for c in all_chats 
        if (str(c['SenderID']) == str(user_a_id) and str(c['ReceiverID']) == str(user_b_id)) 
           or (str(c['SenderID']) == str(user_b_id) and str(c['ReceiverID']) == str(user_a_id))
    ]
    # Sort by ChatID or by Timestamp if needed
    # We stored the "ChatID" in ascending order, so sorting by that is effectively chronological
    chat_records.sort(key=lambda x: x['ChatID'])
    return chat_records

def get_users_by_role(role):
    """Return a list of user dicts that match the given role ('Player' or 'Scout')."""
    all_users = users_sheet.get_all_records()
    return [u for u in all_users if u['Role'] == role]

def get_user_by_id(user_id):
    """Helper to retrieve a single user dictionary from user ID."""
    all_users = users_sheet.get_all_records()
    for u in all_users:
        if str(u['UserID']) == str(user_id):
            return u
    return None


# 4. Radar chart visualization -----------------------------------------------
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


# 5. Streamlit UI Configuration ----------------------------------------------
load_css("style.css")
st.title("⚽ Next-Gen Soccer Scout")

# Session state initialization
if 'user' not in st.session_state:
    st.session_state.user = None
if 'menu' not in st.session_state:
    st.session_state.menu = "Dashboard"

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
                    st.experimental_rerun()
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
    # If user is logged in, show logout and main menu
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.experimental_rerun()
    
    # Sidebar menu
    st.sidebar.markdown("### Menu")
    if st.sidebar.button("Dashboard"):
        st.session_state.menu = "Dashboard"
    if st.session_state.user['Role'] == "Player":
        if st.sidebar.button("My Profile"):
            st.session_state.menu = "My Profile"
    if st.sidebar.button("Find Players"):
        st.session_state.menu = "Find Players"
    # NEW: Chat button
    if st.sidebar.button("Chat"):
        st.session_state.menu = "Chat"
    
    # Main content switch
    menu = st.session_state.menu

    # ------------------ Dashboard -------------------------------------------
    if menu == "Dashboard":
        st.header(f"Welcome {st.session_state.user['Role']} {st.session_state.user['Email']}!")
        if st.session_state.user['Role'] == "Player":
            st.write("Manage your profile and get discovered by scouts!")
        else:
            st.write("Discover talented players and build your dream team!")

    # ------------------ My Profile (for Players) ---------------------------
    elif menu == "My Profile" and st.session_state.user['Role'] == "Player":
        st.header("Player Profile")
        existing_data = next(
            (p for p in players_sheet.get_all_records() 
             if str(p['UserID']) == str(st.session_state.user['UserID'])), 
            None
        )
        
        with st.form("ProfileForm"):
            cols = st.columns(3)
            first_name = cols[0].text_input("First Name", value=existing_data['First Name'] if existing_data else "")
            last_name = cols[1].text_input("Last Name", value=existing_data['Last Name'] if existing_data else "")
            position = cols[2].selectbox(
                "Position", 
                ["Goalkeeper", "Defender", "Midfielder", "Forward"], 
                index=(["Goalkeeper", "Defender", "Midfielder", "Forward"].index(existing_data['Position']))
                       if existing_data else 3
            )
            
            cols = st.columns(3)
            age = cols[0].number_input("Age", 16, 40, value=existing_data['Age'] if existing_data else 18)
            height = cols[1].number_input("Height (cm)", 150, 220, 
                                          value=existing_data['Height (cm)'] if existing_data else 175)
            weight = cols[2].number_input("Weight (kg)", 50, 120, 
                                          value=existing_data['Weight (kg)'] if existing_data else 70)
            
            agility = st.slider("Agility", 0, 100, value=existing_data['Agility'] if existing_data else 50)
            power = st.slider("Power", 0, 100, value=existing_data['Power'] if existing_data else 50)
            speed = st.slider("Speed", 0, 100, value=existing_data['Speed'] if existing_data else 50)
            
            bio = st.text_area("Bio", value=existing_data['Bio'] if existing_data else "")
            video_links = st.text_input("Highlight Video Links (comma-separated)", 
                                        value=existing_data['Video Links'] if existing_data else "")
            
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

    # ------------------ Find Players ---------------------------------------
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
                            # Show first video link if multiple are provided
                            st.video(player['Video Links'].split(",")[0])
                        if st.button(f"Contact {player['UserID']}", key=f"contact_{player['UserID']}"):
                            st.write(f"📧 Contact at: {player['Email']}")
        else:
            st.warning("No players found matching criteria or please click 'Search Players'.")

    # ------------------ Chat Menu -------------------------------------------
    elif menu == "Chat":
        st.header("💬 Chat")

        current_user = st.session_state.user
        current_user_id = current_user['UserID']
        current_role = current_user['Role']

        # Decide who the user can chat with (Scouts see Players, Players see Scouts)
        if current_role == "Scout":
            # get all players
            other_users = get_users_by_role("Player")
            role_label = "Select a Player to chat with:"
        else:
            # if user is a Player, we show all scouts
            other_users = get_users_by_role("Scout")
            role_label = "Select a Scout to chat with:"

        # If there's no one in the opposite role, show a message
        if not other_users:
            st.info(f"No users with the opposite role found!")
        else:
            # Let the user pick from a dropdown
            selected_user_email = st.selectbox(role_label, [u['Email'] for u in other_users])
            # Find that user’s ID
            selected_user = next(u for u in other_users if u['Email'] == selected_user_email)
            selected_user_id = selected_user['UserID']

            # Display existing chat
            chat_records = get_chat_between_users(current_user_id, selected_user_id)
            st.subheader(f"Chat with {selected_user_email}")
            
            # Show messages in ascending order
            for c in chat_records:
                sender = get_user_by_id(c['SenderID'])
                sender_email = sender['Email'] if sender else "Unknown"
                timestamp = c['Timestamp']
                message_text = c['Message']
                
                # Simple formatting: show "[timestamp] sender: message"
                st.write(f"**[{timestamp}] {sender_email}:** {message_text}")

            # Text input to send a new message
            with st.form("send_message_form", clear_on_submit=True):
                new_msg = st.text_area("Type your message:")
                if st.form_submit_button("Send"):
                    if new_msg.strip():
                        send_message(current_user_id, selected_user_id, new_msg.strip())
                        st.experimental_rerun()  # refresh to show new message
                    else:
                        st.warning("Cannot send an empty message!")
