# filepath: /c:/Users/amara/Documents/Python/self_project/main.py
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import bcrypt
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

# Optional: If you need the auto-refresh from 'streamlit_autorefresh'
from streamlit_autorefresh import st_autorefresh

# -----------------------------------------------------------------------------
# 1. Google Sheets and Caching Setup
# -----------------------------------------------------------------------------

# Single function to create the authorized client and open the spreadsheet once.
# We'll store the client/spreadsheet references in st.session_state or as global
# variables (careful with global in production though).
def get_gs_client_and_spreadsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("SoccerScoutDB")
    return client, spreadsheet

# Create these references once per session:
if "gspread_client" not in st.session_state or "spreadsheet" not in st.session_state:
    gs_client, ss = get_gs_client_and_spreadsheet()
    st.session_state["gspread_client"] = gs_client
    st.session_state["spreadsheet"] = ss

# Helper references to each sheet (do it once)
if "players_sheet" not in st.session_state:
    try:
        st.session_state["players_sheet"] = st.session_state["spreadsheet"].worksheet("Players")
    except gspread.exceptions.WorksheetNotFound:
        ws = st.session_state["spreadsheet"].add_worksheet(title="Players", rows=100, cols=20)
        ws.append_row(["UserID", "First Name", "Last Name", "Position", "Age",
                       "Height (cm)", "Weight (kg)", "Email", "Agility",
                       "Power", "Speed", "Bio", "Video Links","Looking For A Team"])
        st.session_state["players_sheet"] = ws

if "users_sheet" not in st.session_state:
    try:
        st.session_state["users_sheet"] = st.session_state["spreadsheet"].worksheet("Users")
    except gspread.exceptions.WorksheetNotFound:
        ws = st.session_state["spreadsheet"].add_worksheet(title="Users", rows=100, cols=10)
        ws.append_row(["UserID", "Email", "PasswordHash", "Role", "DateJoined"])
        st.session_state["users_sheet"] = ws

if "chats_sheet" not in st.session_state:
    try:
        st.session_state["chats_sheet"] = st.session_state["spreadsheet"].worksheet("Chats")
    except gspread.exceptions.WorksheetNotFound:
        ws = st.session_state["spreadsheet"].add_worksheet(title="Chats", rows=100, cols=5)
        ws.append_row(["ChatID", "SenderID", "ReceiverID", "Message", "Timestamp"])
        st.session_state["chats_sheet"] = ws


# -----------------------------------------------------------------------------
# 2. Caching Data Reads to Lower Quota Usage
# -----------------------------------------------------------------------------
# Use short TTLs or none, depending on how fast you need updates.

@st.cache_data(ttl=60)  # e.g. cache for 60s or however long you want
def get_all_users():
    return st.session_state["users_sheet"].get_all_records()

@st.cache_data(ttl=60)
def get_all_players():
    return st.session_state["players_sheet"].get_all_records()

# If the chat needs frequent refreshes, you can use a short TTL or remove caching
# entirely for the chat sheet. But be aware it will hammer your read quota.
@st.cache_data(ttl=5)  # shorter TTL for "near real-time" chat updates
def get_all_chats():
    return st.session_state["chats_sheet"].get_all_records()

# -----------------------------------------------------------------------------
# 3. Functions (Write to Sheets, Filter, etc.)
# -----------------------------------------------------------------------------

def register_user(email, password, role):
    # Because we cache get_all_users(), after we write, we might want to clear
    # the cache so subsequent calls reflect the new data.
    users = get_all_users()
    if any(user['Email'] == email for user in users):
        return False, "Email already exists!"

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    user_id = len(users) + 1
    st.session_state["users_sheet"].append_row([user_id, email, hashed.decode(), role,
                                                datetime.now().strftime("%Y-%m-%d")])
    # Invalidate the cached data to pick up the new user next time
    get_all_users.clear()
    return True, "Registered!"

def login_user(email, password):
    users = get_all_users()
    for user in users:
        if user['Email'] == email and bcrypt.checkpw(password.encode(), user['PasswordHash'].encode()):
            return True, user
    return False, "Invalid credentials!"

