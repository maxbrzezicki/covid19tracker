from flask import Flask, session, redirect, url_for, request, render_template
import sqlite3 as sql
from os import path
from datetime import datetime, timedelta, date
from statistics import median
import hashlib
from collections import Counter
####=====MAIN SETTINGS======================
ROOT = path.dirname(path.realpath(__file__))
app = Flask(__name__)
users = {} 
app.secret_key = b'gaE%DhfJ_A"9t&dVu{U~'
salt=b"Ma;HmzR^2g[V{n'v|zs@}X10rJZeL%GV}|c~S/c6O>Dna=OszHf-v'C<_@u9yf$"
key=b"\xec\x1fZ\x9eKN\x99u\ru\xd1\xb8\x93\xe3\xbe\x8cH\x9fO8C\xba\x11\xde^l\x99\x146e'\x81"
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
    tempAllMRNs=[]
    
    for i in allNotes:
        if i[15]==givenDay:
            if i[16]=="Discharge from ITU":
                noOfDchgFromITU+=1
            elif i[16]=="Home":
                noOfDchgHome+=1
            elif i[16]=="ITU":
                allMRNs.append(i[13])
                
    #lets check MRNs
    #this is actually no of all on ITU (ward aren't reviewed daily)
    noOfActive=len(set(allMRNs))
    print("Date:")
    print(givenDay)
    print("MRNS:")
    print(set(allMRNs))
    statsDictDay={
    "currUpToDate":givenDay,
    "noOfActive":noOfActive,
    "noOfDchgFromITU":noOfDchgFromITU,
    "noOfDchgHome":noOfDchgHome,
    "allMRNs":allMRNs,

    }
    return statsDictDay

    #this module will generate statistics for analysis

def generateStats():
    allPatients=getPatients()
    allNotes=getAllNotes()



### (1) THIS SECTION CALCULATES TOTAL NUMBER OF DEATHS, DISCHARGES AND ACTIVE PATIENTS
#definitions for ACTIVE in PATIENT DATABASE: 0 - death, 1 - on ITU, 2 - dchg to ward, 3 - dchg home


    noOfActive=0
    noOfDchgFromITU=0
    noOfDchgHome=0
    noOfDeaths=0

    allMRNsActive=[]
    allMRNsDchgFromITU=[]
    allMRNsDchgHome=[]
    allMRNsDead=[]

    for i in allPatients:
        if i[5]==0:
            noOfDeaths+=1
            allMRNsDead.append(i[1])
        elif i[5]==1:
            noOfActive+=1
            allMRNsActive.append(i[1])
        elif i[5]==2:
            noOfDchgFromITU+=1
            allMRNsDchgFromITU.append(i[1])
        elif i[5]==3:
            noOfDchgHome+=1
            allMRNsDchgHome.append(i[1])


### END OF SECTION

### (2) THIS SECTION COLLECTS ALL DATES AND DATES OF SIGNIFICANT EVENTS see (1)
    allDates=[]
    dischargeDatesHome=[]
    dischargeDatesITU=[]
    deathDates=[]

    for i in allNotes:
        allDates.append(i[15])
        if i[16]=="Discharge from ITU":
            dischargeDatesITU.append([i[13],i[15]])
        elif i[16]=="Home":
            dischargeDatesHome.append([i[13],i[15]])
        elif i[16]=="Death":
            deathDates.append([i[13],i[15]])

### END OF SECTION


### (3) THIS SECTION GENERATES STATS FOR EVERY DAY IN THE DATABASE

    allStatsDictDay=[]
    allDates=list(dict.fromkeys(allDates))
    allDates=sorted(allDates)


    ## THIS IS THE statistics are current as of ...
    currUpToDate=allDates[-1]
    ##  --



    for i in allDates:
        allStatsDictDay.append(generateStatsForDay(i,allNotes))

### END SECTION


### (4) THIS SECTION GENERATES PER DAY DISPLAYABLE STATS

#### (4.1) New admissions

    noOfNewAdmissions=[]
    noOfNewAdmissions.append((len(set(allStatsDictDay[0]['allMRNs']))))
    for i in range(1,len(allStatsDictDay)):
        noOfNewAdmissions.append(len(list(set(allStatsDictDay[i]['allMRNs']) - set(allStatsDictDay[i-1]['allMRNs']))))
    for i in range(0,len(allStatsDictDay)):
        allStatsDictDay[i]['noOfNewAdmissions']=noOfNewAdmissions[i]

### END SECTION

### (5) THIS SECTION CALCULATES LENGTHS OF STAY




