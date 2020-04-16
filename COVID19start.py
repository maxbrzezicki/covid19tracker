from flask import Flask, render_template, request
import sqlite3 as sql
from os import path
from datetime import datetime, timedelta, date
from operator import itemgetter, attrgetter
from statistics import median
####=====MAIN SETTINGS======================
#ROOT = path.dirname(path.realpath(__file__))
app = Flask(__name__)   


####=====FUNCTION DEFINITIONS======================
##=====STATS

def getSOFA(patientDB):
    pO2FiO2ratio=(int(patientDB[17])*7.5)/(int(patientDB[14])/100) 
    SOFA=0
    
    if pO2FiO2ratio>400:
        SOFA=SOFA+0
    elif pO2FiO2ratio<=400 and  pO2FiO2ratio>300:
        SOFA=SOFA+1 
    elif pO2FiO2ratio<=300 and  pO2FiO2ratio>200:
        SOFA=SOFA+2 
    elif pO2FiO2ratio<=200 and  pO2FiO2ratio>100:
        if patientDB[18][:4]=="CPAP" or patientDB[18][:5]=="BIPAP":
            SOFA=SOFA+3 
        else:
            SOFA=SOFA+2 
    elif pO2FiO2ratio<=100:
        if patientDB[18][:4]=="CPAP" or patientDB[18][:5]=="BIPAP":
            SOFA=SOFA+4 
        else:
            SOFA=SOFA+2 
   
    if patientDB[3]>=150:
        SOFA=SOFA+0 
    elif patientDB[3]<150 and patientDB[3]>100:
        SOFA=SOFA+1 
    elif patientDB[3]<=100 and patientDB[3]>50: 
        SOFA=SOFA+2 
    elif patientDB[3]<=50 and patientDB[3]<20:
        SOFA=SOFA+3 
    elif patientDB[3]<=20:
        SOFA=SOFA+4 

    if patientDB[22]<20:
        SOFA=SOFA+0 
    elif patientDB[22]>=20 and patientDB[22]<=32:
        SOFA=SOFA+1 
    elif patientDB[22]>=33 and patientDB[22]<=101:
        SOFA=SOFA+2 
    elif patientDB[22]<=102 and patientDB[22]<=204:
        SOFA=SOFA+3 
    elif patientDB[22]>204:
        SOFA=SOFA+4 
    
    if patientDB[7]<110:
        SOFA=SOFA+0 
    elif patientDB[7]>=110 and patientDB[7]<=170:
        SOFA=SOFA+1 
    elif patientDB[7]>=170 and patientDB[7]<=299:
        SOFA=SOFA+2 
    elif patientDB[7]<=300 and patientDB[7]<=440:
        SOFA=SOFA+3 
    elif patientDB[7]>440:
        SOFA=SOFA+4 
    
    if patientDB[21]>=70 and patientDB[19]<0.01:
        SOFA=SOFA+0 
    elif patientDB[21]<70 and patientDB[19]<0.01:
        SOFA=SOFA+1 
    elif patientDB[19]>0.01 and patientDB[19]<=0.1:
        SOFA=SOFA+3 
    elif patientDB[19]>0.1:
        SOFA=SOFA+4 
    return SOFA
    
    

def generateStatsForDay(givenDay,allNotes):
    
    noOfDchgFromITU=0
    noOfDchgFromITUList=0
    noOfDchgHome=0
    allMRNs=[]
    
    for i in allNotes:
        if i[15]==givenDay:
            allMRNs.append(i[13])
            if i[16]=="Discharge from ITU":
                noOfDchgFromITU+=1
            elif i[16]=="OFF ITU list":
                noOfDchgFromITUList+=1
            elif i[16]=="Home":
                noOfDchgHome+=1
    #lets check MRNs
    #this is actually no of all REVIEWED 
    noOfActive=len(set(allMRNs))
    
    statsDictDay={
    "currUpToDate":givenDay,
    "noOfActive":noOfActive,
    "noOfDchgFromITU":noOfDchgFromITU,
    "noOfDchgFromITUList":noOfDchgFromITUList,
    "noOfDchgHome":noOfDchgHome,
    "allMRNs":allMRNs,
  #  "noOfNewAdmissions":noOfNewAdmissions,
    }
    return statsDictDay
    
