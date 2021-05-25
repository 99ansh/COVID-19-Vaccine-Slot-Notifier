# import webdriver
import requests
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

client = pymongo.MongoClient("mongodb://127.0.0.1:27017/")


db = client["temp"]
slots = db["slots"]
slots.remove({})

executor = ThreadPoolExecutor(2)
app = Flask(__name__)
#driver = webdriver.Chrome()
with open("url.pickle","rb") as file:
    url = pickle.load(file)
message = {'text': 'SignIn(General)'}
response = requests.post(url, data = json.dumps(message))
print(response)

@app.route('/')
def hello():
    return 'Hello World!'

@app.route('/mobile',methods=["POST"])
def mobile():
    global driver
    global executor
    try:
        print(driver.get_url())
    except Exception as e:
        chrome_options=webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-running-insecure-content')
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
        chrome_options.add_argument(f'user-agent={user_agent}')
        driver = webdriver.Chrome(options=chrome_options)
        executor = ThreadPoolExecutor(2)
    slots.remove({})
    mobileNo=str(request.data.decode("utf-8"))
    driver.get("https://selfregistration.cowin.gov.in/")
    time.sleep(5)

    element1 = WebDriverWait(driver,10).until(lambda d: d.find_element_by_id("mat-input-0"))
    element2 = WebDriverWait(driver,10).until(lambda d: d.find_element_by_tag_name("ion-button"))
    element1.send_keys(mobileNo)
    #driver.get_screenshot_as_file("screenshot.png")
    driver.execute_script("arguments[0].click();",element2)  
    return 'Welcome IP1!'

@app.route('/otp',methods=["POST"])
def message():
    message = str(request.data.decode("utf-8"))
    print(message)
    start=37
    otp=int(message[start:start+6])
    print(otp)
    executor.submit(find_vaccination_slots,otp)
    #user_queries.execute()
    return 'Hello World!'


