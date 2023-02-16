import requests
import gspread
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
import time
import datetime
import pytz
import os

start_time = time.time()

creds_json = os.environ['CREDS']
CREDS = json.loads(creds_json)
SHEET_NAME = os.environ['SHEET_NAME']

gc = gspread.service_account_from_dict(CREDS)
sheet = gc.open(SHEET_NAME)
worksheet = sheet.worksheet("Master")

base_url = os.environ['API_URL']

# get all IDs in order
IDs = []
data = worksheet.get_all_values()

for row in data:
  IDs.append(row[6])
  
IDs.pop(0)

IDsSnip = []
starting_point = 2
append_counter = 0
iteration_counter = 1
fields_to_keep = ["externalId", "price"]

while True:
  if append_counter == len(IDs):
    break
  
  if iteration_counter % 100 == 1 and iteration_counter != 1 or append_counter == len(IDs) - 1:
    base_url = base_url[:-3]
    api_call = requests.get(base_url)
    api_json = api_call.json()
    response = api_json['data']
    new_list = [{'externalId': d['externalId'], 'price': d['price']['playstation-4']} for d in response]
    sorted_array = sorted(new_list, key=lambda x: IDsSnip.index(str(x['externalId'])))
    price_range = "F" + str(starting_point) + ":" + "F" + str(iteration_counter)
    cell_list = worksheet.range(price_range)
    for cell, i in zip(cell_list, sorted_array):
      if i['price'] is None or i['price'] == "None":
        cell.value = ""
      elif type(i['price']) == str:
        cell.value = int(i['price'])
      else:
        cell.value = i['price']
    worksheet.update_cells(cell_list)
    IDsSnip.clear()
    sorted_array.clear()
    new_list.clear()
    base_url = os.environ['API_URL']
    starting_point = iteration_counter + 1
  
  IDsSnip.append(IDs[append_counter])
  base_url += IDs[append_counter] + "%2C"
  append_counter += 1
  iteration_counter += 1

now = datetime.datetime.now()
est = pytz.timezone('US/Eastern')
now_est = now.astimezone(est)

short_date = now_est.strftime("%m/%d/%y")
current_time = now_est.strftime("%I:%M %p")

worksheet.update_acell('A1', "Prices Updated: " + short_date + " " + current_time)

print("--- %s seconds ---" % (time.time() - start_time))   
