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

def get_gs_client_and_spreadsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("SoccerScoutDB")
    return client, spreadsheet

if "gspread_client" not in st.session_state or "spreadsheet" not in st.session_state:
    gs_client, ss = get_gs_client_and_spreadsheet()
    st.session_state["gspread_client"] = gs_client
    st.session_state["spreadsheet"] = ss

# Helper references to each sheet
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

@st.cache_data(ttl=60)
def get_all_users():
    return st.session_state["users_sheet"].get_all_records()

@st.cache_data(ttl=60)
def get_all_players():
    return st.session_state["players_sheet"].get_all_records()

@st.cache_data(ttl=5)
def get_all_chats():
    return st.session_state["chats_sheet"].get_all_records()


# -----------------------------------------------------------------------------
# 3. Functions (Write to Sheets, Filter, etc.)
# -----------------------------------------------------------------------------

def register_user(email, password, role):
    """
    Registers a new user in the 'Users' sheet.
    """
    users = get_all_users()
    if any(user['Email'] == email for user in users):
        return False, "Email already exists!"

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    user_id = len(users) + 1
    st.session_state["users_sheet"].append_row(
        [user_id, email, hashed.decode(), role, datetime.now().strftime("%Y-%m-%d")]
    )
    get_all_users.clear()
    return True, "Registered!"

def login_user(email, password):
    """
    Attempts to log a user in by matching email + password hash.
    """
    users = get_all_users()
    for user in users:
        if user['Email'] == email and bcrypt.checkpw(password.encode(), user['PasswordHash'].encode()):
            return True, user
    return False, "Invalid credentials!"

def update_player_profile(user_id, data):
    """
    Update or create a player's profile row in 'Players' sheet.
    """
    players = get_all_players()
    row_num = next((i + 2 for i, r in enumerate(players) if str(r['UserID']) == str(user_id)), None)
    if row_num:
        st.session_state["players_sheet"].update(f'A{row_num}', [[user_id] + list(data.values())])
    else:
        st.session_state["players_sheet"].append_row([user_id] + list(data.values()))
    get_all_players.clear()

def search_players(position, min_age, max_age, min_height, max_height, min_agility, min_power, min_speed):
    """
    Filters players based on position, age, height, agility, power, speed.
    """
    players = get_all_players()
    filtered = []
    for p in players:
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
    get_all_chats.clear()

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
# 5. Admin Functions
# -----------------------------------------------------------------------------

def update_user_role(user_id, new_role):
    """
    Finds a user in the Users sheet by user_id and updates their role.
    """
    users = get_all_users()
    for i, user in enumerate(users):
        if str(user['UserID']) == str(user_id):
            row_num = i + 2  # +2 because sheet rows start at 1, plus header row
            st.session_state["users_sheet"].update_cell(row_num, 4, new_role)
            get_all_users.clear()
            return True
    return False

def delete_user(user_id):
    """
    Delete a user from the 'Users' sheet and optionally their 'Players' row.
    """
    # 1. Remove from Users sheet
    users = get_all_users()
    user_row = next((i+2 for i, u in enumerate(users) if str(u["UserID"]) == str(user_id)), None)
    if user_row:
        st.session_state["users_sheet"].delete_row(user_row)
        get_all_users.clear()

    # 2. Optionally remove from Players sheet
    players = get_all_players()
    player_row = next((i+2 for i, p in enumerate(players) if str(p["UserID"]) == str(user_id)), None)
    if player_row:
        st.session_state["players_sheet"].delete_row(player_row)
        get_all_players.clear()

    # 3. (Optional) remove from Chats (if you want to fully scrub data)
    # Here, we'd do repeated row deletion. For brevity, not shown.

def is_admin(user):
    """
    Convenience to check if logged-in user is admin.
    """
    return user and user.get("Role") == "Admin"

# -----------------------------------------------------------------------------
# 6. Radar Chart
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
    ax.set_yticks([0,1,2,3,4,5])
    return fig

