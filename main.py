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

if "teams_sheet" not in st.session_state:
    try:
        st.session_state["teams_sheet"] = st.session_state["spreadsheet"].worksheet("Teams")
    except gspread.exceptions.WorksheetNotFound:
        ws = st.session_state["spreadsheet"].add_worksheet(title="Teams", rows=100, cols=10)
        # Example columns. Adjust as needed.
        ws.append_row(["TeamID", "TeamName", "City", "FoundedYear", "CoachName", "CreatedOn"])
        st.session_state["teams_sheet"] = ws

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

@st.cache_data(ttl=60)
def get_all_teams():
    """Returns all Teams from the Teams sheet as a list of dicts."""
    return st.session_state["teams_sheet"].get_all_records()

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

def admin_add_team(team_name, city, founded_year, coach_name):
    """
    Inserts a new team row into the Teams sheet.
    Returns (success_boolean, message).
    """
    teams = get_all_teams()
    new_id = len(teams) + 1
    created_on = datetime.now().strftime("%Y-%m-%d")

    row_data = [
        new_id,
        team_name,
        city,
        founded_year,
        coach_name,
        created_on
    ]

    st.session_state["teams_sheet"].append_row(row_data)
    # Invalidate cache so next get_all_teams() will reflect new data
    get_all_teams.clear()

    return True, f"Team '{team_name}' added (TeamID={new_id})."

def delete_team(team_id):
    """
    Removes a team row from the 'Teams' sheet by its TeamID.
    Returns True if successful, False if not found.
    """
    teams = get_all_teams()
    row_num = next((i + 2 for i, t in enumerate(teams) if str(t["TeamID"]) == str(team_id)), None)
    if row_num:
        st.session_state["teams_sheet"].delete_row(row_num)
        get_all_teams.clear()
        return True
    return False

def update_team(team_id, new_name, new_city, new_founded_year, new_coach):
    """
    Finds the row for team_id and updates its columns.
    """
    teams = get_all_teams()
    row_idx = next((i for i, t in enumerate(teams) if str(t["TeamID"]) == str(team_id)), None)

    if row_idx is None:
        return False, f"Team with ID {team_id} not found!"

    row_number = row_idx + 2  # +2 due to header row + 1-based indexing in Sheets
    # Assuming columns: TeamID, TeamName, City, FoundedYear, CoachName, CreatedOn
    # e.g. A=TeamID, B=TeamName, C=City, D=FoundedYear, E=CoachName, F=CreatedOn
    st.session_state["teams_sheet"].update(
        f"B{row_number}:E{row_number}",
        [[new_name, new_city, new_founded_year, new_coach]]
    )
    get_all_teams.clear()
    return True, f"Team {team_id} updated."


def admin_update_player(
    player_id, first_name, last_name, position, age, height, weight, email,
    agility, power, speed, bio, video_links, looking_for_team
):
    """
    Updates a player's row in the 'Players' sheet by player_id (which is stored as 'UserID').
    Returns (success_boolean, message).
    """
    players = get_all_players()  # from your @st.cache_data function
    # Find the row index that has this player_id
    # row_index in `players` list (0-based) => row # in sheet is row_index+2 (due to header)
    row_idx = next((i for i, p in enumerate(players) if str(p["UserID"]) == str(player_id)), None)
    if row_idx is None:
        return False, f"No player found with ID {player_id}."

    row_number = row_idx + 2  # +2 for sheet offset (header row + 1-based index)
    
    # We'll update columns B through N (2..14) in the sheet (assuming A=UserID).
    # That corresponds to:
    #   First Name, Last Name, Position, Age, Height (cm), Weight (kg), Email,
    #   Agility, Power, Speed, Bio, Video Links, Looking For A Team
    # We build one list of values in that order:
    row_values = [
        first_name,
        last_name,
        position,
        age,
        height,
        weight,
        email,
        agility,
        power,
        speed,
        bio,
        video_links,
        # Convert boolean for "Looking For A Team" if needed:
        "TRUE" if looking_for_team else "FALSE"
    ]
    
    # Update the range B..N => columns 2..14
    # Example: "B{row_number}:N{row_number}"
    st.session_state["players_sheet"].update(
        f"B{row_number}:N{row_number}",
        [row_values]
    )
    # Clear cache so subsequent calls see the change
    get_all_players.clear()
    return True, f"Player {player_id} updated successfully."

