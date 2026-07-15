from scrapling.fetchers import Fetcher, DynamicFetcher, DynamicSession
from scrapling.parser import Selector
from playwright.sync_api import Page


START_PAGE_NUM = 3
END_PAGE_NUM = 5

PREMIER_LEAGUE_URL = "https://www.premierleague.com"
PLAYERS_LISTING_URL = f"{PREMIER_LEAGUE_URL}/en/players?competition=8&season=2026"

GLOBAL_ADP_SELECTOR = ".global-ad-slot"
PLAYER_TABLE_SELECTOR = ".player-listings-table__table-body"
PLAYER_ROW_SELECTOR = ".player-listings-row"
PLAYER_NAME_SELECTOR = ".player-listings-row__player-name"
PLAYER_CLUB_SELECTOR = ".player-listings-row__club"
PLAYER_POSITION_SELECTOR = ".player-listings-row__data--position"
PLAYER_NATIONALITY_SELECTOR = ".player-listings-row__country"
PLAYER_URL_SELECTOR = ".player-listings-row__player"
PAGE_NAVIGATION_SELECTOR = ".player-listings-table__navigation"
COOKIE_ACCEPT_BUTTON_SELECTOR = "#onetrust-accept-btn-handler"

pages = []

def click_accept_cookies(page: Page):
  accept_button = page.query_selector(COOKIE_ACCEPT_BUTTON_SELECTOR)
  if accept_button:
    accept_button.click()
    return True
  return False

def click_next_page_button(page: Page):
  nav_buttons = page.query_selector(PAGE_NAVIGATION_SELECTOR).query_selector_all("button")
  next_button = None
  
  # check which button is the "Next" button based on the aria-label attribute
  if nav_buttons[1].get_attribute("aria-label") == "Next":
    next_button = nav_buttons[1]
  elif nav_buttons[0].get_attribute("aria-label") == "Next":
    next_button = nav_buttons[0]
  
  if next_button:
    if next_button.is_enabled():
      next_button.click()
      return True
  return False

def automation(page: Page):
  '''Automate the process of accepting cookies and navigating through pages.'''
  ret = click_accept_cookies(page)
  if not ret:
    print("No cookies button found or already accepted.")
  else:
    print("Cookies accepted.")
  
  # Navigate to the start page
  for _ in range(START_PAGE_NUM - 1):
    page.wait_for_selector(PLAYER_TABLE_SELECTOR)  # Ensure the player table is loaded
    ret = click_next_page_button(page)
    if not ret:
      print("No more pages to navigate.")
      break
    else:
      print("Skip to next page.")
  
  for _ in range(START_PAGE_NUM, END_PAGE_NUM + 1):
    page.wait_for_selector(PLAYER_TABLE_SELECTOR)  # Ensure the player table is loaded
    pages.append(Selector(page.content()))  # Store the current page's content for later parsing
    
    ret = click_next_page_button(page)
    if not ret:
      print("No more pages to navigate.")
      break
    else:
      print("Navigated to next page.")


# Create a session to fetch the pages with automation
with DynamicSession(headless=False, disable_resources=False, timeout=300000) as session:
  session.fetch(
    PLAYERS_LISTING_URL,
    page_action=automation,
  );


# Extract player data from each page
def get_player_data(player: Selector):
    player_data = {}
    player_data["name"] = player.css(PLAYER_NAME_SELECTOR).first.get_all_text().strip()
    player_data["club"] = player.css(PLAYER_CLUB_SELECTOR).first.get_all_text().strip()
    player_data["position"] = player.css(PLAYER_POSITION_SELECTOR).first.get_all_text().strip()
    player_data["nationality"] = player.css(PLAYER_NATIONALITY_SELECTOR).first.get_all_text().strip()
    player_data["url"] = PREMIER_LEAGUE_URL + player.css(PLAYER_URL_SELECTOR).first.attrib["href"]
    return player_data


# Print the extracted player data
for i, page in enumerate(pages, start=START_PAGE_NUM):
  print(f"Page {i}:")
  players_data = []
  players_table = page.css(PLAYER_TABLE_SELECTOR).first

  players = players_table.css(PLAYER_ROW_SELECTOR)
  players_data = [get_player_data(player) for player in players]

  for player in players_data:
    print(player["name"], player["club"], player["position"], player["nationality"], player["url"], sep=", ")
