# ~ 4-5 mins per run
# TODO: Make faster, hide creds

import gspread
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
import time
import pytz
import datetime
import os

start_time = time.time()

# ENV Variables
creds_json = os.environ['CREDS']
CREDS = json.loads(creds_json)
SHEET_NAME = os.environ['SHEET_NAME']
API_URL = os.environ['API_URL']
SCRAPE_URL = os.environ['SCRAPE_URL']

gc = gspread.service_account_from_dict(CREDS)
sheet = gc.open(SHEET_NAME)
worksheet = sheet.worksheet("Master")

last_row = len(worksheet.get_all_values())
last_col = worksheet.row_values(last_row)

while all(val == "" for val in last_col):
    last_row -= 1
    last_col = worksheet.row_values(last_row)

IDs = []
place_counter = 0
new_players = []
url = SCRAPE_URL
base_url = API_URL
pagecounter = 1
data = worksheet.get_all_values()

for row in data:
  IDs.append(row[6])
  
IDs.pop(0)

while True:
    updated_url = url + str(pagecounter)
    page = requests.get(updated_url)
    soup = BeautifulSoup(page.content, 'html.parser')
    pagination_elements = soup.find_all(class_='pagination__link')
    for button in pagination_elements:
        if "Next" in button.text:
            next_page_element = button
        else:
            next_page_element = False
    name_first = soup.find_all(class_='player-list-item__name-first')
    name_last = soup.find_all(class_='player-list-item__name-last')
    overalls = soup.find_all(class_='player-list-item__score-value')
    id_elements = soup.find_all(class_='player-list-item__link')
    programs = soup.find_all(class_='player-list-item__program')
    positions = soup.find_all(class_='player-list-item__archetype')

    name_first_texts = [element.text for element in name_first]
    name_last_texts = [element.text.strip().replace('\n', '') for element in name_last]
    overalls_texts = [element.text.strip().replace('\n', '') for element in overalls]
    id_hrefs = [element['href'] for element in id_elements]
    ids = [s[s.rindex('-')+1:-1] for s in id_hrefs]
    programs_texts = [element.text for element in programs]
    positions_text = [element.text.split(' - ')[0].strip() for element in positions]
    
    for first, last, overall, i, program, position in zip(name_first_texts, name_last_texts, overalls_texts, ids, programs_texts, positions_text):
        if i not in IDs:
            fullname = (first + " " + last)
            new_players.append({
                "ExternalID": i,
                "Name": fullname,
                "Overall": overall,
                "Program": program,
                "Position": position,
                'Price': 0
            })
            base_url += i + "%2C"
            
    if next_page_element:
        pagecounter = pagecounter + 1
    else:
        break
    
base_url = base_url[:-3]

api_call = requests.get(base_url)
api_json = api_call.json()
counter = last_row

for player in new_players:
    for t in api_json['data']:
        externalID_Response = t['externalId']
        if str(externalID_Response) == player['ExternalID']:
            if t['price']['playstation-4'] == "Unknown":
                player['Price'] = 0
            else:
                player['Price'] = t['price']['playstation-4']  
    
    update_range = worksheet.range(counter + 1, 2, counter + 1, 7)
    cell_counter = 0
    
    for cell in update_range:
        cell_counter += 1
        if cell_counter == 1:
            cell.value = player['Name']
        elif cell_counter == 2:
            cell.value = int(player['Overall'])
        elif cell_counter == 3:
            cell.value = player['Program']
        elif cell_counter == 4:
            cell.value = player['Position']
        elif cell_counter == 5:
            cell.value = player['Price']
        elif cell_counter == 6:
            cell.value = int(player['ExternalID'])
            counter += 1
    
    if counter == 60:
        time.sleep(60)
    
    worksheet.update_cells(update_range)            
  
worksheet.sort((3, 'des'))

now = datetime.datetime.now()
est = pytz.timezone('US/Eastern')
now_est = now.astimezone(est)

short_date = now_est.strftime("%m/%d/%y")
current_time = now_est.strftime("%I:%M %p")

worksheet.update_acell('A2', "Players Updated: " + short_date + " " + current_time)

print(new_players)

print("--- %s seconds ---" % (time.time() - start_time)) 