def find_vaccination_slots(otp=""):
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
        # print(ids)
        # print(state_final)
        # print(district_final)
    if otp!="":
        #time.sleep(5)
        element = WebDriverWait(driver,180).until(lambda d: d.find_element_by_id("mat-input-1"))
        element.send_keys(otp)

        now = datetime.now() # current date and time
        date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
        print("date and time:",date_time)

        element = WebDriverWait(driver,180).until(lambda d: d.find_element_by_tag_name("ion-button"))
        driver.execute_script("arguments[0].click();",element)

        #Inside account
        element = WebDriverWait(driver,180).until(lambda d: d.find_element_by_class_name("m-lablename"))
        driver.execute_script("arguments[0].click();",element)
        
        # element = WebDriverWait(driver,180).until(lambda d: d.find_element_by_tag_name("ion-button"))
        # driver.execute_script("arguments[0].click();",element)

        time.sleep(3) #essential or not test

        #Find by State and District
        #searchElement = WebDriverWait(driver,180).until(lambda d: d.find_element_by_xpath("/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[1]/div/label/div")) #click searchElement If search by district
        searchElement = WebDriverWait(driver,180).until(lambda d: d.find_element_by_xpath("/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[2]/div/label/div")) #click searchElement If search by district
        driver.execute_script("arguments[0].click();",searchElement)
        print(searchElement.text)

    # print(ids)
    # print(state_final)
    # print(district_final)
    for a in ids:
        state=state_final[a]
        # print(state)
        try:  
            time.sleep(3) #essential for getting states
            #select state dropdown
            #path = "/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[2]/ion-row/ion-col[1]/mat-form-field/div/div[1]/div/mat-select"
            path = "/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[3]/ion-row/ion-col[1]/mat-form-field/div/div[1]/div/mat-select"
            path = "/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[3]/ion-row/ion-col[1]/mat-form-field/div/div[1]/div/mat-select"
            element = WebDriverWait(driver,5).until(lambda d: d.find_element_by_xpath(path))
            #print("clicked for state:"+element.text)
            driver.execute_script("arguments[0].click();",element)
            #Select state  
            time.sleep(2)
            path = "/html/body/div[2]/div[2]/div/div/div/mat-option[{}]/span".format(a)
            element = WebDriverWait(driver,5).until(lambda d: d.find_element_by_xpath(path))
            #state = element.text do not uncomment spelling error 
            print("state:"+state)
            driver.execute_script("arguments[0].click();",element)
            
            time.sleep(2) #essential wait for corresponding district to be loaded in UI   
        except Exception as e:
            print("Exception in finding states")
        l=[]
        while(len(ids[a])>0):
            s=ids[a][-1] #optimize pop traverse from back
            b=s[0]
            district=district_final[s[1]]
            try:
                #select district dropdown
                #path = "/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[2]/ion-row/ion-col[2]/mat-form-field/div/div[1]/div/mat-select"
                path = "/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[3]/ion-row/ion-col[2]/mat-form-field/div/div[1]/div/mat-select"
                element = WebDriverWait(driver,5).until(lambda d: d.find_element_by_xpath(path))
                driver.execute_script("arguments[0].click();",element)
                #("clicked for district ")
                #Select district 
                time.sleep(1)
                path = "/html/body/div[2]/div[2]/div/div/div/mat-option[{}]/span".format(b)
                element = WebDriverWait(driver,5).until(lambda d: d.find_element_by_xpath(path))
                #district = element.text
                print("district:"+district)
                driver.execute_script("arguments[0].click();",element)

                #Search button
                #path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[2]/ion-row/ion-col[3]/ion-button"
                path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[3]/ion-row/ion-col[3]/ion-button"
                element = WebDriverWait(driver,5).until(lambda d: d.find_element_by_xpath(path))
                driver.execute_script("arguments[0].click();",element)

                time.sleep(2) #essential wait for vaccine status
                
            except Exception as e:
                print("All districts over for {}".format(state))
                break

            x=0
            centers=[]
            availability=[]
            while(1>0):
                try:
                    #center name
                    #path = "/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[6]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[1]/div/h5".format(x+1)
                    #path = "/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[8]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[1]/div/h5".format(x+1)
                    path = "/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row[3]/ion-col[3]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[1]/div/h5".format(x+1)
                    element = WebDriverWait(driver,0).until(lambda d: d.find_element_by_xpath(path))
                    #print(element.text)
                    center = element.text
            
                    #center address
                    #path = "/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[6]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[1]/div/p".format(x+1)
                    #path = "/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[8]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[1]/div/p".format(x+1)
                    path = "/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row[3]/ion-col[3]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[1]/div/p".format(x+1)
                    element = WebDriverWait(driver,0).until(lambda d: d.find_element_by_xpath(path))
                    #print(element.text)
                    address = element.text
                except Exception as e:
                    print("------------All centers found in",state,district)
                    break
                
                availability=[]
                for i in range(6):
                    try:
                        #date
                        #path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[5]/div/div/ul/carousel/div/div/slide[{}]/div/li/a/p".format(i+1)
                        #path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[7]/div/div/ul/carousel/div/div/slide[{}]/div/li/a/p".format(i+1)
                        path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row[3]/ion-col[2]/div/div/ul/carousel/div/div/slide[{}]/div/li/a/p".format(i+1)
                        element = WebDriverWait(driver,0).until(lambda d: d.find_element_by_xpath(path))
                        #print(element.text,end="::")
                        date = element.text
                        
                        #path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[8]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[2]/ul/li[{}]/div".format(x+1,i+1)
                        #path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[8]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[2]/ul/li[{}]/div".format(x+1,i+1)
                        path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row[3]/ion-col[3]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[2]/ul/li[{}]/div".format(x+1,i+1)
                        element = WebDriverWait(driver,0).until(lambda d: d.find_elements_by_xpath(path))
                        #print("r=============================",len(element))

                        for r in range(len(element)):
                        
                            #path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[6]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[2]/ul/li[{}]/div/div/a".format(x+1,i+1)
                            #path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[8]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[2]/ul/li[{}]/div/div/a".format(x+1,i+1)
                            #path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[8]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[2]/ul/li[{}]/div[{}]/div/a".format(x+1,i+1,r+1)
                            path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row[3]/ion-col[3]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[2]/ul/li[{}]/div[{}]/div/a".format(x+1,i+1,r+1)
                            
                            element = WebDriverWait(driver,0).until(lambda d: d.find_element_by_xpath(path))
                            #print(element.text,end="::")
                            status = element.text

                            vaccine = ""
                            age = ""
                            if status!="NA" and status!="Booked" and status!="0" and status!="":
                                #path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[6]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[2]/ul/li[{}]/div/div/div[1]/h5".format(x+1,i+1)
                                #path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[8]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[2]/ul/li[{}]/div/div/div[1]/h5".format(x+1,i+1)
                                #path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[8]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[2]/ul/li[{}]/div[{}]/div/div[1]/h5".format(x+1,i+1,r+1)
                                path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row[3]/ion-col[3]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[2]/ul/li[{}]/div[{}]/div/div[1]/h5".format(x+1,i+1,r+1)
                                element = WebDriverWait(driver,0).until(lambda d: d.find_element_by_xpath(path))
                                #print(element.text,end="::")
                                vaccine = element.text

                                #path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[6]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[2]/ul/li[{}]/div/div/div[2]/span".format(x+1,i+1)
                                #path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[8]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[2]/ul/li[{}]/div/div/div[2]/span".format(x+1,i+1)
                                #path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[8]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[2]/ul/li[{}]/div[{}]/div/div[2]/span".format(x+1,i+1,r+1)
                                path="/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row[3]/ion-col[3]/div/div/mat-selection-list/div[{}]/mat-list-option/div/div[2]/ion-row/ion-col[2]/ul/li[{}]/div[{}]/div/div[2]/span".format(x+1,i+1,r+1)
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
                    l.append(item)
                    for temp in item:
                        item_temp[temp]=item[temp]
                    print(".",end=" ")
                    slots.insert_one(item_temp)
                x+=1

            if l==[]:
                print("No slots available in",state,district)
                ids[a].pop()
            else:
                print("Publishing for",state,district)
                connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
                channel = connection.channel()
                channel.queue_declare(queue='hello')
                channel.basic_publish(exchange='', routing_key='hello', body=json.dumps(l))
                connection.close()
                print("Published")
                ids[a].pop()
            #print("Next district")
            print()
        
        print("All districts over, for State",state)
        # ids_left=ids.copy()
        # ids_left.pop(a)
        driver.get(driver.current_url)
        time.sleep(2)
        driver.refresh()

        try:
            if (driver.current_url)=="https://selfregistration.cowin.gov.in/":
                raise Exception("Auto terminated due to logout")
            searchElement = WebDriverWait(driver,60).until(lambda d: d.find_element_by_xpath("/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid/ion-row/ion-col[2]/div/label/div")) #click searchElement If search by district available
            driver.execute_script("arguments[0].click();",searchElement)
            #print(searchElement.text)
        except Exception as e:
            print(e)
            now = datetime.now() # current date and time
            date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
            print("date and time:",date_time)
            flag2=1
            with open("ids_left.pickle","wb") as file:
                pickle.dump(ids,file)
            with open("state_final.pickle","wb") as file:
                pickle.dump(state_final,file)
            with open("district_final.pickle","wb") as file:
                pickle.dump(district_final,file)
            break
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
        print("date and time:",date_time)
        url = 'https://hooks.slack.com/services/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'
        message = {'text': 'SignIn(General)'}
        response = requests.post(url, data = json.dumps(message))
        print(response)
        driver.close()
        # if driver.current_url=="https://selfregistration.cowin.gov.in/appointment":
        #     find_vaccination_slots()
        # else:
        #     print("Request new sign in")
    else:
        print("Request new sign in")
        with open("url.pickle","rb") as file:
            url = pickle.load(file)
        message = {'text': 'SignIn(General)'}
        response = requests.post(url, data = json.dumps(message))
        print(response)
        driver.close()

    #driver.get("https://selfregistration.cowin.gov.in/")

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000)