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
    new_list_ps = [{'externalId': d['externalId'], 'price': d['price']['playstation-4']} for d in response]
    new_list_xb = [{'externalId': d['externalId'], 'price': d['price']['xbox-one']} for d in response]
    sorted_array_ps = sorted(new_list_ps, key=lambda x: IDsSnip.index(str(x['externalId'])))
    sorted_array_xb = sorted(new_list_xb, key=lambda x: IDsSnip.index(str(x['externalId'])))
    price_range_ps = "F" + str(starting_point) + ":" + "F" + str(iteration_counter)
    price_range_xb = "M" + str(starting_point) + ":" + "M" + str(iteration_counter)
    cell_list_ps = worksheet.range(price_range_ps)
    for cell, i in zip(cell_list_ps, sorted_array_ps):
      if i['price'] is None or i['price'] == "None":
        cell.value = ""
      elif type(i['price']) == str:
        cell.value = int(i['price'])
      else:
        cell.value = i['price']
    worksheet.update_cells(cell_list_ps)
    cell_list_xb = worksheet.range(price_range_xb)
    for cell, i in zip(cell_list_xb, sorted_array_xb):
      if i['price'] is None or i['price'] == "None":
        cell.value = ""
      elif type(i['price']) == str:
        cell.value = int(i['price'])
      else:
        cell.value = i['price']
    worksheet.update_cells(cell_list_xb)
    IDsSnip.clear()
    sorted_array_ps.clear()
    sorted_array_xb.clear()
    new_list_ps.clear()
    new_list_xb.clear()
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
