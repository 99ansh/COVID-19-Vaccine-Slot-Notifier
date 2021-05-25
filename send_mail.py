from pymongo import MongoClient
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate 
import pika, sys, os
import json
from datetime import datetime
import pickle

def main():
    dbclient = MongoClient("mongodb://localhost:27017")

    database = dbclient["temp"]
    users=database["users"]
    modified_data=database["modified_data"]

    with open("gmailaddress.pickle","rb") as file:
        gmailaddress = pickle.load(file)
    with open("gmailpassword.pickle","rb") as file:
        gmailpassword = pickle.load(file)
    
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='hello')

    mail_count=[280]

    # def callback(ch, method, properties, body_str):
    #     print(" [x] Received ",body_str)
    #     body = json.loads(body_str)
    #     state=body["state"]
    #     district=body["district"]
    #     center=body["center"]
    #     address=body["address"]
    #     availability = body["availability"]
    #     for item in availability:
    #         age=item["age"].split("Age ").pop()
    #         # print("FINDING......................... ",{"state":state,"district":district,"age":age})
    #         required_users = users.find({"state":state,"district":district,"age":age})
    #         for user in required_users:
                
    #             msg = body_str.decode("utf-8")
    #             msg = MIMEMultipart()
    #             msg['From'] = gmailaddress
    #             msg['To'] = user["emailId"]
    #             msg['Date'] = formatdate(localtime=True)
    #             msg['Subject'] = "New COVID-19 Vaccine Slots available in your area"

    #             info = "State - "+state+"<br>District - "+district+"<br>Center - "+center+"<br>Address - "+address+"<br><br>"
    #             info+= "Date - "+item['date']+"<br>"
    #             info+= "Number of Seats available - "+item['status']+"<br>"
    #             info+= "Vaccine - "+item['vaccine']+"<br>"
    #             info+= ""+item['age']+"<br><br>"

    #             text = f'<!DOCTYPE html><html><head><style></style></head><body>{info}</body></html>'
    #             msg.attach(MIMEText(text,'html'))

    #             mailServer = smtplib.SMTP('smtp.gmail.com' , 587)
    #             mailServer.starttls()
    #             mailServer.login(gmailaddress , gmailpassword)
    #             mailServer.sendmail(gmailaddress, user["emailId"] , msg.as_string())
    #             mail_count[0]+=1
    #             print(" \n Number of emials sent today,",mail_count[0])
    #             if mail_count==450:
    #                 print("EMAIL LIMIT EXCEEDED FOR TODAY")
    #                 try:
    #                     sys.exit(0)
    #                 except SystemExit:
    #                     os._exit(0)
    #             mailServer.quit()

    def callback(ch, method, properties, body_str):
        i=0
        #print(" [x]1`Received ",body_str)
        slots = json.loads(body_str)
        x={}
        y={}
        qstate=[]
        qdistrict=[]
        for slot in slots:
            state=slot["state"]
            qstate=[state]
            district=slot["district"]
            qdistrict=[district]
            center=slot["center"]
            address=slot["address"]
            x[(center,address)]=[]
            y[(center,address)]=[]
            availability = slot["availability"]
            for item in availability:
                #print("item=",item)
                age=item["age"].split("Age ").pop()
                if age=="18+":
                    x[(center,address)].append((item["date"],item["vaccine"],item["status"]))
                elif age=="45+":
                    y[(center,address)].append((item["date"],item["vaccine"],item["status"]))
            if len(y[(center,address)])==0:
                y.pop((center,address))
            if len(x[(center,address)])==0:
                x.pop((center,address))
        
        modified_item1={"state":qstate[0],"district":qdistrict[0],"age":"18+","data":x}
        modified_item2={"state":qstate[0],"district":qdistrict[0],"age":"45+","data":y}

        # print(modified_item1)
        # print(modified_item2)
        
        if (len(modified_item1["data"])>0):
            required_users = users.find({"state":state,"district":district,"age":"18+"})
            info = "<h2>State - "+modified_item1['state']+"</h2><h2>District - "+modified_item1['district']+"</h2>"+"<h2>Age - 18+</h2>"
            info+="<table cellpadding=4px>"
            info+="<tr>"
            info+="<th><h3>Centers</h3></th>"
            info+="<th><h3>Dates</h3></th>"
            info+="</tr>"
            for i in modified_item1["data"]:
                info+="<tr>"
                info+="<td><h4>"+i[0]+"</h4></td>"
                for j in modified_item1["data"][i]:
                    info+="<td><u><h4>"+j[0]+"</h4></u></td>"
                info+="</tr>"
                info+="<tr>"
                info+="<td>"+i[1]+"</td>"
                for j in modified_item1["data"][i]:
                    info+="<td>"+j[1]+"</td>"
                info+="</tr>"
                info+="<tr>"
                info+="<td>"+" "+"</td>"
                for j in modified_item1["data"][i]:
                    info+="<td><h4>"+j[2]+"</h4></td>"
                info+="</tr>"
                info+="<tr>"
                
                info+="</tr>"
            info+="</table>"
            info+="<h4>Register for Vaccination at https://selfregistration.cowin.gov.in/ </h4>"
            info+="<br><address>Developer contact - <a href='mailto:99ansh@gmail.com'>Ansh Mehta</a></address>"
            info+="<br><a href='https://docs.google.com/forms/d/e/1FAIpQLSdkSc_F_8zodGT4SsLQ05aBiiiuhCm6ksQgvS5EW0hi7LZAnQ/viewform'><i><u>Unsubscribe</u></i><a>"

            for user in required_users:           
                msg = MIMEMultipart()
                msg['From'] = gmailaddress
                msg['To'] = user["emailId"]
                msg['Date'] = formatdate(localtime=True)
                msg['Subject'] = "New COVID-19 vaccine slots are available in your area"

                text = f'<html><body>{info}</body></html>'
                msg.attach(MIMEText(text,'html'))

                mailServer = smtplib.SMTP('smtp.gmail.com' , 587)
                mailServer.starttls()
                mailServer.login(gmailaddress , gmailpassword)
                now = datetime.now() # current date and time
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
                print("Email sent to",user["name"],user["emailId"],date_time)
                mailServer.sendmail(gmailaddress, user["emailId"] , msg.as_string())
                mail_count[0]+=1
                print("Number of emials sent today,",mail_count[0])
                if mail_count==450:
                    print("EMAIL LIMIT EXCEEDED FOR TODAY")
                    try:
                        sys.exit(0)
                    except SystemExit:
                        os._exit(0)
                mailServer.quit()            


        #45+
        if (len(modified_item2["data"])>0):
            required_users = users.find({"state":state,"district":district,"age":"45+"})
            info = "<h2>State - "+modified_item2['state']+"</h2><h2>District - "+modified_item2['district']+"</h2>"+"<h2>Age - 45+</h2>"
            info+="<table cellpadding=4px>"
            info+="<tr>"
            info+="<th><h3>Centers</h3></th>"
            info+="<th><h3>Dates</h3></th>"
            info+="</tr>"
            for i in modified_item2["data"]:
                info+="<tr>"
                info+="<td><h4>"+i[0]+"</h4></td>"
                for j in modified_item2["data"][i]:
                    info+="<td><u><h4>"+j[0]+"</h4></u></td>"
                info+="</tr>"
                info+="<tr>"
                info+="<td>"+i[1]+"</td>"
                for j in modified_item2["data"][i]:
                    info+="<td>"+j[1]+"</td>"
                info+="</tr>"
                info+="<tr>"
                info+="<td>"+" "+"</td>"
                for j in modified_item2["data"][i]:
                    info+="<td><h4>"+j[2]+"</h4></td>"
                info+="</tr>"
                info+="<tr>"
                
                info+="</tr>"
            info+="</table>"
            info+="<h4>Register for Vaccination at https://selfregistration.cowin.gov.in/ </h4>"
            info+="<br><address>Developer contact - <a href='mailto:99ansh@gmail.com'>Ansh Mehta</a></address>"
            
            info+="<br><a href='https://docs.google.com/forms/d/e/1FAIpQLSdkSc_F_8zodGT4SsLQ05aBiiiuhCm6ksQgvS5EW0hi7LZAnQ/viewform'><i><u>Unsubscribe</u></i><a>"

            for user in required_users: 

                msg = MIMEMultipart()
                msg['From'] = gmailaddress
                msg['To'] = user["emailId"]
                msg['Date'] = formatdate(localtime=True)
                msg['Subject'] = "New COVID-19 vaccine slots are available in your area"

                text = f'<html><body>{info}</body></html>'
                msg.attach(MIMEText(text,'html'))

                mailServer = smtplib.SMTP('smtp.gmail.com' , 587)
                mailServer.starttls()
                mailServer.login(gmailaddress , gmailpassword)
                
                now = datetime.now() # current date and time
                date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
                print("Email sent to",user["name"],user["emailId"],date_time)
                mailServer.sendmail(gmailaddress, user["emailId"] , msg.as_string())
                mail_count[0]+=1
                print(" \n Number of emials sent today,",mail_count[0])
                if mail_count==450:
                    print("EMAIL LIMIT EXCEEDED FOR TODAY")
                    try:
                        sys.exit(0)
                    except SystemExit:
                        os._exit(0)
                mailServer.quit()            

    channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)



# mailto = "99ansh@gmail.com"
# msg = "trial"
# mailServer = smtplib.SMTP('smtp.gmail.com' , 587)
# mailServer.starttls()
# mailServer.login(gmailaddress , gmailpassword)
# mailServer.sendmail(gmailaddress, mailto , msg)
# print(" \n Sent!")
# mailServer.quit()