def admin_delete_player(player_id):
    """
    Deletes a player's row in the 'Players' sheet by player_id.
    Returns True if row was found/deleted, False if not found.
    
    Optionally, you may also want to delete the corresponding User 
    from the Users sheet if you'd like. Or keep them separate if 
    there's a reason to preserve the user login.
    """
    players = get_all_players()
    row_number = next((i+2 for i, p in enumerate(players) if str(p["UserID"]) == str(player_id)), None)
    if row_number:
        st.session_state["players_sheet"].delete_row(row_number)
        get_all_players.clear()
        return True
    return False



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
            st.write("Manage users, roles, teams, **and players** here.")

            # -----------------------------------------------------------------
            # Example: Manage Players
            # -----------------------------------------------------------------
            st.subheader("Existing Players")

            all_players = get_all_players()
            if not all_players:
                st.info("No players found.")
            else:
                for player in all_players:
                    p_id = player["UserID"]  # or int if you prefer
                    first_name = player["First Name"]
                    last_name = player["Last Name"]
                    position = player["Position"]
                    age = player["Age"]
                    height = player["Height (cm)"]
                    weight = player["Weight (kg)"]
                    email = player["Email"]
                    agility = player["Agility"]
                    power = player["Power"]
                    speed = player["Speed"]
                    bio = player["Bio"]
                    video_links = player["Video Links"]
                    looking_for_team = (
                        str(player["Looking For A Team"]).lower() == "true" 
                        or str(player["Looking For A Team"]).lower() == "yes"
                    )

                    # Put each player's info in an expander or container
                    with st.expander(f"Player {p_id}: {first_name} {last_name}", expanded=False):
                        st.write(f"**Position:** {position}, **Age:** {age}, **Email:** {email}")
                        
                        # Let admin edit these fields
                        # (We can create separate columns or do them in one column, etc.)
                        col1, col2, col3 = st.columns(3)
                        new_first_name = col1.text_input(
                            "First Name",
                            value=first_name,
                            key=f"fname_{p_id}"
                        )
                        new_last_name = col2.text_input(
                            "Last Name",
                            value=last_name,
                            key=f"lname_{p_id}"
                        )
                        new_position = col3.selectbox(
                            "Position",
                            ["Goalkeeper", "Defender", "Midfielder", "Forward"],
                            index=["Goalkeeper", "Defender", "Midfielder", "Forward"].index(position)
                            if position in ["Goalkeeper", "Defender", "Midfielder", "Forward"] else 0,
                            key=f"pos_{p_id}"
                        )

                        col4, col5, col6 = st.columns(3)
                        new_age = col4.number_input(
                            "Age",
                            min_value=16, max_value=50,
                            value=int(age) if str(age).isdigit() else 20,
                            key=f"age_{p_id}"
                        )
                        new_height = col5.number_input(
                            "Height (cm)",
                            min_value=100, max_value=250,
                            value=int(height) if str(height).isdigit() else 170,
                            key=f"height_{p_id}"
                        )
                        new_weight = col6.number_input(
                            "Weight (kg)",
                            min_value=30, max_value=150,
                            value=int(weight) if str(weight).isdigit() else 70,
                            key=f"weight_{p_id}"
                        )

                        new_email = st.text_input(
                            "Email",
                            value=email,
                            key=f"email_{p_id}"
                        )

                        # Sliders for agility, power, speed
                        new_agility = st.slider(
                            "Agility",
                            min_value=0, max_value=5,
                            value=int(agility),
                            key=f"agility_{p_id}"
                        )
                        new_power = st.slider(
                            "Power",
                            min_value=0, max_value=5,
                            value=int(power),
                            key=f"power_{p_id}"
                        )
                        new_speed = st.slider(
                            "Speed",
                            min_value=0, max_value=5,
                            value=int(speed),
                            key=f"speed_{p_id}"
                        )

                        new_bio = st.text_area(
                            "Bio",
                            value=bio,
                            key=f"bio_{p_id}"
                        )
                        new_video_links = st.text_input(
                            "Video Links (comma-separated)",
                            value=video_links,
                            key=f"videolinks_{p_id}"
                        )
                        new_looking_for_team = st.checkbox(
                            "Looking For A Team",
                            value=looking_for_team,
                            key=f"looking_{p_id}"
                        )

                        # Buttons
                        col_update, col_delete = st.columns(2)
                        if col_update.button(f"Update Player {p_id}", key=f"update_{p_id}"):
                            success, msg = admin_update_player(
                                player_id=p_id,
                                first_name=new_first_name,
                                last_name=new_last_name,
                                position=new_position,
                                age=new_age,
                                height=new_height,
                                weight=new_weight,
                                email=new_email,
                                agility=new_agility,
                                power=new_power,
                                speed=new_speed,
                                bio=new_bio,
                                video_links=new_video_links,
                                looking_for_team=new_looking_for_team
                            )
                            if success:
                                st.success(msg)
                                st.rerun(scope="app")
                            else:
                                st.error(msg)

                        if col_delete.button(f"Delete Player {p_id}", key=f"delete_{p_id}"):
                            if admin_delete_player(p_id):
                                st.warning(f"Player {first_name} {last_name} deleted.")
                                st.rerun(scope="app")
                            else:
                                st.error("Could not delete. Player not found?")


            # ------------------------- Manage Teams -------------------------
            st.subheader("Add New Team")
            with st.form("AddTeamForm"):
                team_name = st.text_input("Team Name")
                city = st.text_input("City")
                founded_year = st.number_input("Founded Year", 1800, 2050, 2022)
                coach_name = st.text_input("Coach Name", "")
                
                if st.form_submit_button("Add Team"):
                    if team_name.strip():
                        success, msg = admin_add_team(team_name, city, founded_year, coach_name)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("Team Name is required.")

            st.subheader("Existing Teams")
            teams = get_all_teams()
            if not teams:
                st.info("No teams found.")
            else:
                for t in teams:
                    # Display each team in a collapsible expander or row
                    with st.expander(f"Team ID {t['TeamID']}: {t['TeamName']}", expanded=False):
                        # Show current info
                        st.write(f"**City:** {t['City']} | **Founded:** {t['FoundedYear']} | **Coach:** {t['CoachName']}")
                        
                        # Let admin modify
                        new_name = st.text_input("Team Name", value=t['TeamName'], key=f"name_{t['TeamID']}")
                        new_city = st.text_input("City", value=t['City'], key=f"city_{t['TeamID']}")
                        new_founded = st.number_input(
                            "Founded Year", 1800, 2050, int(t['FoundedYear']),
                            key=f"founded_{t['TeamID']}"
                        )
                        new_coach = st.text_input("Coach Name", value=t['CoachName'], key=f"coach_{t['TeamID']}")

                        col1, col2 = st.columns(2)
                        if col1.button(f"Update Team {t['TeamID']}", key=f"update_{t['TeamID']}"):
                            success, msg = update_team(
                                team_id=t["TeamID"],
                                new_name=new_name,
                                new_city=new_city,
                                new_founded_year=new_founded,
                                new_coach=new_coach
                            )
                            if success:
                                st.success(msg)
                                st.rerun(scope="app")
                            else:
                                st.error(msg)

                        if col2.button(f"Delete Team {t['TeamID']}", key=f"delete_{t['TeamID']}"):
                            if delete_team(t["TeamID"]):
                                st.warning(f"Team {t['TeamName']} deleted.")
                                st.rerun(scope="app")
                            else:
                                st.error("Deletion failed or Team not found.")

            # ------------------------- Manage Users -------------------------
            st.subheader("All Users")
            users = get_all_users()
            if not users:
                st.info("No users found.")
            else:
                for user in users:
                    user_id = user['UserID']
                    user_email = user['Email']
                    user_role = user['Role']
                    user_date = user.get("DateJoined", "")
                    
                    # A container or expander for each user
                    with st.expander(f"User {user_id}: {user_email} ({user_role})", expanded=False):
                        st.write(f"Joined: {user_date}")

                        # Example: update role
                        new_role = st.selectbox(
                            "Role", 
                            ["Player", "Scout", "Admin"], 
                            index=["Player", "Scout", "Admin"].index(user_role) 
                            if user_role in ["Player", "Scout", "Admin"] else 0,
                            key=f"role_select_{user_id}"
                        )
                        if new_role != user_role:
                            if st.button(f"Update Role for User {user_id}", key=f"role_btn_{user_id}"):
                                if update_user_role(user_id, new_role):
                                    st.success(f"Role updated for user {user_email} to {new_role}")
                                    st.rerun(scope="app")

                        # Example: update email
                        new_email = st.text_input("Email", value=user_email, key=f"email_{user_id}")
                        if new_email != user_email:
                            if st.button(f"Update Email for User {user_id}", key=f"email_btn_{user_id}"):
                                success, msg = update_user_email(user_id, new_email)
                                if success:
                                    st.success(msg)
                                    st.rerun(scope="app")
                                else:
                                    st.error(msg)

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
