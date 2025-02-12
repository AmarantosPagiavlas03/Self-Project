import requests
from bs4 import BeautifulSoup
from django.utils.timezone import now
from scout_app.models import PlayerProfile, PlayerStatistics

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def scrape_players():
    """
    Scrape all players from the EPSATH players list page.
    """
    base_url = "https://www.epsath.gr/players/players.php"
    response = requests.get(base_url, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the main players table - adjust selector as needed
    table = soup.find('table')  # Update with actual table class
    players = []
    
    for row in table.find_all('tr')[0:]:  # Skip header row
        cols = row.find_all('td')
        if cols:
            link = cols[1].find('a')
            age = 2025 - int(cols[2].text.strip())
            if link:
                player_id = link['href'].split('=')[1]
                full_name = link.text.strip()
                print(full_name)
                
                # Split full name into first and last name
                first_name, last_name = full_name.split(' ', 1) if ' ' in full_name else (full_name, '')
                
                # Create or update player profile
                player_profile, created = PlayerProfile.objects.update_or_create(
                    user__email=f"{player_id}@epsath.gr",  # Use a unique email based on player_id
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'age': age,
                        # Add other fields if available
                    }
                )
                players.append(player_profile)
                # Scrape detailed stats for the player
                scrape_player_stats(player_profile, player_id)


    return players

def scrape_player_stats(player_profile, player_id):
    """
    Scrape detailed statistics for a specific player.
    """
    stats_url = f"https://www.epsath.gr/players/display_player.php?player_id={player_id}"
    response = requests.get(stats_url, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the statistics table
    stats_table = soup.find('div', {'class': 'table'})  # Update with actual class
    
    if stats_table:
        season = soup.find('h4').text.strip().split(' ')[-1]
        stats = parse_player_stats_table(stats_table)
        
        # Create or update PlayerStatistics
        PlayerStatistics.objects.update_or_create(
            player_profile=player_profile,
            season=season,  # Adjust season as needed
            defaults={
                'goals': int(stats.get('fkoa', 0)),
                'own_goals': int(stats.get('autogkol', 0)),
                'yellow_cards': int(stats.get('kitrines', 0)),
                'red_cards': int(stats.get('kokkines', 0)),
                'minutes_played': stats.get('lepta_symmetoxis', "0'"),
                'goal_every': stats.get('fkoa_kathe', '--'),
                'own_goal_every': stats.get('autogkol_kathe', '--'),
                'yellow_card_every': stats.get('kitrini_kathe', '--'),
                'red_card_every': stats.get('kokkini_kathe', '--'),
            }
        )

def parse_player_stats_table(table):
    """
    Parse the player statistics table from the HTML content.
    Returns a dictionary with the extracted stats.
    """
    # print(table)
    stats = {}

    # Find all rows in the table body
    rows = table.find_all('tr')
    # Second row contains the corresponding values
    values_row_0 = [td.text.strip() for td in rows[0].find_all('td')]
    values_row_1 = [td.text.strip() for td in rows[1].find_all('td')]

    # Extract stats based on column index
    stats['fkoa'] = values_row_0[0]
    stats['autogkol'] = values_row_0[1]
    stats['kitrines'] = values_row_0[2]
    stats['kokkines'] = values_row_0[3]
    stats['lepta_symmetoxis'] =values_row_0[4]
    stats['fkoa_kathe'] = values_row_1[0]
    stats['autogkol_kathe'] = values_row_1[1]
    stats['kitrini_kathe'] = values_row_1[2]
    stats['kokkini_kathe'] = values_row_1[3]

    
    return stats