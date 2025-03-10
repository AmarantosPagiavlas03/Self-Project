# filepath: /c:/Users/amara/Documents/Python/self_project/main.py
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import bcrypt
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import random
# Optional: If you need the auto-refresh from 'streamlit_autorefresh'
from streamlit_autorefresh import st_autorefresh
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import time
import random
import string
import json
import streamlit.components.v1 as components
from datetime import timedelta
from datetime import datetime, timezone, timedelta
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

if "sessions_sheet" not in st.session_state:
    try:
        st.session_state["sessions_sheet"] = st.session_state["spreadsheet"].worksheet("Sessions")
    except gspread.exceptions.WorksheetNotFound:
        ws = st.session_state["spreadsheet"].add_worksheet(title="Sessions", rows=100, cols=10)
        ws.append_row(["Token", "UserID", "Expiration"])
        st.session_state["sessions_sheet"] = ws

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

@st.cache_data(ttl=60)
def get_all_sessions():
    return st.session_state["sessions_sheet"].get_all_records()

# -----------------------------------------------------------------------------
# 3. Session Management Functions
# -----------------------------------------------------------------------------


def generate_session_token():
    """Generate a random 32-character token."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def validate_session_token(token):
    """Validate session token with proper timezone handling."""
    ws = st.session_state["sessions_sheet"]
    
    try:
        # Case-sensitive exact match search
        cell = ws.find(token, in_column=1, case_sensitive=True)
        record = ws.row_values(cell.row)
        
        # Ensure UTC timezone for comparison
        expires_at = datetime.fromisoformat(record[2]).replace(tzinfo=timezone.utc)
        current_time = datetime.now(timezone.utc)
        
        if current_time < expires_at:
            return record[1]  # Return UserID
        else:
            # Auto-clean expired tokens
            ws.delete_row(cell.row)
            return None
            
    except gspread.exceptions.CellNotFound:
        return None
    except Exception as e:
        # Use proper logging instead of st.error for background ops
        print(f"Session validation error: {str(e)}")  
        return None

def update_session_activity(token):
    """Update session expiration with consistent TTL."""
    ws = st.session_state["sessions_sheet"]
    
    try:
        # Find token with exact match
        cell = ws.find(token, in_column=1, case_sensitive=True)
        record = ws.row_values(cell.row)
        
        # Maintain original TTL duration (7 days from initial login)
        new_expiration = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        
        # Update both expiration and last activity time
        ws.update(f"C{cell.row}:D{cell.row}", [[new_expiration, datetime.now(timezone.utc).isoformat()]])
        
    except gspread.exceptions.CellNotFound:
        print(f"Token not found during update: {token}")
    except Exception as e:
        print(f"Session update error: {str(e)}")
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

def update_team_profile(user_id, data):
    """
    Creates or updates a team's row in the Teams sheet, keyed by user_id.
    data should be a dict with keys matching your columns, except UserID.
    """
    teams = get_all_teams()  # e.g. list of dict
    row_num = next(
        (i + 2 for i, t in enumerate(teams) if str(t["UserID"]) == str(user_id)), 
        None
    )

    # Build row data in the correct column order
    # Assuming columns: [UserID, Team Name, City, Founded Year, Stadium, Coach, Description, Website, CreatedOn]
    # `data` might look like: {
    #     "Team Name": ...,
    #     "City": ...,
    #     ...
    # }
    if row_num:
        # Update existing row
        # For example, we update columns B..I (2..9) if A=UserID
        row_values = [
            data["Team Name"],
            data["City"],
            data["Founded Year"],
            data["Stadium"],
            data["Coach"],
            data["Description"],
            data["Website"],
            data.get("CreatedOn", "")
        ]
        st.session_state["teams_sheet"].update(
            f"B{row_num}:I{row_num}",
            [row_values]
        )
    else:
        # Append a new row
        new_row = [
            user_id,
            data["Team Name"],
            data["City"],
            data["Founded Year"],
            data["Stadium"],
            data["Coach"],
            data["Description"],
            data["Website"],
            data.get("CreatedOn", "")
        ]
        st.session_state["teams_sheet"].append_row(new_row)

    get_all_teams.clear()  # invalidate cache

    return True

def search_players(name_filter, position, min_age, max_age, 
                   min_height, max_height, 
                   min_agility, min_power, min_speed):
    players = get_all_players()
    filtered = []
    for p in players:
        # 1) Check name match (if name_filter is provided)
        #    We'll check if the typed string is in "FirstName LastName" (case-insensitive).
        if name_filter:
            full_name = (p['First Name'] + " " + p['Last Name']).lower()
            if name_filter.lower() not in full_name:
                continue  # Skip this player if name doesn't match

        # 2) Position check
        if position is None or position == "All" or p['Position'] == position:
            # 3) Age check
            if min_age <= p['Age'] <= max_age:
                # 4) Height check
                if min_height <= p['Height (cm)'] <= max_height:
                    # 5) Performance checks
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
    return [u for u in all_users]

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

def update_user_email(user_id, new_email):
    """Example function to update email by user ID."""
    users = get_all_users()
    row_idx = next((i for i, u in enumerate(users) if str(u["UserID"]) == str(user_id)), None)
    if row_idx is None:
        return False, f"No user with ID {user_id}"
    row_number = row_idx + 2
    # Column 2 is 'Email' in your original setup: [UserID, Email, PasswordHash, Role, ...]
    st.session_state["users_sheet"].update_cell(row_number, 2, new_email)
    get_all_users.clear()
    return True, f"Email updated to {new_email}"

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
        st.session_state["teams_sheet"].delete_rows(row_num)
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

def admin_add_player(
    first_name, last_name, position, age, height, weight, email, 
    agility, power, speed, bio, video_links, looking_for_team
):
    """
    Creates a new row in the Players sheet with the given data.
    Returns (success_boolean, message).
    """
    players = get_all_players()  # your cached function that returns all players
    new_id = len(players) + 1  # A simple ID scheme (UserID = row_count + 1)

    # Convert the boolean for "Looking For A Team" to a string if needed
    lft_value = "TRUE" if looking_for_team else "FALSE"

    row_data = [
        new_id,
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
        lft_value
    ]

    st.session_state["players_sheet"].append_row(row_data)
    get_all_players.clear()  # Invalidate the cache so we see the new row next time
    return True, f"Player '{first_name} {last_name}' added (ID={new_id})."


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
# 6. Captcha
# -----------------------------------------------------------------------------
def generate_2fa_code(length=6):
    """
    Returns a random numeric string of given length, e.g. '123456'.
    """
    return "".join(str(random.randint(0, 9)) for _ in range(length))

def send_email_code(to_email, code):
    """
    Sends an email with the 2FA code using SendGrid.
    Requires a valid SENDGRID_API_KEY in your environment or st.secrets.
    """
    api_key = st.secrets["SENDGRID_API_KEY"]["SENDGRID_API_KEY"]
 
    # Usually you'd store the API key in st.secrets["SENDGRID_API_KEY"] or os.environ["SENDGRID_API_KEY"]
    SENDGRID_API_KEY = api_key

    if not SENDGRID_API_KEY:
        raise ValueError("No SendGrid API key found. Set 'SENDGRID_API_KEY' as an environment variable.")

    message = Mail(
        from_email="amarantosp@gmail.com",
        to_emails=to_email,
        subject="Your 2FA Code",
        html_content=f"""
        <p>Hello,</p>
        <p>Your 2FA code is: <strong>{code}</strong>.</p>
        <p>It will expire in 5 minutes.</p>
        <p>Thank you,<br>Your App Team</p>
        """
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        # Optional: You can log response.status_code or response.body if needed
    except Exception as e:
        print(str(e))
        # In production, log the exception or notify developers
        raise

 

def generate_complex_captcha():
    """
    Returns a tuple: (question_string, answer_string).
    E.g. ("(4 + 3) * 2", "14")
    """
    # Helper function to do an operation on two numbers
    def do_op(a, b, op):
        if op == '+':
            return a + b
        elif op == '-':
            return a - b
        else:  # '*'
            return a * b

    x = random.randint(1, 10)
    y = random.randint(1, 10)
    z = random.randint(1, 10)
    ops = ['+', '-', '*']
    op1 = random.choice(ops)
    op2 = random.choice(ops)

    # 50% chance to do (x op1 y) op2 z, or x op1 (y op2 z)
    if random.random() < 0.5:
        # (x op1 y) op2 z
        intermediate = do_op(x, y, op1)
        final_answer = do_op(intermediate, z, op2)
        question = f"({x} {op1} {y}) {op2} {z}"
    else:
        # x op1 (y op2 z)
        intermediate = do_op(y, z, op2)
        final_answer = do_op(x, intermediate, op1)
        question = f"{x} {op1} ({y} {op2} {z})"

    return question, str(final_answer)
 
# -----------------------------------------------------------------------------
# 7. Streamlit UI
# -----------------------------------------------------------------------------

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main():
    load_css("style.css")
    st.title("⚽ Next-Gen Soccer Scout ")

    # if 'user' not in st.session_state:
    #     # Get token from URL parameters (if exists)
    #     token_param = st._get_query_params().get("token", [None])[0]
        
    #     # Phase 1: Token from URL (initial validation)
    #     if token_param:
    #         user_id = validate_session_token(token_param)
    #         st.write(user_id)
    #         if user_id:
    #             user = get_user_by_id(user_id)
    #             if user:
    #                 st.session_state.user = user
    #                 update_session_activity(token_param)
                    
    #                 # Remove token from URL after validation
    #                 components.html("""
    #                     <script>
    #                     const url = new URL(window.location);
    #                     url.searchParams.delete('token');
    #                     window.history.replaceState(null, '', url.toString());
    #                     </script>
    #                 """, height=0)
                    
    #                 # Store token in localStorage for future refreshes
    #                 components.html(f"""
    #                     <script>
    #                     localStorage.setItem('session_token', '{token_param}');
    #                     </script>
    #                 """, height=0)
    #         else:
    #             # Invalid token - clear everything
    #             components.html("""
    #                 <script>
    #                 localStorage.removeItem('session_token');
    #                 </script>
    #             """, height=0)
        
    #     # Phase 2: Check localStorage if no URL token
    #     else:
    #         # Inject JavaScript to check localStorage and redirect
    #         components.html("""
    #             <script>
    #             const token = localStorage.getItem('session_token');
    #             if (token && !window.location.search.includes('token')) {
    #                 const url = new URL(window.location);
    #                 url.searchParams.set('token', token);
    #                 window.location.href = url.toString();
    #             }
    #             </script>
    #         """, height=0)

    if 'user' not in st.session_state:
        # Create a listener component
        token_data = components.declare_component("token_listener", url="")()
        if token_data:
            st.session_state.js_token = token_data['value']

    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'menu' not in st.session_state:
        st.session_state.menu = "Dashboard"
    if 'login_menu' not in st.session_state:
        st.session_state.login_menu = "Login"

    # ------------------- Auth Flow ------------------------
    if not st.session_state.user:
        if st.sidebar.button("Login"):
            st.session_state.login_menu = "Login"
        if st.sidebar.button("Register"):
            st.session_state.login_menu = "Register"
        auth_action = st.session_state.login_menu
        
        if auth_action == "Login":


            if "login_step" not in st.session_state:
                st.session_state.login_step = "credentials"

            if st.session_state.login_step == "credentials":
                st.subheader("Login - Step 1: Enter Credentials")
                with st.form("LoginForm"):
                    email = st.text_input("Email")
                    password = st.text_input("Password", type="password")
                    if st.form_submit_button("Next"):
                        success, user_record = login_user(email, password)
                        if success:
                            # Bypass 2FA for Admin
                            if user_record.get("Role") == "Admin":
                                st.session_state.user = user_record
                                st.success("Logged in as Admin!")
                                
                                # token = generate_session_token()
                                # expiration = datetime.now(timezone.utc) + timedelta(days=7)
                                # user_id = user_record.get("UserID")
                                # st.session_state["sessions_sheet"].append_row([
                                #     token,
                                #     user_id,
                                #     expiration.isoformat(),
                                #     datetime.now(timezone.utc).isoformat()  # LastActivity
                                # ])
                                # # get_all_sessions.clear()

                                # # Redirect with token in URL (trigger Phase 1 validation)
                                # components.html(f"""
                                #     <script>
                                #     localStorage.setItem('session_token', '{token}');
                                #     window.location.search = `token={token}`;
                                #     </script>
                                # """, height=0)
 
                                st.rerun()                              
                            else:
                                st.session_state["temp_user"] = user_record
                                code = generate_2fa_code(6)
                                st.session_state["2fa_code"] = code
                                st.session_state["2fa_code_time"] = time.time()
                                send_email_code(user_record['Email'], code)
                                st.session_state.login_step = "2fa"
                        else:
                            st.error("Invalid credentials")

            elif st.session_state.login_step == "2fa":
                st.subheader("Login - Step 2: 2FA Code")
                code_input = st.text_input("Check your email for the verification code:")
                if st.button("Verify"):
                    now = time.time()
                    code_generated_at = st.session_state["2fa_code_time"]
                    
                    # Expire code after 5 minutes (300s)
                    if now - code_generated_at > 300:
                        st.error("2FA code expired. Please try logging in again.")
                        # Reset to Step 1
                        st.session_state.login_step = "credentials"
                    else:
                        correct_code = st.session_state["2fa_code"]
                        if code_input.strip() == correct_code:
                            # 2FA passed; finalize login
                            st.session_state.user = st.session_state["temp_user"]
                            st.success("You are now logged in!")

                            # # Generate and store session token
                            # token = generate_session_token()
                            # user_id = user_record.get("UserID")
                            # expiration = datetime.now(timezone.utc) + timedelta(days=7)
                            # st.session_state["sessions_sheet"].append_row([
                            #     token,
                            #     user_id,
                            #     expiration.isoformat(),
                            #     datetime.now(timezone.utc).isoformat()  # LastActivity
                            # ])
                            # # get_all_sessions.clear()

                            # # Redirect with token in URL (trigger Phase 1 validation)
                            # components.html(f"""
                            #     <script>
                            #     localStorage.setItem('session_token', '{token}');
                            #     window.location.search = `token={token}`;
                            #     </script>
                            # """, height=0)



                            # Clear temp states
                            st.session_state.pop("temp_user", None)
                            st.session_state.pop("2fa_code", None)
                            st.session_state.pop("2fa_code_time", None)
                            
                            # Reset login step if you want to reuse logic
                            st.session_state.login_step = "credentials"
                            st.rerun(scope="app")
                        else:
                            st.error("Incorrect code, please try again.")        

        elif auth_action == "Register":
            if "register_step" not in st.session_state:
                st.session_state.register_step = "credentials"
            if st.session_state.register_step == "credentials":
                st.subheader("Register - Step 1: Enter Credentials")
                with st.form("Register"):
                    email = st.text_input("Email")
                    password = st.text_input("Password", type="password")
                    role = st.selectbox("Role", ["Player", "Scout", "Team", "Admin"])
                    if st.form_submit_button("Next"):
                        success, user_record = register_user(email, password,role)
                        if success:
                            # Password is correct, but let's do 2FA
                            st.session_state["temp_user"] = user_record
                            # Generate a one-time code
                            code = generate_2fa_code(6)
                            st.session_state["2fa_code"] = code
                            st.session_state["2fa_code_time"] = time.time()
                            
                            # Here is where you actually USE send_email_code
                            send_email_code(user_record["Email"], code)  # <--- (1)

                            # Move to step 2
                            st.session_state.register_step = "2fa"
                        else:
                            st.error("Invalid credentials")

            elif st.session_state.register_step == "2fa":
                st.subheader("Register - Step 2: 2FA Code")
                code_input = st.text_input("Check your email for the verification code:")
                if st.button("Verify"):
                    now = time.time()
                    code_generated_at = st.session_state["2fa_code_time"]
                    
                    # Expire code after 5 minutes (300s)
                    if now - code_generated_at > 300:
                        st.error("2FA code expired. Please try logging in again.")
                        # Reset to Step 1
                        st.session_state.register_step = "credentials"
                    else:
                        correct_code = st.session_state["2fa_code"]
                        if code_input.strip() == correct_code:
                            # 2FA passed; finalize login
                            st.session_state.user = st.session_state["temp_user"]
                            st.success("You are now logged in!")

                            # Generate and store session token
                            token = generate_session_token()
                            user_id = user_record.get("UserID")
                            expiration = datetime.now(timezone.utc) + timedelta(days=7)
                            st.session_state["sessions_sheet"].append_row([
                                token,
                                user_id,
                                expiration.isoformat(),
                                datetime.now(timezone.utc).isoformat()  # LastActivity
                            ])
                            # get_all_sessions.clear()

                            # Redirect with token in URL (trigger Phase 1 validation)
                            components.html(f"""
                                <script>
                                localStorage.setItem('session_token', '{token}');
                                window.location.search = `token={token}`;
                                </script>
                            """, height=0)
                            st.stop()


                            # Clear temp states
                            st.session_state.pop("temp_user", None)
                            st.session_state.pop("2fa_code", None)
                            st.session_state.pop("2fa_code_time", None)
                            
                            # Reset login step if you want to reuse logic
                            st.session_state.register_step = "credentials"
                            st.rerun(scope="app")
                        else:
                            st.error("Incorrect code, please try again.")     

    # ------------------- Main App -------------------------
    else:
        # if st.sidebar.button("Logout"):
        #     # Database cleanup
        #     user_id = st.session_state.user["UserID"]
        #     sessions = get_all_sessions()
        #     rows_to_delete = [i+2 for i,s in enumerate(sessions) if str(s["UserID"]) == str(user_id)]
        #     for row in reversed(rows_to_delete):
        #         st.session_state["sessions_sheet"].delete_rows(row)
            
        #     # Client-side cleanup
        #     components.html("""
        #         <script>
        #         localStorage.removeItem('session_token');
        #         window.location.href = window.location.href.split('?')[0];
        #         </script>
        #     """, height=0)
        #     st.session_state.clear()
        #     st.stop()
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

        if st.session_state.user and st.session_state.user['Role'] == "Team":
            if st.sidebar.button("My Team Profile"):
                st.session_state.menu = "My Team Profile"
        
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

        elif menu == "My Team Profile" and st.session_state.user['Role'] == "Team":
            st.header("Team Profile")

            user_id = st.session_state.user["UserID"]
            teams_data = get_all_teams()
            existing_team = next(
                (t for t in teams_data if str(t['UserID']) == str(user_id)), 
                None
            )

            # Pre-fill form values if the team row exists:
            default_team_name = existing_team["Team Name"] if existing_team else ""
            default_city = existing_team["City"] if existing_team else ""
            default_founded = existing_team["Founded Year"] if existing_team else 2020
            default_stadium = existing_team["Stadium"] if existing_team else ""
            default_coach = existing_team["Coach"] if existing_team else ""
            default_desc = existing_team["Description"] if existing_team else ""
            default_website = existing_team["Website"] if existing_team else ""

            with st.form("TeamProfileForm"):
                st.subheader("Basic Info")
                c1, c2 = st.columns(2)
                team_name = c1.text_input("Team Name", value=default_team_name)
                city = c2.text_input("City", value=default_city)

                founded_year = st.number_input("Founded Year", 1800, 2100, value=int(default_founded) if str(default_founded).isdigit() else 2020)
                stadium = st.text_input("Stadium", value=default_stadium)
                coach = st.text_input("Coach Name", value=default_coach)
                description = st.text_area("Description", value=default_desc)
                website = st.text_input("Website", value=default_website)

                if st.form_submit_button("Save Team Profile"):
                    # Build the data dict to pass into update_team_profile
                    profile_data = {
                        "Team Name": team_name,
                        "City": city,
                        "Founded Year": founded_year,
                        "Stadium": stadium,
                        "Coach": coach,
                        "Description": description,
                        "Website": website,
                        # Optionally store a CreatedOn if it's a new entry
                        "CreatedOn": datetime.now().strftime("%Y-%m-%d") if not existing_team else existing_team.get("CreatedOn", "")
                    }
                    success = update_team_profile(user_id, profile_data)
                    if success:
                        st.success("Team profile updated!")

        # --------------- Find Players ---------------
        elif menu == "Find Players":
            st.header("🔍 Advanced Player Search")

            with st.expander("Search Filters"):
                # ---- NEW: Name filter ----
                name_filter = st.text_input("Player Name (partial or full)")

                # Existing filters
                cols = st.columns(3)
                position_filter = cols[0].selectbox("Position", ["All", "Goalkeeper", "Defender", "Midfielder", "Forward"])
                min_age, max_age = cols[1].slider("Age Range", 16, 40, (16, 40))
                min_height, max_height = cols[2].slider("Height (cm)", 150, 220, (150, 220))

                st.subheader("Performance Metrics")
                cols = st.columns(3)
                min_agility = cols[0].slider("Min Agility", 0, 5, 0)
                min_power = cols[1].slider("Min Power", 0, 5, 0)
                min_speed = cols[2].slider("Min Speed", 0, 5, 0)

            if st.button("Search Players"):
                # Pass the name_filter as the first argument
                st.session_state.search_results = search_players(
                    name_filter, 
                    position_filter if position_filter != "All" else None,
                    min_age, max_age,
                    min_height, max_height,
                    min_agility, min_power, min_speed
                )

            # ... The rest of your code to display st.session_state.search_results ...
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
            st_autorefresh(interval=2000, limit=100, key="chat_refresher")
            st.header("💬 Chat")

            current_user = st.session_state.user
            current_user_id = current_user['UserID']
            current_role = current_user['Role']

            # Get potential chat partners with caching
            @st.cache_data(ttl=60)
            def get_chat_partners( current_user_id):
                all_users = get_all_users()
                return [u for u in all_users if str(u['UserID']) != str(current_user_id)]

            other_users = get_chat_partners(current_user_id)
            
            if not other_users:
                st.info("🚫 No users available to chat with.")
                return

            # User selection with search capability
            selected_user_email = st.selectbox(
                "Select user to chat with:",
                options=[u['Email'] for u in other_users],
                help="Start typing to search for users"
            )
            selected_user = next(u for u in other_users if u['Email'] == selected_user_email)
            selected_user_id = selected_user['UserID']

            # Chat container styling
            chat_container = st.container()
            
            # Get and display messages with loading state
            with st.spinner("Loading messages..."):
                chat_records = get_chat_between_users(current_user_id, selected_user_id)
                # Sort messages by timestamp
                chat_records = sorted(chat_records, key=lambda x: x['Timestamp'])

            with chat_container:
                st.subheader(f"💬 Conversation with {selected_user_email}")
                
                if not chat_records:
                    st.markdown("---")
                    st.info("No messages yet. Start the conversation!")
                    st.markdown("---")
                else:
                    for c in chat_records:
                        is_current_user = str(c['SenderID']) == str(current_user_id)
                        sender = get_user_by_id(c['SenderID'])
                        timestamp = datetime.strptime(c['Timestamp'], "%Y-%m-%d %H:%M:%S").strftime("%b %d, %H:%M")
                        
                        # Message bubble styling
                        if is_current_user:
                            st.markdown(f"""
                            <div style="display: flex; justify-content: flex-end; margin: 5px 0;">
                                <div style="background: #007bff; color: white; border-radius: 15px; padding: 8px 12px; max-width: 70%;">
                                    <div style="font-size: 0.8em; opacity: 0.7;">You • {timestamp}</div>
                                    {c['Message']}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="display: flex; justify-content: flex-start; margin: 5px 0;">
                                <div style="background: #e9ecef; color: black; border-radius: 15px; padding: 8px 12px; max-width: 70%;">
                                    <div style="font-size: 0.8em; opacity: 0.7;">{sender['Email']} • {timestamp}</div>
                                    {c['Message']}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

            # Message input with enhanced features
            with st.form("send_message_form", clear_on_submit=True):
                new_msg = st.text_area(
                    "Type your message:",
                    key="message_input",
                    height=100,
                    placeholder="Write your message here... (Shift+Enter for new line)"
                )
                
                cols = st.columns([5, 1])
                with cols[1]:
                    send_clicked = st.form_submit_button(
                        "✈️ Send",
                        help="Send message (Ctrl/Cmd + Enter)"
                    )
                    
                if send_clicked and new_msg.strip():
                    # Show sending status
                    with st.spinner("Sending..."):
                        send_message(current_user_id, selected_user_id, new_msg.strip())
                        # Auto-scroll to bottom after sending
                        st.rerun(scope="app")
                        
                elif send_clicked and not new_msg.strip():
                    st.warning("Message cannot be empty!")

            # JavaScript for auto-scroll to bottom
            components.html(
                """
                <script>
                window.addEventListener('load', function() {
                    window.parent.document.querySelectorAll('[data-testid="stVerticalBlock"]')[5].scrollTop = 999999;
                });
                </script>
                """,
                height=0
            )
                # --------------- Admin Panel ---------------
       
        elif menu == "Admin Panel" and is_admin(st.session_state.user):
            st.header("🔑 Admin Panel")
            st.write("Manage users, roles, teams, **and players** here.")

            # -----------------------------------------------------------------
            # Example: Manage Players
            # -----------------------------------------------------------------
            st.subheader("Add New Player")
            with st.form("AddPlayerForm"):
                new_first_name = st.text_input("First Name")
                new_last_name = st.text_input("Last Name")
                new_position = st.selectbox(
                    "Position", 
                    ["Goalkeeper", "Defender", "Midfielder", "Forward"]
                )

                # Basic fields
                c1, c2, c3 = st.columns(3)
                new_age = c1.number_input("Age", 16, 40, 20)
                new_height = c2.number_input("Height (cm)", 150, 220, 175)
                new_weight = c3.number_input("Weight (kg)", 50, 120, 70)

                # Performance metrics
                new_agility = st.slider("Agility", 0, 5, 3)
                new_power = st.slider("Power", 0, 5, 3)
                new_speed = st.slider("Speed", 0, 5, 3)

                # Extra fields
                new_bio = st.text_area("Bio")
                new_video_links = st.text_input("Video Links (comma-separated)")
                new_email = st.text_input("Email (optional or required, your choice)")
                new_lft = st.checkbox("Looking For A Team", value=True)

                if st.form_submit_button("Add Player"):
                    if new_first_name.strip() and new_last_name.strip():
                        success, msg = admin_add_player(
                            new_first_name, new_last_name, new_position, 
                            new_age, new_height, new_weight, new_email,
                            new_agility, new_power, new_speed,
                            new_bio, new_video_links, new_lft
                        )
                        if success:
                            st.success(msg)
                        else:
                            st.error("Failed to add player.")
                    else:
                        st.warning("First and Last Name are required.")       

            st.subheader("Existing Players")

            all_players = get_all_players()
            if not all_players:
                st.info("No players found.")
            else:
                # 1) Add a text input for name search
                name_query = st.text_input("Search players by name (partial or full)")

                # 2) Filter players if there's a search query
                if name_query:
                    name_query_lower = name_query.lower()
                    filtered_players = []
                    for p in all_players:
                        full_name = (p["First Name"] + " " + p["Last Name"]).lower()
                        if name_query_lower in full_name:
                            filtered_players.append(p)
                else:
                    # If no query, show all players
                    filtered_players = all_players

                # 3) Display the filtered list
                if not filtered_players:
                    st.warning("No players match your search.")
                else:
                    for player in filtered_players:
                        p_id = player["UserID"]
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
                        looking_for_team = (str(player["Looking For A Team"]).lower() in ["true", "1", "yes"])

                        with st.expander(f"Player {p_id}: {first_name} {last_name}", expanded=False):
                            st.write(f"**Position:** {position}, **Age:** {age}")
                            
                            # Admin can override fields
                            c1, c2, c3 = st.columns(3)
                            new_first_name = c1.text_input(
                                "First Name",
                                value=first_name,
                                key=f"fname_{p_id}"
                            )
                            new_last_name = c2.text_input(
                                "Last Name",
                                value=last_name,
                                key=f"lname_{p_id}"
                            )
                            new_position = c3.selectbox(
                                "Position",
                                ["Goalkeeper", "Defender", "Midfielder", "Forward"],
                                index=["Goalkeeper", "Defender", "Midfielder", "Forward"].index(position)
                                if position in ["Goalkeeper", "Defender", "Midfielder", "Forward"]
                                else 0,
                                key=f"pos_{p_id}"
                            )

                            colA, colB, colC = st.columns(3)
                            new_age = colA.number_input(
                                "Age", 16, 50,
                                int(age) if str(age).isdigit() else 20,
                                key=f"age_{p_id}"
                            )
                            new_height = colB.number_input(
                                "Height (cm)", 100, 250,
                                int(height) if str(height).isdigit() else 170,
                                key=f"height_{p_id}"
                            )
                            new_weight = colC.number_input(
                                "Weight (kg)", 30, 150,
                                int(weight) if str(weight).isdigit() else 70,
                                key=f"weight_{p_id}"
                            )

                            new_email = st.text_input("Email", value=email, key=f"email_{p_id}")
                            new_agility = st.slider("Agility", 0, 5, int(agility), key=f"agility_{p_id}")
                            new_power = st.slider("Power", 0, 5, int(power), key=f"power_{p_id}")
                            new_speed = st.slider("Speed", 0, 5, int(speed), key=f"speed_{p_id}")

                            new_bio = st.text_area("Bio", value=bio, key=f"bio_{p_id}")
                            new_video_links = st.text_input("Video Links", value=video_links, key=f"videos_{p_id}")
                            new_lft = st.checkbox("Looking For A Team?", value=looking_for_team, key=f"lft_{p_id}")

                            # Update & delete buttons
                            update_col, delete_col = st.columns([1,1])
                            if update_col.button(f"Update Player {p_id}", key=f"update_{p_id}"):
                                success, msg = admin_update_player(
                                    p_id, new_first_name, new_last_name, new_position,
                                    new_age, new_height, new_weight, new_email,
                                    new_agility, new_power, new_speed, new_bio,
                                    new_video_links, new_lft
                                )
                                if success:
                                    st.success(msg)
                                    st.rerun(scope="app")
                                else:
                                    st.error(msg)

                            if delete_col.button(f"Delete Player {p_id}", key=f"delete_{p_id}"):
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
                # 1) Name-based search
                name_search = st.text_input("Search teams by name (partial or full)")

                # 2) Filter teams if there's a search query
                if name_search:
                    query_lower = name_search.lower()
                    filtered_teams = [team for team in teams if query_lower in team["TeamName"].lower()]
                else:
                    filtered_teams = teams

                # 3) If no matches, warn. Otherwise, show results as before.
                if not filtered_teams:
                    st.warning("No teams match your search.")
                else:
                    for t in filtered_teams:
                        # Display each team in a collapsible expander
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
                            ["Player", "Scout", "Team", "Admin"], 
                            index=["Player", "Scout", "Team", "Admin"].index(user_role)
                            if user_role in ["Player", "Scout", "Team", "Admin"] else 0,
                            key=f"role_select_{user_id}"
                        )

                        if new_role != user_role:
                            if st.button(f"Update Role for User {user_id}", key=f"role_btn_{user_id}"):
                                if update_user_role(user_id, new_role):
                                    st.success(f"Role updated for user {user_email} to {new_role}")
                                    st.rerun(scope="app")

                        # Example: update email
                        new_email = st.text_input("Email", value=user_email, key=f"user_email_{user_id}")
                        if new_email != user_email:
                            if st.button(f"Update Email for User {user_id}", key=f"email_btn_{user_id}"):
                                success, msg = update_user_email(user_id, new_email)
                                if success:
                                    st.success(msg)
                                    st.rerun(scope="app")
                                else:
                                    st.error(msg)

                        # Delete user
                        if st.button(f"Delete User {user_id}", key=f"delete_user_{user_id}"):
                            delete_user(user_id)
                            st.warning(f"User {user_email} deleted.")
                            st.rerun(scope="app")


        else:
            # If user tries to access Admin Panel but is not admin
            st.error("You do not have permission to view this page.")

if __name__ == "__main__":
    main()