def generateStats():
    allPatients=getPatients()
    allNotes=getAllNotes()
    

    noOfActive=0
    for i in allPatients:
        if i[5]==1:
            noOfActive+=1


    noOfDchgFromITU=0
    noOfDchgFromITUList=0
    noOfDchgHome=0
    noOfDeaths=0
    allDates=[]
    dischargeDates=[]
    dischargeDatesITU=[]
    for i in allNotes:
        allDates.append(i[15]) #we're gonna needs this later
        if i[16]=="Discharge from ITU":
            noOfDchgFromITU+=1
            dischargeDatesITU.append([i[13],i[15]])
        elif i[16]=="OFF ITU list":
            noOfDchgFromITUList+=1
        elif i[16]=="Home":
            noOfDchgHome+=1
            dischargeDates.append([i[13],i[15]])
        elif i[16]=="Death":
            noOfDeaths+=1
            
            
    allDates=list(dict.fromkeys(allDates))
    allDates=sorted(allDates)
    
    
    
    currUpToDate=allDates[-1]
    allStatsDictDay=[]
    noOfNewAdmissions=[]
    for i in allDates:
        allStatsDictDay.append(generateStatsForDay(i,allNotes))
    
    noOfNewAdmissions.append((len(set(allStatsDictDay[0]['allMRNs']))))
    for i in range(1,len(allStatsDictDay)):
        noOfNewAdmissions.append(len(list(set(allStatsDictDay[i]['allMRNs']) - set(allStatsDictDay[i-1]['allMRNs']))))
    
    for i in range(0,len(allStatsDictDay)):
        allStatsDictDay[i]['noOfNewAdmissions']=noOfNewAdmissions[i]
    
    lengthOfStayHospital=[]
    for i in dischargeDates:
        print("So, lets go through notes")
        z=getNotes(i[0])
        tempListDates=[]
        tempListDates.clear()
        for ii in z:
            tempListDates.append(ii[15])
        tempListDates=sorted(tempListDates)
        lengthOfStayHospital.append(tempListDates[-1]-tempListDates[0])
    try:    
        medianLengthOfStayHospital=median(lengthOfStayHospital)
    except:
        medianLengthOfStayHospital="Unable to calculate"
        
    lengthOfStayITU=[]
    for i in dischargeDatesITU:
        print("So, lets go through notes")
        z=getNotes(i[0])
        tempListDates=[]
        tempListDates.clear()
        for ii in z:
            tempListDates.append(ii[15])
        tempListDates=sorted(tempListDates)
        lengthOfStayITU.append(tempListDates[-1]-tempListDates[0])
    
    try:    
        medianLengthOfStayITU=median(lengthOfStayITU)
    except:
        medianLengthOfStayITU="Unable to calculate"
    
    
    statsDict={
    "noOfActive":noOfActive,
    "noOfDeaths":noOfDeaths,
    "noOfDchgFromITU":noOfDchgFromITU,
    "noOfDchgFromITUList":noOfDchgFromITUList,
    "noOfDchgHome":noOfDchgHome,
    "currUpToDate":currUpToDate,
    "allStatsDictDay":allStatsDictDay,
    "lengthOfStayHospital":sorted(lengthOfStayHospital),
    "lengthOfStayITU":sorted(lengthOfStayITU),
    "medianLengthOfStayHospital":medianLengthOfStayHospital,
    "medianLengthOfStayITU":medianLengthOfStayITU,
    }
    
   
    return statsDict
    
def statsDchgFrom(fromThis,givenDay):
    MRNsDchg=[]
    dchgData=[]
    z=[]
    allNotes=getAllNotes()
    for i in allNotes:
        if givenDay:
            if i[15]>=givenDay:
                if i[16]==fromThis:
                    MRNsDchg.append([i[13],i[15]])
        else:
            if i[16]==fromThis:
                MRNsDchg.append([i[13],i[15]])
    
    for i in MRNsDchg:
        for ii in allNotes:
            if ii[13]==i[0]:
                if ii[15]>=i[1]:
                   z.append(ii) 
        dchgData.append(z)
        
        z=[]
    return dchgData
    
                