#### (5.1) Length of ITU (running)
    lengthOfStayITU=[]
    currentAsOfMRN={}

    for i in allMRNsActive:
        tempListDates=[]
        tempListDates.clear()
        for ii in allNotes:
            if ii[13]==i:
                tempListDates.append(ii[15])
        tempListDates=sorted(tempListDates)
        lengthOfStayITU.append(tempListDates[-1]-tempListDates[0])
        currentAsOfMRN[i]=tempListDates[-1]

    try:
        medianLengthOfStayITU=median(lengthOfStayITU)
    except:
        medianLengthOfStayITU="Unable to calculate"

#### (5.2) Length of Hospital (running)
    lengthOfStayHospital=[]


    for i in allMRNsDchgFromITU:
        tempListDates=[]
        tempListDates.clear()
        for ii in allNotes:
            if ii[13]==i:
                tempListDates.append(ii[15])
        tempListDates=sorted(tempListDates)
        lengthOfStayHospital.append(tempListDates[-1]-tempListDates[0])
        currentAsOfMRN[i]=tempListDates[-1]

    lengthOfStayHospital=lengthOfStayHospital+lengthOfStayITU





    try:
        medianLengthOfStayHospital=median(lengthOfStayHospital)
    except:
        medianLengthOfStayHospital="Unable to calculate"


#### (5.3) Length of Hospital stay - all surviving
    lengthOfStayHospitalS=[]
    for i in dischargeDatesHome:
        z=getNotes(i[0])
        tempListDates=[]
        tempListDates.clear()
        for ii in z:
            tempListDates.append(ii[15])
        tempListDates=sorted(tempListDates)
        lengthOfStayHospitalS.append(tempListDates[-1]-tempListDates[0])


    try:
        medianLengthOfStayHospitalS=median(lengthOfStayHospitalS)
    except:
        medianLengthOfStayHospitalS="Unable to calculate"

#### (5.4) Length of ITU stay - all surviving

    lengthOfStayITUS=[]
    for i in dischargeDatesITU:
        print("So, lets go through notes")
        z=getNotes(i[0])
        tempListDates=[]
        tempListDates.clear()
        for ii in z:
            tempListDates.append(ii[15])
        tempListDates=sorted(tempListDates)
        lengthOfStayITUS.append(tempListDates[-1]-tempListDates[0])

    try:
        medianLengthOfStayITUS=median(lengthOfStayITUS)
    except:
        medianLengthOfStayITUS="Unable to calculate"


### Just to complete @AS OF@ for warded patients1
    for i in allMRNsDchgFromITU:
        tempListDates=[]
        tempListDates.clear()
        for ii in allNotes:
            if ii[13]==i:
                tempListDates.append(ii[15])
        tempListDates=sorted(tempListDates)
        lengthOfStayITU.append(tempListDates[-1]-tempListDates[0])
        currentAsOfMRN[i]=tempListDates[-1]

