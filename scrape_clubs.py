import requests
from bs4 import BeautifulSoup
import sqlite3
import time

# Database setup
def setup_database():
    conn = sqlite3.connect("clubs.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clubs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            club_id INTEGER UNIQUE,
            club_code TEXT,
            club_name TEXT
        )
    """)
    conn.commit()
    return conn

# Function to scrape a single club page
def scrape_club_page(club_id):
    url = f"https://rfegolf.es/ClubPaginas/ClubMicrosite.aspx?ClubId={club_id}"
    response = requests.get(url)

    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract club code
    club_code_span = soup.find("span", id="ctl00_m_g_8f33b236_8d4d_4ed3_9f12_5cb8b11142ed_ctl00_TabContainer1_TabElClub_lblCodigoFederativo")
    club_code = club_code_span.text.strip() if club_code_span else None

    # Extract club name
    club_name_div = soup.find("div", id="ctl00_m_g_8f33b236_8d4d_4ed3_9f12_5cb8b11142ed_ctl00_dvClubName")
    club_name = club_name_div.text.strip() if club_name_div else None

    if club_code and club_name:
        return {
            "club_id": club_id,
            "club_code": club_code,
            "club_name": club_name
        }
    return None

# Function to save club data to the database
def save_to_database(conn, club_data):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO clubs (club_id, club_code, club_name)
            VALUES (?, ?, ?)
        """, (club_data["club_id"], club_data["club_code"], club_data["club_name"]))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Club ID {club_data['club_id']} already exists in the database.")

# Main function to iterate through club IDs
def main():
    conn = setup_database()

    for club_id in range(1090, 2001):
        print(f"Scraping Club ID: {club_id}")
        club_data = scrape_club_page(club_id)

        if club_data:
            print(f"Found: {club_data}")
            save_to_database(conn, club_data)
        else:
            print(f"Club ID {club_id} not found or missing data.")

        # To avoid overwhelming the server, add a delay between requests
        time.sleep(0.5)

    conn.close()

if __name__ == "__main__":
    main()