@app.route("/displayFrom", methods=["GET"])
def displayFrom():
    fromD=request.args.get('from')
    if request.args.get('days'):
        daysD=datetime.strptime(request.args.get('days'), '%Y-%m-%d %H:%M:%S.%f')
    else:
        daysD=0
    #daysD=datetime(2020, 4, 7, 0, 0)
    labelName=request.args.get('labelName')  
    valueName=int(request.args.get('valueName'))
   # return render_template('displayFrom.html',patientData=getPtInfo(MRN), patientDB=getNotes(MRN))
    patientDB=statsDchgFrom(fromD,daysD)
    listOfMRNs=[]
    for i in patientDB:
        listOfMRNs.append(i[0][13])
    listOfMRNs=set(listOfMRNs)
    lenTT=len(listOfMRNs)
    
    chartData={}
    #lets transpose this
    for i in listOfMRNs:
        chartDataM=[]
        for ii in patientDB:
            if ii[0][13]==i:
                chartDataM.append(ii)
        chartData[i]=chartDataM
    
    return render_template('displayFrom.html', chartData=chartData, lenTT=lenTT, listOfMRNs=listOfMRNs, patientDB=patientDB, daysD=request.args.get('days'),diffDate7=datetime.today() - timedelta(days=7),fromD=fromD,paraMeter={'labelName':labelName,'valueName':valueName})
    
##=====GET INFO
def getPatients():
	patientsMain=[]
	con = sql.connect("covid.sql")
	print ("Opened database successfully")
	con.row_factory = sql.Row
	cur = con.cursor()
	cur.execute('SELECT * FROM Patients')
	rows = cur.fetchall()
	for row in rows:
		patientsMain.append([row[0],row[1],row[2],row[3],row[4],row[5],row[6]])
	con.close()
	return patientsMain
  
@app.route("/patientList")
@app.route("/")
def patientList():
        #try:
            #getPatients()
        return render_template('patientList.html', patientsMain=getPatients(),statsDict=generateStats())    
        #except:
         #   return render_template('addPatient.html', msg="There was a problem with the Data Base. Maybe it is empty! Please try adding a patient")
    
    
def getPtInfo(MRN):
	patientInfo=[]
	con = sql.connect("covid.sql")
	print ("Opened database successfully")
	con.row_factory = sql.Row
	cur = con.cursor()
	cur.execute('SELECT * FROM Patients WHERE MRN=? ',[MRN])
	rows = cur.fetchall()
	for row in rows:
		patientInfo.append([row[0],row[1],row[2],row[3],row[4],row[5],row[6]])
	con.close()
	return patientInfo


    
def getAllNotes():
	allNotes=[]
	con = sql.connect("covid.sql")
	print ("Opened database successfully")
	con.row_factory = sql.Row
	cur = con.cursor()
	cur.execute('SELECT * FROM Labs')
	rows = cur.fetchall()
	for row in rows:
		allNotes.append([row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12],row[13],row[14],datetime.strptime(row[15], '%Y-%m-%dT%H:%M'),row[16],row[17],row[18],row[19],row[20],row[21],row[22],row[23],row[24]])
	con.close()
	return allNotes

    
def getNotes(MRN):
	notesMain=[]
	con = sql.connect("covid.sql")
	print ("Opened database successfully")
	con.row_factory = sql.Row
	cur = con.cursor()
	cur.execute('SELECT * FROM Labs WHERE MRN=? ',[MRN])
	rows = cur.fetchall()
	for row in rows:
		notesMain.append([row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12],row[13],row[14],datetime.strptime(row[15], '%Y-%m-%dT%H:%M'),row[16],row[17],row[18],row[19],row[20],row[21],row[22],row[23],row[24]])
	con.close()
	return notesMain


##=====INSERT INFO
def enterPatient(MRN,Age,Comorb,ClinFrailty,PName):
    con = sql.connect("covid.sql")
    print ("Opened database successfully for adding a new patient")
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("INSERT INTO `Patients`(`id`,`MRN`,`Age`,`Comorb`,`ClinFrailty`, `Active`, `PName`) VALUES (NULL,?,?,?,?,1,?)",
               [MRN,Age,Comorb,ClinFrailty,PName])
    con.commit()
    print ("Commited!")
    con.close()
    
@app.route("/addPatient")
def addPatient():	
	return render_template('addPatient.html')
    
@app.route("/addPatient2", methods=["POST"])
def addPatient2():	
    MRN=request.form['MRN']
    Age=request.form['Age']
    Comorb=request.form['Comorb']
    ClinFrailty=request.form['ClinFrailty']
    PName=request.form['PName']
    enterPatient(MRN,Age,Comorb,ClinFrailty,PName)
    return render_template('addNote.html', patientData=getPtInfo(MRN), patientDB=getNotes(MRN),msg="Patient admitted successfully! Now enter the note.")

    
