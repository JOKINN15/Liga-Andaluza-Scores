import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
from datetime import datetime
import os

username = os.getenv('GOLF_USER')
password = os.getenv('GOLF_PASSWORD')

# Create an engine and base class for the ORM
Base = declarative_base()
golf_engine = create_engine('sqlite:///golf.db', echo=True)  # SQLite database file for golf
golf_session = sessionmaker(bind=golf_engine)()

# Separate engine for clubs database
clubs_engine = create_engine('sqlite:///clubs.db', echo=True)  # SQLite database file for clubs
clubs_session = sessionmaker(bind=clubs_engine)()

# Player model
class Player(Base):
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    license = Column(String(50), unique=True, nullable=False)
    nickname = Column(String(50), nullable=False)
    current_handicap = Column(Float, nullable=False, default=0.0)
    handicap_galactico = Column(Float, nullable=False, default=0.0)
    results = relationship('Result', backref='player', lazy=True)

# Result model
class Result(Base):
    __tablename__ = 'results'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    fecha = Column(String(20), nullable=False)  # Date
    club = Column(String(50), nullable=False)  # Club name
    nombre_torneo = Column(String(100), nullable=False)  # Tournament name
    nivel = Column(String(5), nullable=False)  # Level
    jornada = Column(Integer, nullable=False)  # Match round
    res_hcp = Column(Integer, nullable=True)  # Handicap result
    res_sch = Column(String(20), nullable=True)  # Result SCH
    dif_neto = Column(Integer, nullable=True)  # Net difference (integer, can be negative or 0)
    res_stb = Column(Integer, nullable=True)  # Net difference (integer, can be negative or 0)
    mod_jue = Column(String(10), nullable=True)  # Game mode
    form_calc = Column(String(5), nullable=True)  # Calculation formula
    hcp_ini = Column(Float, nullable=True)  # Initial handicap
    hcp_jue = Column(Float, nullable=True)  # Played handicap
    hcp_fin = Column(Float, nullable=True)  # Final handicap

class Club(Base):
        __tablename__ = 'clubs'
        id = Column(Integer, primary_key=True)
        club_id = Column(Integer, unique=True, nullable=False)
        club_code = Column(String(50), unique=True, nullable=False) 
        club_name = Column(String(100), nullable=False)

# Function to get club name from club code
def get_club_name_from_code(club_code):
    # Query the clubs table
    club = clubs_session.query(Club).filter_by(club_code=club_code).first()
    return club.club_name if club else f"Unknown Club ({club_code})"


# Function to load players from JSON and add to the database
def load_players_from_json(json_file):
    with open(json_file, 'r') as f:
        players_data = json.load(f)
    
    # Add players to the database
    golf_session.query(Player).delete()
    for player_data in players_data:
        player = Player(
            license=player_data['license'],
            nickname=player_data['nickname']
        )
        golf_session.add(player)
    golf_session.commit()

