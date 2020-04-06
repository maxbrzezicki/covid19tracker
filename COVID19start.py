from flask import Flask, render_template, request
import sqlite3 as sql
from os import path


####=====MAIN SETTINGS======================
#ROOT = path.dirname(path.realpath(__file__))
app = Flask(__name__)   


####=====FUNCTION DEFINITIONS======================

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
		patientsMain.append([row[0],row[1],row[2],row[3],row[4],row[5]])
	con.close()
	return patientsMain
  
@app.route("/patientList")
@app.route("/")
def patientList():	
    return render_template('page1.html', patientsMain=getPatients())    
    
def getPtInfo(MRN):
	patientInfo=[]
	con = sql.connect("covid.sql")
	print ("Opened database successfully")
	con.row_factory = sql.Row
	cur = con.cursor()
	cur.execute('SELECT * FROM Patients WHERE MRN=? ',[MRN])
	rows = cur.fetchall()
	for row in rows:
		patientInfo.append([row[0],row[1],row[2],row[3],row[4],row[5]])
	con.close()
	return patientInfo

    
def getNotes(MRN):
	notesMain=[]
	con = sql.connect("covid.sql")
	print ("Opened database successfully")
	con.row_factory = sql.Row
	cur = con.cursor()
	cur.execute('SELECT * FROM Labs WHERE MRN=? ',[MRN])
	rows = cur.fetchall()
	for row in rows:
		notesMain.append([row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12],row[13],row[14],row[15]])
	con.close()
	return notesMain


##=====INSERT INFO
def enterPatient(MRN,Age,Comorb,ClinFrailty):
    con = sql.connect("covid.sql")
    print ("Opened database successfully for adding a new patient")
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("INSERT INTO `Patients`(`id`,`MRN`,`Age`,`Comorb`,`ClinFrailty`, `Active`) VALUES (NULL,?,?,?,?,1)",
               [MRN,Age,Comorb,ClinFrailty])
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
    enterPatient(MRN,Age,Comorb,ClinFrailty)
    return render_template('page1.html', patientsMain=getPatients(), msg="Addedd successfully")

    
def enterNote(Wcc,Lymph,Plt,LDH,CRP,Na,Creat,Ddimer,LofO2,PctgO2,Temp,RR,OtherIx,MRN,Date):
    con = sql.connect("covid.sql")
    print ("Opened database successfully for entering a note")
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("INSERT INTO `Labs`(`id`,`Wcc`,`Lymph`,`Plt`,`LDH`,`CRP`,`Na`,`Creat`,`Ddimer`,`LofO2`,`Temp`,`RR`,`OtherIx`,`MRN`,`PctgO2`,`Date`) VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
               [Wcc,Lymph,Plt,LDH,CRP,Na,Creat,Ddimer,LofO2,Temp,RR,OtherIx,MRN,PctgO2,Date])
    con.commit()
    print ("Commited!")
    con.close()
    
@app.route("/patients1", methods=["GET","POST"])
def addNote():
    MRN=request.args.get('MRN')
    return render_template('page3.html', patientData=getPtInfo(MRN), patientDB=getNotes(MRN))
    
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
    enterNote(Wcc,Lymph,Plt,LDH,CRP,Na,Creat,Ddimer,LofO2,PctgO2,Temp,RR,OtherIx,MRN,Date)
    return render_template('page1.html', patientsMain=getPatients(),msg="Note added")

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
	return render_template('page1.html', patientsMain=getPatients(),msg="Patient successfully deducted,-")