def enterNote(Wcc,Lymph,Plt,LDH,CRP,Na,Creat,Ddimer,LofO2,PctgO2,Temp,RR,OtherIx,MRN,Date,Location,pO2,modOfVent,Norad,Terl,MAP,Bili):
    con = sql.connect("covid.sql")
    print ("Opened database successfully for entering a note")
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("INSERT INTO `Labs`(`id`,`Wcc`,`Lymph`,`Plt`,`LDH`,`CRP`,`Na`,`Creat`,`Ddimer`,`LofO2`,`Temp`,`RR`,`OtherIx`,`MRN`,`PctgO2`,`Date`, `Location`, `pO2`, `modOfVent`,`Norad`,`Terl`,`MAP`,`Bili`,`PFratio`,`SOFA`) VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
               [Wcc,Lymph,Plt,LDH,CRP,Na,Creat,Ddimer,LofO2,Temp,RR,OtherIx,MRN,PctgO2,Date,Location,pO2,modOfVent,Norad,Terl,MAP,Bili,int(pO2)/int(PctgO2),getSOFA([0,Wcc,int(Lymph),int(Plt),LDH,int(CRP),int(Na),int(Creat),int(Ddimer),int(LofO2),Temp,RR,OtherIx,MRN,int(PctgO2),Date,Location,int(pO2),modOfVent,int(Norad),int(Terl),int(MAP),int(Bili)])])
    con.commit()
    print ("Commited!")
    con.close()
    
@app.route("/patients1", methods=["GET","POST"])
def addNote():
    MRN=request.args.get('MRN')
    return render_template('addNote.html', patientData=getPtInfo(MRN), patientDB=getNotes(MRN))
    
@app.route("/patients2", methods=["POST"])
def addNote2():
    Wcc=request.form['Wcc']
    Lymph=request.form['Lymph']
    Plt=request.form['Plt']
    LDH=request.form['LDH']
    CRP=request.form['CRP']
    Na=request.form['Na']
    Creat=request.form['Creat']
    Ddimer=request.form['Ddimer']
    LofO2=request.form['LofO2']
    Temp=request.form['Temp']
    RR=request.form['RR']
    OtherIx=request.form['OtherIx']
    MRN=request.form['MRN']
    PctgO2=request.form['PctgO2']
    Date=request.form['Date']
    Location=request.form['Location']
    pO2=request.form['pO2']
    modOfVent=request.form['modOfVent']
    Norad=request.form['Norad']
    Terl=request.form['Terl']
    MAP=request.form['MAP']
    Bili=request.form['Bili']
    enterNote(Wcc,Lymph,Plt,LDH,CRP,Na,Creat,Ddimer,LofO2,PctgO2,Temp,RR,OtherIx,MRN,Date,Location,pO2,modOfVent,Norad,Terl,MAP,Bili)
    return render_template('addNote.html', patientData=getPtInfo(MRN), patientDB=getNotes(MRN),msg="Note added")

#=====DEDUCT
@app.route("/deduct", methods=["GET"])
def discharge():
	MRN=request.args.get('MRN')
	con = sql.connect("covid.sql")
	print ("Opened database successfully for patient discharge")
	cur = con.cursor()
	cur.execute('UPDATE Patients SET "Active"="0" WHERE "MRN"=?',[MRN])
	con.commit()
	print ("Commited!")
	con.close()
	return render_template('patientList.html', patientsMain=getPatients(),statsDict=generateStats(),msg="Successfully deducted")    

@app.route("/toWard", methods=["GET"])
def dischargetoWard():
	MRN=request.args.get('MRN')
	con = sql.connect("covid.sql")
	print ("Opened database successfully for patient discharge")
	cur = con.cursor()
	cur.execute('UPDATE Patients SET "Active"="3" WHERE "MRN"=?',[MRN])
	con.commit()
	print ("Commited!")
	con.close()
	return render_template('patientList.html', patientsMain=getPatients(),statsDict=generateStats(),msg="Successfully deducted")    


@app.route("/1")
def route():
    return render_template("index.html")
#=====DISPLAY
@app.route("/display", methods=["GET"])
def display():
    MRN=request.args.get('MRN')
    return render_template('display.html',patientData=getPtInfo(MRN), patientDB=getNotes(MRN))
    
@app.route("/stats", methods=["GET"])
def statsPage():
    return render_template('stats.html')