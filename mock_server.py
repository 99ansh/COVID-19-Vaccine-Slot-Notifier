
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from flask import Flask
from flask import request
from concurrent.futures import ThreadPoolExecutor

import time
from datetime import datetime
import pymongo
import pandas as pd
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import pika
import json
import pickle
import user_queries
import sys

def start():
    try:
        
        now = datetime.now() # current date and time
        date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
        print("initial date and  time:",date_time)

        client = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
        db = client["temp"]
        slots = db["slots"]
        slots.remove({})

        chrome_options=webdriver.ChromeOptions()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        # chrome_options.add_argument('--ignore-certificate-errors')
        # chrome_options.add_argument('--allow-running-insecure-content')
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
        chrome_options.add_argument(f'user-agent={user_agent}')
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://www.cowin.gov.in/")
        time.sleep(5)
        print("hello")
        print(driver,db)
        return [driver,db]
    except Exception as e:
        return

def find_vaccination_slots(driver,db):
    now = datetime.now() # current date and time
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    print("initial date and  time:",date_time)
    
    slots = db["slots"]
    flag2=0
    try:
        with open("ids_left.pickle","rb") as file:
            ids_left=pickle.load(file)
            print("Old data remaining")
            flag=1

        # removing already visited district therefore for state list is empty 
        ids={}
        for x in ids_left:
            if ids_left[x]!=[]:
                ids[x]=ids_left[x]

        with open("state_final.pickle","rb") as file:
            state_final=pickle.load(file)
        with open("district_final.pickle","rb") as file:
            district_final=pickle.load(file)
    except Exception as e:
        print(e)
        print("No old data remaining")
        flag=0

    if flag==0:
        states_districts = user_queries.get_users()
        #calculate a and b
        state_district_ids = db["states_districts"]
        ids={}
        state_final={} #because of spelling
        district_final={} #because of spelling
        # print(states_districts)
        for query in states_districts:
            state = query[0]
            district = query[1]
            # print(state,district)
            obj = state_district_ids.find_one({"state_name":state,"district_name":district})
            # print(obj)
            custom_state_id = obj["custom_state_id"]
            custom_district_id = obj["custom_district_id"]
            actual_district_id = obj["actual_district_id"]
            state_final[custom_state_id]=state
            district_final[actual_district_id]=district
            if custom_state_id in ids:
                ids[custom_state_id].append((custom_district_id,actual_district_id))
            else:
                ids[custom_state_id]=[(custom_district_id,actual_district_id)]

    #Find by State and District
    path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[2]/div/label/div"
    path="/html/body/app-root/div/app-home/div[3]/div/appointment-table/div/div/div/div/div/div/div/div/div/div/form/mat-tab-group/mat-tab-header/div[2]/div/div/div[2]/div"
    searchElement = WebDriverWait(driver,180).until(lambda d: d.find_element_by_xpath(path))
    driver.execute_script("arguments[0].click();",searchElement)
    print(searchElement.text)

    # print(ids)
    # print(state_final)
    # print(district_final)

    # 1. looping over all the states as per user query
    for custom_state_id in ids:
        state=state_final[custom_state_id]
        # print(state)
        try:  
            time.sleep(3) #essential for getting states
            #select state dropdown
            
            path="/html/body/app-root/div/app-home/div[3]/div/appointment-table/div/div/div/div/div/div/div/div/div/div/form/mat-tab-group/div/mat-tab-body[2]/div/div/div[1]/mat-form-field/div/div[1]/div/mat-select"
            element = WebDriverWait(driver,5).until(lambda d: d.find_element_by_xpath(path))
            #print("clicked for state:"+element.text)
            driver.execute_script("arguments[0].click();",element)
            #Select state  
            time.sleep(2)
            path = "/html/body/div[2]/div[2]/div/div/div/mat-option[{}]".format(custom_state_id)
            print(path)
            element = WebDriverWait(driver,5).until(lambda d: d.find_element_by_xpath(path))
            #state = element.text do not uncomment spelling error 
            print("state:"+state)
            driver.execute_script("arguments[0].click();",element)
            
            time.sleep(2) #essential wait for corresponding district to be loaded in UI   
        except Exception as e:
            print("Exception in finding states")
        
        all_availability_in_state=[]

        # 2. looping over all the districts for a state as per user query
        while(len(ids[custom_state_id])>0):
            custom_district_id,actual_district_id=ids[custom_state_id][-1] #optimize pop traverse from back
            b=custom_district_id
            district=district_final[actual_district_id]
            try:
                #select district dropdown
                path = "/html/body/app-root/div/app-home/div[3]/div/appointment-table/div/div/div/div/div/div/div/div/div/div/form/mat-tab-group/div/mat-tab-body[2]/div/div/div[2]/mat-form-field/div/div[1]/div/mat-select"
                element = WebDriverWait(driver,5).until(lambda d: d.find_element_by_xpath(path))
                driver.execute_script("arguments[0].click();",element)
                #Select district 
                time.sleep(1)
                
                path = "/html/body/div[2]/div[2]/div/div/div/mat-option[{}]".format(custom_district_id)
                element = WebDriverWait(driver,5).until(lambda d: d.find_element_by_xpath(path))
                print("district:"+district)
                driver.execute_script("arguments[0].click();",element)

                #Search button
                path="/html/body/app-root/div/app-home/div[3]/div/appointment-table/div/div/div/div/div/div/div/div/div/div/form/mat-tab-group/div/mat-tab-body[2]/div/div/div[3]/button"
                element = WebDriverWait(driver,5).until(lambda d: d.find_element_by_xpath(path))
                driver.execute_script("arguments[0].click();",element)

                time.sleep(2) #essential wait for vaccine status
                
            except Exception as e:
                print("All districts over for {}".format(state))
                break

            x=0

            all_availability_in_district=[]

            # 3. looping over all the centers for a district
            while(1>0):
                try:
                    #center name
                    path ="/html/body/app-root/div/app-home/div[3]/div/appointment-table/div/div/div/div/div/div/div/div/div/div/div[2]/form/div/div/div[5]/div[3]/div/div/div/div[{}]/div/div/div[1]/div/h5".format(x+1)
                    element = WebDriverWait(driver,0).until(lambda d: d.find_element_by_xpath(path))
                    center = element.text
                    print(center)
            
                    #center address
                    path = "/html/body/app-root/div/app-home/div[3]/div/appointment-table/div/div/div/div/div/div/div/div/div/div/div[2]/form/div/div/div[5]/div[3]/div/div/div/div[{}]/div/div/div[1]/div/p".format(x+1)
                    element = WebDriverWait(driver,0).until(lambda d: d.find_element_by_xpath(path))
                    address = element.text
                    print(address)
                except Exception as e:
                    print("------------All centers found in",state,district)
                    break
                
                availability=[]
                # 4. looping over next six days of availability for a center
                for i in range(6):
                    try:
                        #date
                        path = "/html/body/app-root/div/app-home/div[3]/div/appointment-table/div/div/div/div/div/div/div/div/div/div/div[2]/form/div/div/div[5]/div[2]/div/div/ul/carousel/div/div/slide[{}]/div/li/a/p".format(i+1)
                        element = WebDriverWait(driver,0).until(lambda d: d.find_element_by_xpath(path))
                        #print(element.text,end="::")
                        date = element.text
                        print(date)
                        #find number of vaccine categories each day
                        path = "/html/body/app-root/div/app-home/div[3]/div/appointment-table/div/div/div/div/div/div/div/div/div/div/div[2]/form/div/div/div[5]/div[3]/div/div/div/div[{}]/div/div/div[2]/ul/li[{}]".format(x+1,i+1)
                        element = WebDriverWait(driver,0).until(lambda d: d.find_elements_by_xpath(path))
                        #print("r=============================",len(element))

                        # 5. looping over multiple vaccines category available on each day 
                        for r in range(len(element)):
                            vaccine = ""
                            age = ""
                            status=""

                            try:
                                #NA
                                path = "/html/body/app-root/div/app-home/div[3]/div/appointment-table/div/div/div/div/div/div/div/div/div/div/div[2]/form/div/div/div[5]/div[3]/div/div/div/div[{}]/div/div/div[2]/ul/li[{}]/div[{}]/div/a".format(x+1,i+1,1)
                                element = WebDriverWait(driver,0).until(lambda d: d.find_element_by_xpath(path))
                                #print(element.text,end="::")
                                status = element.text
                                print(status)
                            except Exception as e:
                                print("Status is not NA")
                            try:
                            #Booked
                                path = "/html/body/app-root/div/app-home/div[3]/div/appointment-table/div/div/div/div/div/div/div/div/div/div/div[2]/form/div/div/div[5]/div[3]/div/div/div/div[{}]/div/div/div[2]/ul/li[{}]/div[{}]/div[2]/a".format(x+1,i+1,r+1)
                                element = WebDriverWait(driver,0).until(lambda d: d.find_element_by_xpath(path))
                                #print(element.text,end="::")
                                status = element.text
                                print(status)
                            except Exception as e:
                                print("Status is not Booked")
                            
                            try:
                            #Number of doses (d1+d2)
                                path = "/html/body/app-root/div/app-home/div[3]/div/appointment-table/div/div/div/div/div/div/div/div/div/div/div[2]/form/div/div/div[5]/div[3]/div/div/div/div[{}]/div/div/div[2]/ul/li[{}]/div[{}]/div/div[2]/a".format(x+1,i+1,r+1)
                                element = WebDriverWait(driver,0).until(lambda d: d.find_element_by_xpath(path))
                                #print(element.text,end="::")
                                status = element.text
                                print(status)
                            except Exception as e:
                                print("Number of doses not found")

                            if status!="NA" and status!="Booked" and status!="0" and status!="":
                                path ="/html/body/app-root/div/app-home/div[3]/div/appointment-table/div/div/div/div/div/div/div/div/div/div/div[2]/form/div/div/div[5]/div[3]/div/div/div/div[{}]/div/div/div[2]/ul/li[{}]/div[{}]/div/div[1]/h5".format(x+1,i+1,r+1)
                                element = WebDriverWait(driver,0).until(lambda d: d.find_element_by_xpath(path))
                                #print(element.text,end="::")
                                vaccine = element.text
                                      
                                path="/html/body/app-root/div/app-home/div[3]/div/appointment-table/div/div/div/div/div/div/div/div/div/div/div[2]/form/div/div/div[5]/div[3]/div/div/div/div[{}]/div/div/div[2]/ul/li[{}]/div[{}]/div/div[3]/span/span".format(x+1,i+1,r+1)
                                element = WebDriverWait(driver,0).until(lambda d: d.find_element_by_xpath(path))
                                #print(element.text,end="")
                                age = element.text
                                #print()
                                availability.append({"date":date,"status":status,"vaccine":vaccine,"age":age})

                    except Exception as e:
                        print("----------Empty Element Exception")
                        break
                item={"state":state,"district":district,"center":center,"address":address,"availability":availability}
                item_temp={}
                if len(availability)>0:
                    #print("item",item)
                    all_availability_in_district.append(item)
                    for temp in item:
                        item_temp[temp]=item[temp]
                    print(".",end=" ")
                    slots.insert_one(item_temp)
                x+=1

            if all_availability_in_district==[]:
                print("No slots available in",state,district)
                ids[custom_state_id].pop()
            else:
                # Sending emails for each district
                print("Publishing for",state,district)
                connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
                channel = connection.channel()
                channel.queue_declare(queue='hello')
                data = json.dumps(all_availability_in_district)
                channel.basic_publish(exchange='', routing_key='hello', body=data)
                connection.close()
                print("Published")
                ids[custom_state_id].pop() #popping a district
            print("Next district")
            print()
        
        print("All districts over, for State",state)
        # ids_left=ids.copy()
        # ids_left.pop(a)
        driver.get(driver.current_url)
        time.sleep(2)
        driver.refresh()

        try:
            if (driver.current_url)!="https://www.cowin.gov.in/":
                raise Exception("Auto terminated due to logout")
        except Exception as e:
            print(e)
            now = datetime.now() # current date and time
            date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
            print("date and  time:",date_time)
            flag2=1
            with open("ids_left.pickle","wb") as file:
                pickle.dump(ids,file)
            with open("state_final.pickle","wb") as file:
                pickle.dump(state_final,file)
            with open("district_final.pickle","wb") as file:
                pickle.dump(district_final,file)
            break
    
    # all states districts over
    if flag2==0:
        print("Terminated properly")
        # delete pickles if exists
        try:
            os.remove("ids_left.pickle")
        except Exception as e:
            print(e)
        try:
            os.remove("district_final.pickle")
        except Exception as e:
            print(e)
        try:
            os.remove("state_final.pickle")
        except Exception as e:
            print(e)
        now = datetime.now() # current date and time
        date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
        print("completion date and time:",date_time)
        driver.close()
    else:
        print("Request new sign in")
        driver.close()

first_time=True

driver,db=start()
find_vaccination_slots(driver,db)

# while(1>0):
#     try:
#         if first_time:
#             first_time=False
#             driver,db=start()
#             find_vaccination_slots(driver,db)
#         else:
#             find_vaccination_slots(driver,db)
#     except Exception as e:
#         driver,db = start()
#         find_vaccination_slots(driver,db)