def update_player_profile(user_id, data):
    players = get_all_players()
    row_num = next((i + 2 for i, r in enumerate(players) if str(r['UserID']) == str(user_id)), None)
    if row_num:
        st.session_state["players_sheet"].update(f'A{row_num}', [[user_id] + list(data.values())])
    else:
        st.session_state["players_sheet"].append_row([user_id] + list(data.values()))
    get_all_players.clear()  # invalidate player cache to see updates

def search_players(position, min_age, max_age, min_height, max_height, min_agility, min_power, min_speed):
    players = get_all_players()
    filtered = []
    for p in players:
        # Example actual filtering
        if position is None or position == "All" or p['Position'] == position:
            if min_age <= p['Age'] <= max_age:
                if min_height <= p['Height (cm)'] <= max_height:
                    if p['Agility'] >= min_agility and p['Power'] >= min_power and p['Speed'] >= min_speed:
                        filtered.append(p)
    return filtered

# -----------------------------------------------------------------------------
# 4. Chat Functions
# -----------------------------------------------------------------------------
def send_message(sender_id, receiver_id, message):
    all_chats = get_all_chats()
    new_id = len(all_chats) + 1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state["chats_sheet"].append_row([new_id, sender_id, receiver_id, message, timestamp])
    get_all_chats.clear()  # ensure the next read sees the new message

def get_chat_between_users(user_a_id, user_b_id):
    all_chats = get_all_chats()
    chat_records = [
        c for c in all_chats 
        if (str(c['SenderID']) == str(user_a_id) and str(c['ReceiverID']) == str(user_b_id))
           or (str(c['SenderID']) == str(user_b_id) and str(c['ReceiverID']) == str(user_a_id))
    ]
    chat_records.sort(key=lambda x: x['ChatID'])
    return chat_records

def get_users_by_role(role):
    all_users = get_all_users()
    return [u for u in all_users if u['Role'] == role]

def get_user_by_id(user_id):
    all_users = get_all_users()
    for u in all_users:
        if str(u['UserID']) == str(user_id):
            return u
    return None

# -----------------------------------------------------------------------------
# 5. Radar Chart
# -----------------------------------------------------------------------------
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
    ax.set_yticks([0,1, 2,3, 4, 5])
    return fig

# -----------------------------------------------------------------------------
# 6. Streamlit UI
# -----------------------------------------------------------------------------
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main():
    load_css("style.css")
    st.title("⚽ Next-Gen Soccer Scout")

    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'menu' not in st.session_state:
        st.session_state.menu = "Dashboard"

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
        # Logged in
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.rerun(scope="app")
        
        st.sidebar.markdown("### Menu")
        if st.sidebar.button("Dashboard"):
            st.session_state.menu = "Dashboard"
        if st.session_state.user['Role'] == "Player":
            if st.sidebar.button("My Profile"):
                st.session_state.menu = "My Profile"
        if st.sidebar.button("Find Players"):
            st.session_state.menu = "Find Players"
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
            user_id = st.session_state.user["UserID"]
            players_data = get_all_players()
            existing_data = next((p for p in players_data if str(p['UserID']) == str(user_id)), None)
            
            
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
                
                agility = st.slider("Agility", 0, 5, value=existing_data['Agility'] if existing_data else 5)
                power = st.slider("Power", 0, 5, value=existing_data['Power'] if existing_data else 5)
                speed = st.slider("Speed", 0, 5, value=existing_data['Speed'] if existing_data else 5)
                
                bio = st.text_area("Bio", value=existing_data['Bio'] if existing_data else "")
                video_links = st.text_input("Highlight Video Links (comma-separated)", 
                                            value=existing_data['Video Links'] if existing_data else "")
                looking_for_team = st.checkbox("Looking For A Team")
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
                        'Video Links': video_links,
                        'Looking For A Team': looking_for_team
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
                min_agility = cols[0].slider("Min Agility", 0, 5, 3)
                min_power = cols[1].slider("Min Power", 0, 5, 3)
                min_speed = cols[2].slider("Min Speed", 0, 5, 3)

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
            st_autorefresh(interval=2000, limit=100, key="fizzbuzzcounter")
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
                            st.rerun(scope="app")()  # refresh to show new message
                        else:
                            st.warning("Cannot send an empty message!")

if __name__ == "__main__":
    main()