# -----------------------------------------------------------------------------
# 7. Streamlit UI
# -----------------------------------------------------------------------------

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main():
    load_css("style.css")
    st.title("⚽ Next-Gen Soccer Scout ")

    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'menu' not in st.session_state:
        st.session_state.menu = "Dashboard"

    # ------------------- Auth Flow ------------------------
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
                role = st.selectbox("Role", ["Player", "Scout", "Admin"])  # Admin now possible
                if st.form_submit_button("Create Account"):
                    success, result = register_user(email, password, role)
                    if success:
                        st.success("Account created! Please login.")
                    else:
                        st.error(result)

    # ------------------- Main App -------------------------
    else:
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.rerun(scope="app")

        st.sidebar.markdown("### Menu")
        if st.sidebar.button("Dashboard"):
            st.session_state.menu = "Dashboard"
        
        # If user is a Player, show My Profile
        if st.session_state.user['Role'] == "Player":
            if st.sidebar.button("My Profile"):
                st.session_state.menu = "My Profile"
        
        if st.sidebar.button("Find Players"):
            st.session_state.menu = "Find Players"
        
        if st.sidebar.button("Chat"):
            st.session_state.menu = "Chat"
        
        # Admin-only button
        if is_admin(st.session_state.user):
            if st.sidebar.button("Admin Panel"):
                st.session_state.menu = "Admin Panel"

        menu = st.session_state.menu

        # --------------- Dashboard ---------------
        if menu == "Dashboard":
            st.header(f"Welcome {st.session_state.user['Role']} {st.session_state.user['Email']}!")
            if st.session_state.user['Role'] == "Player":
                st.write("Manage your profile and get discovered by scouts!")
            elif st.session_state.user['Role'] == "Scout":
                st.write("Discover talented players and build your dream team!")
            else:
                st.write("As an Admin, you can manage users, roles, and more.")

        # --------------- My Profile (Players only) ---------------
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
                          if existing_data else 0
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
                video_links = st.text_input(
                    "Highlight Video Links (comma-separated)", 
                    value=existing_data['Video Links'] if existing_data else ""
                )
                looking_for_team = st.checkbox("Looking For A Team", value=existing_data['Looking For A Team'] if existing_data else False)
                
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

        # --------------- Find Players ---------------
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
                        cols = st.columns([1.5,1.5])
                        with cols[0]:
                            fig = plot_radar_chart(player)
                            st.pyplot(fig)
                        with cols[1]:
                            st.markdown(f"**{player['First Name']} {player['Last Name']}** ({player['Age']} yrs)")
                            st.caption(f"**Position:** {player['Position']} | **Height:** {player['Height (cm)']}cm")
                            st.write(player['Bio'])
                            if player['Video Links']:
                                # Show first video link if multiple are provided
                                first_link = player['Video Links'].split(",")[0].strip()
                                if first_link.startswith("http"):
                                    st.video(first_link)
                                else:
                                    st.write("Video link not valid or recognized.")
                            if st.button(f"Contact {player['UserID']}", key=f"contact_{player['UserID']}"):
                                st.write(f"📧 Contact at: {player['Email']}")
            else:
                st.warning("No players found matching criteria or please click 'Search Players'.")

        # --------------- Chat ---------------
        elif menu == "Chat":
            st_autorefresh(interval=2000, limit=100, key="fizzbuzzcounter")
            st.header("💬 Chat")

            current_user = st.session_state.user
            current_user_id = current_user['UserID']
            current_role = current_user['Role']

            if current_role == "Scout":
                other_users = get_users_by_role("Player")
                role_label = "Select a Player to chat with:"
            elif current_role == "Player":
                other_users = get_users_by_role("Scout")
                role_label = "Select a Scout to chat with:"
            else:
                # Admin can choose to chat with either role
                all_other_users = [u for u in get_all_users() if str(u['UserID']) != str(current_user_id)]
                other_users = sorted(all_other_users, key=lambda x: x['Email'])
                role_label = "Select a user to chat with:"

            if not other_users:
                st.info("No users available to chat with.")
            else:
                selected_user_email = st.selectbox(role_label, [u['Email'] for u in other_users])
                selected_user = next(u for u in other_users if u['Email'] == selected_user_email)
                selected_user_id = selected_user['UserID']

                chat_records = get_chat_between_users(current_user_id, selected_user_id)
                st.subheader(f"Chat with {selected_user_email}")
                
                for c in chat_records:
                    sender = get_user_by_id(c['SenderID'])
                    sender_email = sender['Email'] if sender else "Unknown"
                    timestamp = c['Timestamp']
                    message_text = c['Message']
                    st.write(f"**[{timestamp}] {sender_email}:** {message_text}")

                with st.form("send_message_form", clear_on_submit=True):
                    new_msg = st.text_area("Type your message:")
                    if st.form_submit_button("Send"):
                        if new_msg.strip():
                            send_message(current_user_id, selected_user_id, new_msg.strip())
                            st.rerun(scope="app")
                        else:
                            st.warning("Cannot send an empty message!")

        # --------------- Admin Panel ---------------
        elif menu == "Admin Panel" and is_admin(st.session_state.user):
            st.header("🔑 Admin Panel")
            st.write("Manage users, roles, and more here.")

            # List all users
            users = get_all_users()
            st.subheader("All Users")
            for user in users:
                user_id = user['UserID']
                user_email = user['Email']
                user_role = user['Role']
                user_date = user.get("DateJoined", "")

                col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                col1.write(f"**ID:** {user_id}")
                col2.write(f"**Email:** {user_email}")
                col3.write(f"**Role:** {user_role}")
                col4.write(f"**Joined:** {user_date}")
                
                # Manage role
                new_role = st.selectbox(
                    f"Change Role (UserID={user_id})",
                    ["Player", "Scout", "Admin"],
                    index=["Player", "Scout", "Admin"].index(user_role) if user_role in ["Player","Scout","Admin"] else 0,
                    key=f"role_{user_id}"
                )
                if new_role != user_role:
                    if st.button(f"Update Role for User {user_id}", key=f"update_{user_id}"):
                        if update_user_role(user_id, new_role):
                            st.success(f"Role updated for user {user_email} to {new_role}")
                            st.rerun(scope="app")

                # Delete user
                if st.button(f"Delete User {user_id}", key=f"delete_{user_id}"):
                    delete_user(user_id)
                    st.warning(f"User {user_email} deleted.")
                    st.rerun(scope="app")

        else:
            # If user tries to access Admin Panel but is not admin
            st.error("You do not have permission to view this page.")

if __name__ == "__main__":
    main()
