import datetime
import pandas as pd
import json
import urllib
import urllib.request
import requests
import time
import subprocess
import sys
# from telegram import Update
# from telegram.ext import CallbackContext, PollAnswerHandler, PollHandler
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import argparse
import os
import pickle
from pathlib import Path

date = datetime.datetime.now().strftime("%d-%m-%Y")
def save_loc_people():
    with open(people_path, 'wb') as f: 
        pickle.dump(loc_people, f)

def save_locations():
    with open(location_path, 'wb') as f: 
        pickle.dump(locations, f)


my_headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36",
              "accept": "application/json"}

class Response:
    def __init__(self):
        self.status_code = 0

def run_telegram():
    "Run Telegram"
    location_output = dict()
    updater = Updater(token=token, use_context=True)

    dispatcher = updater.dispatcher

        
    start_handler = CommandHandler('start', start)

    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)

    updater.start_polling()
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(echo_handler)
    while True:
        prev_location_output = location_output.copy()
        location_output = dict()
        for i in loc_people:
            for location in loc_people[i]:
                response = Response()
                if location in location_output.keys():
                    continue
                try:
                    response = requests.get("https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id="+str(locations[location])+"&date="+date, headers=my_headers)
                    data = response.json()
                    location_y = []
                    for center in data["centers"]:
                        #print(center)
                        for session in center["sessions"]:
                            if session["min_age_limit"] == 18:
                                if session["available_capacity"] > 0:
                                    location_y.append({"id": center["center_id"], "state_name": center["state_name"], "district_name": center["district_name"],"name": center["name"], "address": center["address"], "vaccine": session["vaccine"], "available_capacity": session["available_capacity"]})
                    location_output[location] = location_y.copy()
                except Exception as e:
                    if e is KeyboardInterrupt:
                        save_loc_people()
                        sys.exit(1)
                    continue
        # print(location_output)
        for i in loc_people:
            if i == "default":
                continue
            for location in loc_people[i]:
                try:
                    updated = prev_location_output[location] != location_output[location]
                except Exception as e:
                    updated = True
                    if e is KeyboardInterrupt:
                        save_loc_people()
                        sys.exit(1)
                    # print(updated)
                if updated:
                    try:
                        # print("reached")
                        centers = location_output[location]
                        if not args.interactive:
                            print(centers)
                        for center in centers:
                            text = center['state_name']+"\n"+center["district_name"]+"\n"+center["name"]+"\n"+"Address: "+center["address"]+"\n"+center["vaccine"]+": " + str(center["available_capacity"])
                            dispatcher.bot.send_message(chat_id=i, text=text)
                            # print(requests.status_code)
                    except:
                        pass
        
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            save_loc_people()
            sys.exit(1)
        # print("Okay")


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a covid19 vaccine tracking. ")
    if args.telegramallow:
        loc_people[str(update.effective_chat.id)] = []
        save_loc_people()
        context.bot.send_message(chat_id=update.effective_chat.id, text="You have been added to my list of known people. You can now send me a comma separated list of districts you want to track. Or you can incrementally add districts by add, district-name")

    elif args.interactive:
        if str(input("Would you like to add " + str(update.effective_chat.first_name) + "(" + str(update.effective_chat.id) + ") ? (y/n): ")) == "y":
            loc_people[str(update.effective_chat.id)] = []
            save_loc_people()
            context.bot.send_message(chat_id=update.effective_chat.id, text="You have been added to my list of known people. You can now send me a comma separated list of districts you want to track. Or you can incrementally add districts by add, district-name")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry the user has disabled automatic adding of users")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry the user has disabled automatic adding of users")
    # print(update,context)

def echo (update, context):
    # print("Hello")
    if str(update.effective_chat.id) in loc_people.keys():
        # print("reached")
        temp = list(map(str.strip, update.message.text.lower().split(',')))
        
        if temp[0] != 'add':
            if temp[0] == 'get':
                context.bot.send_message(chat_id=update.effective_chat.id, text=str(loc_people[str(update.effective_chat.id)]))
                return
            temp3 = [x for x in temp if x in locations.keys()]
            loc_people[str(update.effective_chat.id)] = list(set(temp3))
            context.bot.send_message(chat_id=update.effective_chat.id, text="Tracking Locations:"+ str(temp3))
            
        else:
            temp2 = loc_people[str(update.effective_chat.id)]
            
            temp3 = [x for x in temp[1:] if x in locations.keys()]
            for district in temp3:
                temp2.append(district)
            loc_people[str(update.effective_chat.id)] = list(set(temp2))
            context.bot.send_message(chat_id=update.effective_chat.id, text="Tracking Locations:"+ str(temp2))
        save_loc_people()
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--telegram', default=False, action="store_true")
    parser.add_argument('--interactive', default=False, action="store_true")
    parser.add_argument('--telegramallow', default=False, action="store_true")
    parser.add_argument('--init', default=False, action="store_true")
    parser.add_argument('--token') # Token
    parser.add_argument('--tokenfile') # Token File
    parser.add_argument('--p') # People File
    parser.add_argument('--l') # Location File
    args = parser.parse_args()
    if args.token:
        token = args.token
    elif args.tokenfile:
        with open(args.tokenfile, "rb") as f:
            token = f.read()
    else:
        if Path("./.token").exists():
            with open("./.token", "rb") as f:
                token = f.read()
        else:
            print("No token provided!")
            sys.exit(1)
    if args.init:
        pass
    if args.p:
        people_path=args.p
    else:
        people_path=os.path.expanduser('./.people.vaccine')
    if args.l:
        location_path=args.l
    else:
        location_path=os.path.expanduser('./.location.vaccine')
    try:
        with open(location_path, "rb") as f:
            locations = pickle.load(f)
    except:
        locations = {}
        response = requests.get("https://cdn-api.co-vin.in/api/v2/admin/location/states" , headers=my_headers)
        data = response.json()
        for i in data['states']:
            response = requests.get("https://cdn-api.co-vin.in/api/v2/admin/location/districts/" + str(i['state_id']), headers=my_headers)
            data =response.json()
            for j in data['districts']:
                locations[j['district_name'].lower()] = j['district_id']
        save_locations()
        # print(locations)
    try:
        with open(people_path, 'rb') as f:  
            loc_people = pickle.load(f)
    except:
        print("No People File!")
        loc_people = {}
        inp = [x for x in list(map(str.lower, list(map(str.strip, input("Districts (comma separated): ").split(','))))) if x in locations.keys()]
        loc_people["default"] = inp
        save_loc_people()
    if args.telegram:
        run_telegram()