# Function to scrape and store results for players
def scrape_and_store_results():
    # Configure Selenium WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # Step 1: Log in and navigate to the main page
        login_url = 'https://rfegolf.es/PaginasServicios/areadeljugador.aspx'
        driver.get(login_url)
        time.sleep(2)

        # Perform login
        entrar_button = driver.find_element(By.ID, "ctl00_CabeceraGolf_imgAbrirLogin")
        driver.execute_script("arguments[0].click();", entrar_button)
        time.sleep(2)

        driver.find_element(By.ID, "ctl00_CabeceraGolf_login_UserName").send_keys(username)
        driver.find_element(By.ID, "ctl00_CabeceraGolf_login_password").send_keys(password)
        login_button = driver.find_element(By.ID, "ctl00_CabeceraGolf_login_login")
        driver.execute_script("arguments[0].click();", login_button)

        time.sleep(3)  # Wait for login to complete

        # Step 2: Navigate to "Área del Jugador"
        area_del_jugador_link = driver.find_element(By.ID, "ctl00_m_g_81dd4ba0_8871_48bd_83e5_76aca2e74970_ctl00_enlaceAJ")
        driver.execute_script("arguments[0].click();", area_del_jugador_link)
        time.sleep(3)

        # Step 3: Emulate click on "Ficha de actividad"
        ficha_actividad_link = driver.find_element(By.LINK_TEXT, "Ficha de actividad")
        driver.execute_script("arguments[0].click();", ficha_actividad_link)
        time.sleep(3)

        # Erase all records in the 'results' table
        golf_session.query(Result).delete()
        golf_session.commit()

        # Fetch players and their results
        players = golf_session.query(Player).all()

        for player in players:
            license = player.license
            search_input = driver.find_element(By.ID, "Ficha_Actividad1_TBLicencia")
            search_input.clear()
            search_input.send_keys(license)

            search_button = driver.find_element(By.ID, "Ficha_Actividad1_BConsLicencia")
            driver.execute_script("arguments[0].click();", search_button)
            time.sleep(10)

            # Step 4: Parse results
            rows = driver.find_elements(By.CSS_SELECTOR, "tr.item, tr.altern")  # Select tr elements with either class "named" or "alternate"
            first_10_rows = rows[:10]
            results = []
            for row in first_10_rows:
                columns = row.find_elements(By.TAG_NAME, "td")
                if len(columns) < 13:
                    continue

                fecha = columns[0].text.strip()
                club_code = columns[1].find_element(By.TAG_NAME, "span").text.strip()
                nombre_torneo = columns[2].find_element(By.TAG_NAME, "a").text.strip()
                nivel = columns[3].text.strip()
                jornada = int(columns[4].text.strip()) if columns[4].text.strip().isdigit() else None
                res_hcp = int(columns[5].text.strip()) if columns[5].text.strip().isdigit() else None
                res_sch = columns[6].text.strip()
                dif_neto = int(columns[7].text.strip()) if columns[7].text.strip().lstrip('-').isdigit() else None
                mod_jue = columns[8].text.strip()
                form_calc = columns[9].text.strip()
                hcp_ini = float(columns[10].text.strip()) if columns[10].text.strip() else None
                hcp_jue = float(columns[11].text.strip()) if columns[11].text.strip() else None
                hcp_fin = float(columns[12].text.strip()) if columns[12].text.strip() else None

                results.append({
                    "fecha": fecha,
                    "club_code": club_code,
                    "nombre_torneo": nombre_torneo,
                    "nivel": nivel,
                    "jornada": jornada,
                    "res_hcp": res_hcp,
                    "res_sch": res_sch,
                    "dif_neto": dif_neto,
                    "res_stb": dif_neto + 36,
                    "mod_jue": mod_jue,
                    "form_calc": form_calc,
                    "hcp_ini": hcp_ini,
                    "hcp_jue": hcp_jue,
                    "hcp_fin": hcp_fin
                })

            # Sort results by fecha (date) in descending order and select top 10
            results.sort(key=lambda x: datetime.strptime(x["fecha"], "%m/%Y"), reverse=True)
            top_10_results = results[:10]

            # Fetch club names only for top 10 results
            for result in top_10_results:
                result["club"] = get_club_name_from_code(result["club_code"])

            # Insert the results into the database
            for result_data in top_10_results:
                new_result = Result(
                    player_id=player.id,
                    fecha=result_data["fecha"],
                    club=result_data["club"],
                    nombre_torneo=result_data["nombre_torneo"],
                    nivel=result_data["nivel"],
                    jornada=result_data["jornada"],
                    res_hcp=result_data["res_hcp"],
                    res_sch=result_data["res_sch"],
                    dif_neto=result_data["dif_neto"],
                    res_stb=result_data["res_stb"],
                    mod_jue=result_data["mod_jue"],
                    form_calc=result_data["form_calc"],
                    hcp_ini=result_data["hcp_ini"],
                    hcp_jue=result_data["hcp_jue"],
                    hcp_fin=result_data["hcp_fin"]
                )
                golf_session.add(new_result)

            # After adding the results, update the player's current_handicap to the latest `hcp_fin`
            if results:
                player.current_handicap = top_10_results[0]["hcp_fin"]

            golf_session.commit()

            driver.back()  # Navigate back to the previous page
            time.sleep(5)

    finally:
        driver.quit()

if __name__ == "__main__":
    # Create the tables in the database (if they don't already exist)
    Base.metadata.create_all(golf_engine)

    # Load players from JSON and populate the database
    load_players_from_json('players.json')

    # Scrape and store results
    scrape_and_store_results()

    print("Scraping and database population completed!")