#### FINALLY SAVING TO THE RETURN DICT




    statsDict={
    #DATA CURRENT AS OF
    "currUpToDate":currUpToDate,
    "currentAsOfMRN":currentAsOfMRN,

    #NUMBERS OF PATIENTS IN GIVEN STATUS
    "noOfActive":noOfActive,
    "noOfDeaths":noOfDeaths,
    "noOfDchgFromITU":noOfDchgFromITU,
    "noOfDchgHome":noOfDchgHome,


    #ALL STATS FOR DAYS
    "allStatsDictDay":allStatsDictDay,

    # SURVIVING DATA
    "lengthOfStayHospitalS":sorted(lengthOfStayHospitalS),
    "lengthOfStayITUS":sorted(lengthOfStayITUS),
    "medianLengthOfStayHospitalS":medianLengthOfStayHospitalS,
    "medianLengthOfStayITUS":medianLengthOfStayITUS,

    #RUNNING DATA
    "lengthOfStayITU":sorted(lengthOfStayITU),
    "medianLengthOfStayITU":medianLengthOfStayITU,
    "lengthOfStayHospital":sorted(lengthOfStayHospital),
    "medianLengthOfStayHospital":medianLengthOfStayHospital,

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
    labelName=request.args.get('labelName')
    valueName=int(request.args.get('valueName'))
    patientDB=statsDchgFrom(fromD,daysD)
    listOfMRNs=[]
    for i in patientDB:
        for ii in i:
            listOfMRNs.append(ii[13])
    w=Counter(listOfMRNs)
    lenTT=w[sorted(w)[0]]
    listOfMRNs=set(listOfMRNs)
    

    chartData={}
    #lets transpose this
    for i in listOfMRNs:
        chartDataM=[]
        for ii in patientDB:
            if ii[0][13]==i:
                chartDataM.append(ii)
        chartData[i]=chartDataM

    return render_template('displayFrom.html', chartData=chartData, lenTT=lenTT, listOfMRNs=listOfMRNs, patientDB=patientDB, daysD=request.args.get('days'),diffDate7=datetime.today() - timedelta(days=7),fromD=fromD,paraMeter={'labelName':labelName,'valueName':valueName})


def statsDchgFrom2(givenDay,activityNo):
    MRNsDchg=[]
    dchgData=[]
    z=[]
    allNotes=getAllNotes()
    allMRNsActive=[]
    
    allPatients=getPatients()
    
    for i in allPatients:
        if i[5]==activityNo:
            allMRNsActive.append(i[1])
        
    for i in allNotes:
        if givenDay:
            if i[15]>=givenDay:
                if i[13] in allMRNsActive:
                    MRNsDchg.append([i[13],i[15]])
        else:
            if i[13] in allMRNsActive:
                MRNsDchg.append([i[13],i[15]])

    for i in MRNsDchg:
        for ii in allNotes:
            if ii[13]==i[0]:
                if ii[15]>=i[1]:
                   z.append(ii)
        dchgData.append(z)

        z=[]
    return dchgData


@app.route("/displayITU", methods=["GET"])
def displayITU():
    if request.args.get('days'):
        daysD=datetime.strptime(request.args.get('days'), '%Y-%m-%d %H:%M:%S.%f')
    else:
        daysD=0
    labelName=request.args.get('labelName')
    valueName=int(request.args.get('valueName'))
    
    activityNo=1
    patientDB=statsDchgFrom2(daysD,activityNo)
    
    listOfMRNs=[]
    for i in patientDB:
        listOfMRNs.append(i[0][13])
    w=Counter(listOfMRNs)
    lenTT=w[sorted(w)[0]]
    listOfMRNs=set(listOfMRNs)
    
    
    chartData={}
    #lets transpose this
    for i in listOfMRNs:
        chartDataM=[]
        for ii in patientDB:
            if ii[0][13]==i:
                chartDataM.append(ii)
        chartData[i]=chartDataM

    return render_template('displayITU.html', chartData=chartData, lenTT=lenTT, listOfMRNs=listOfMRNs, patientDB=patientDB, daysD=request.args.get('days'),diffDate7=datetime.today() - timedelta(days=7),paraMeter={'labelName':labelName,'valueName':valueName})


##=====GET INFO
def getPatients():
	patientsMain=[]
	con = sql.connect(path.join(ROOT, "covid.sql"))
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
        if 'username' in session:
            return render_template('patientList.html', patientsMain=getPatients(),statsDict=generateStats())
        else:
            return redirect(url_for('login'))
            
@app.route("/login", methods=["POST","GET"])
def login():
    if request.method == 'POST':
        if key==hashlib.pbkdf2_hmac('sha256', request.form['password'].encode('utf-8'), salt, 100000):
            session['username'] = "ALLOW"
            return redirect(url_for('patientList'))
        else:
            return '''
            <center>
        WRONG PASSWORD! Please try again:<br>
    <form method="post">
    <input type="password" name="password">
            <input type=submit value=Login>
        </form></center>
    '''

    else:
        return '''<center>
        Please type in your password (default=password):<br>
    <form method="post">
    <input type="password" name="password">
            <input type=submit value=Login>
        </form></center>
    '''

@app.route('/logout')
def logout():
    session.pop('username', None)
    return '''<center>
      You have now been logged out. <a href="/login">Log back in</a>
    '''


def getPtInfo(MRN):
	patientInfo=[]
	con = sql.connect(path.join(ROOT, "covid.sql"))
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
	con = sql.connect(path.join(ROOT, "covid.sql"))
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
	con = sql.connect(path.join(ROOT, "covid.sql"))
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
    con = sql.connect(path.join(ROOT, "covid.sql"))
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
    if 'username' in session:
        return render_template('addPatient.html')
    else:
        return redirect(url_for('login'))
	

@app.route("/addPatient2", methods=["POST"])
def addPatient2():
    if 'username' in session:
        MRN=request.form['MRN']
        Age=request.form['Age']
        Comorb=request.form['Comorb']
        ClinFrailty=request.form['ClinFrailty']
        PName=request.form['PName']
        enterPatient(MRN,Age,Comorb,ClinFrailty,PName)
        return render_template('addNote.html', patientData=getPtInfo(MRN), patientDB=getNotes(MRN),msg="Patient admitted successfully! Now enter the note.")
    else:
        return redirect(url_for('login'))



def enterNote(Wcc,Lymph,Plt,LDH,CRP,Na,Creat,Ddimer,LofO2,PctgO2,Temp,RR,OtherIx,MRN,Date,Location,pO2,modOfVent,Norad,Terl,MAP,Bili):
    con = sql.connect(path.join(ROOT, "covid.sql"))
    print ("Opened database successfully for entering a note")
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("INSERT INTO `Labs`(`id`,`Wcc`,`Lymph`,`Plt`,`LDH`,`CRP`,`Na`,`Creat`,`Ddimer`,`LofO2`,`Temp`,`RR`,`OtherIx`,`MRN`,`PctgO2`,`Date`, `Location`, `pO2`, `modOfVent`,`Norad`,`Terl`,`MAP`,`Bili`,`PFratio`,`SOFA`) VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
               [Wcc,Lymph,Plt,LDH,CRP,Na,Creat,Ddimer,LofO2,Temp,RR,OtherIx,MRN,PctgO2,Date,Location,pO2,modOfVent,Norad,Terl,MAP,Bili,int(pO2)/int(PctgO2),getSOFA([0,Wcc,Lymph,int(Plt),LDH,int(CRP),int(Na),int(Creat),int(Ddimer),int(LofO2),Temp,RR,OtherIx,MRN,int(PctgO2),Date,Location,int(pO2),modOfVent,float(Norad),Terl,int(MAP),int(Bili)])])
    con.commit()
    print ("Commited!")
    con.close()

@app.route("/patients1", methods=["GET","POST"])
def addNote():
    if 'username' in session:
        MRN=request.args.get('MRN')
        return render_template('addNote.html', patientData=getPtInfo(MRN), patientDB=getNotes(MRN))
    else:
        return redirect(url_for('login'))
        
@app.route("/patients2", methods=["POST"])
def addNote2():
    if 'username' in session:
        MRN=request.args.get('MRN')
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
    else:
        return redirect(url_for('login'))
    
#=====DEDUCT
@app.route("/deduct", methods=["GET"])
def discharge():
    if 'username' in session:
        MRN=request.args.get('MRN')
        con = sql.connect(path.join(ROOT, "covid.sql"))
        print ("Opened database successfully for patient discharge")
        cur = con.cursor()
        cur.execute('UPDATE Patients SET "Active"="0" WHERE "MRN"=?',[MRN])
        con.commit()
        print ("Commited!")
        con.close()
        return render_template('patientList.html', patientsMain=getPatients(),statsDict=generateStats(),msg="Successfully deducted")
    else:
        return redirect(url_for('login'))
    
    
@app.route("/toWard", methods=["GET"])
def dischargetoWard():
    if 'username' in session:    
        MRN=request.args.get('MRN')
        con = sql.connect(path.join(ROOT, "covid.sql"))
        print ("Opened database successfully for patient discharge")
        cur = con.cursor()
        cur.execute('UPDATE Patients SET "Active"="2" WHERE "MRN"=?',[MRN])
        con.commit()
        print ("Commited!")
        con.close()
        return render_template('patientList.html', patientsMain=getPatients(),statsDict=generateStats(),msg="Successfully deducted")
    else:
        return redirect(url_for('login'))

@app.route("/toHome", methods=["GET"])
def dischargeHome():
    if 'username' in session:    
        MRN=request.args.get('MRN')
        con = sql.connect(path.join(ROOT, "covid.sql"))
        print ("Opened database successfully for patient discharge")
        cur = con.cursor()
        cur.execute('UPDATE Patients SET "Active"="3" WHERE "MRN"=?',[MRN])
        con.commit()
        print ("Commited!")
        con.close()
        return render_template('patientList.html', patientsMain=getPatients(),statsDict=generateStats(),msg="Successfully deducted")
    else:
        return redirect(url_for('login'))
    
    

#=====DISPLAY
@app.route("/display", methods=["GET"])
def display():
    if 'username' in session:
        MRN=request.args.get('MRN')
        return render_template('display.html',patientData=getPtInfo(MRN), patientDB=getNotes(MRN))
    else:
        return redirect(url_for('login'))
@app.route("/stats", methods=["GET"])
def statsPage():
    if 'username' in session:
        return render_template('stats.html')
    else:
        return redirect(url_for('login'))