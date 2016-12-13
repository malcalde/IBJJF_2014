#!/usr/bin/env python

'''
Created on 22/01/2014

@author: malcalde
'''

import sys
import re
import csv
import os
import traceback
import math
import html2text
import urllib2
import sqlite3
import hashlib
import timeit

from datetime import date

assert(len(sys.argv) > 1)
MY_TEAM = sys.argv[1]

DEBUG_SQL = False
DEBUG_COMPETITORID = 'NOBODY'

stmA = """ 
  select  distinct C.id competitionID, C.name competitionName, T.competitorID competitorID, T.competitorName competidor_name, R.rawID
  from result R, competition C, team T
  where 1=1
     and T.id = '%s'
     and T.competitorID = R.competitorID
     and R.competitionID=C.id
	 and C.is_loaded=0
     order by T.competitorID, C.year
"""

stmB = stm = """
     select distinct R.competitorID, C.name 
  from result R, competition T, academy A, competitor C, lk_medal M
where R.medal=M.id
  and C.id = R.competitorID
  and A.id = R.academyID
  and T.id=R.competitionID
  and R.competitorID != '%s'
  and R.rawID like ('%s')
  """

stmC = """
select C.name competitor, replace(A.name,'LAST UPDATED','???') academy, C.birth_year estimated_birth_year,  sum(1) competitions, sum(('N/A' != m.name)) medals,
             sum(('GOLD' == m.name)) medal_gold, sum(('SILVER' == m.name)) medal_silver, sum(('BRONZE' == m.name)) medal_bronze,
             sum( (9 * ('GOLD' == m.name)) +  (3 * ('SILVER' == m.name)) + (1 * ('BRONZE' == m.name))) score,
             C.id competitorID
from result R, competition T, academy A, competitor C, lk_medal M
where R.medal=M.id
  and C.id = R.competitorID
  and A.id = R.academyID
  and T.is_loaded != 10
  and T.id=R.competitionID
  and C.id in %s
 group by  competitor
 order by medal_gold DESC, medal_silver DESC, medal_bronze DESC, medals DESC, competitions DESC
"""

stmD = """
select T.name competition, T.year year, T.mode mode, A.name academy, C.name competitor, C.birth_year estimated_birth_year,
	   R.gender, R.belt, R.category, R.weight, m.name medal 
 from result R, competition T, academy A, competitor C, lk_medal M
where R.medal=M.id
  and C.id = R.competitorID
  and A.id = R.academyID
  and T.is_loaded = 1
  and T.id=R.competitionID 
  and R.competitorID = '%s'
 order by year desc
"""

stmE = "INSERT INTO result VALUES ('%s','%s','%s','%s','%s','%s','%s','%s',%s,'%s')"


my_db = sqlite3.connect('data/my-ibjjf.db')
assert (my_db is not None),"Fail opening database"

srcs = open("my-fake_results.txt", "r")
for row in srcs:
    row = row.strip()
    if row == '': continue
    
    if (not row.startswith('#')):
        index = 0
        row_parts = row.split('-')
        
        competitionID = row_parts[index]
        index +=1
        
        academyID = row_parts[index]
        index +=1
        
        belt = row_parts[index]
        index +=1
        
        category = row_parts[index]
        index +=1
        if category == 'MASTER' or category == 'JUVENILE' or category == 'PEE-WEE':
            category = category + '_' + row_parts[index]
            index +=1
        
        gender = row_parts[index]
        index +=1
        
        weight = row_parts[index]
        index +=1
        
        competitorID = row_parts[index]
        index +=1
        
        if len(row_parts) != index:
            weight = weight + '_' + competitorID
            competitorID = row_parts[index]
        
        row = row.replace("-" + academyID, "")
        row = row.replace('-#','')
        row = row.replace('LIGHT-FEATHER','LIGHT_FEATHER')
        row = row.replace('MEDIUM-HEAVY','MEDIUM_HEAVY')
        row = row.replace('ULTRA-HEAVY','ULTRA_HEAVY')
        row = row.replace('SUPER-HEAVY','SUPER_HEAVY')
        row = row.replace('OPEN CLASS','OPEN_CLASS')
        row = row.replace('MASTER-1','MASTER_1')
        row = row.replace('MASTER-2','MASTER_2')
        row = row.replace('MASTER-3','MASTER_3')
        row = row.replace('MASTER-4','MASTER_4')
        row = row.replace('MASTER-5','MASTER_5')
        row = row.replace('MASTER-6','MASTER_6')  
        row = row.replace('_#','').strip()
    
        rowID  ="FAKE_" + row
        try:
            #print "[INFO] Inserting fake result (%s,%s,%s,%s,%s,%s)"%(competitionID,belt,category,gender,weight,competitorID)
            if DEBUG_SQL or competitorID == DEBUG_COMPETITORID:
                print 100*'*'
                print stmE%((rowID, competitionID, academyID, competitorID, belt, category, gender, weight, 0,row))
                print 100*'*' 
            my_db.execute(stmE%((rowID, competitionID, academyID, competitorID, belt, category, gender, weight, 0,row)))
        except: pass

my_db.commit()

competitionID = None
competitionName = None
competitorID = None
competitionName = None
resultFilter = None
        

print "%s"%(80*'=')
print "Informe competiciones proximas para '%s.' "%(MY_TEAM)
print "%s"%(80*'=')
print "\n"

if DEBUG_SQL or competitorID == DEBUG_COMPETITORID:
    print 100*'='
    print stmA%(MY_TEAM)
    print 100*'='

for row in my_db.execute(stmA%(MY_TEAM)):
     
    if competitorID != row[2] or competitorID is None: 
        if competitorID is not None: print "\n%s"%(80*'-')
        print "Competidor: %s."%(row[3].title())
        competitionID = None
    else: 
        assert False
        continue
        
    if competitionID != row[0]:
          print "\n\tCompeticion: %s."%(row[1]) 

    competitionID = row[0]
    competitionName = row[1]
    competitorID = row[2]
    competitionName = row[3]
    resultFilter = row[4].replace(row[2],'%')
    
    if DEBUG_SQL or competitorID == DEBUG_COMPETITORID:
        print 100*'='
        print stmB%(competitorID, resultFilter)
        print 100*'='

    oponents = {}
    
    filterOponents = "('IMPOSSIBLEISNOTHING'"
    for row_o in my_db.execute(stmB%(competitorID, resultFilter)): 
        filterOponents += ",'%s'"%(row_o[0])
    filterOponents += ")"
 
    if DEBUG_SQL or competitorID == DEBUG_COMPETITORID:
        print 100*'='
        print stmC%(filterOponents)
        print 100*'='
     
    for row_t in my_db.execute(stmC%(filterOponents)):
        if row_t[3] > 1:
            oponents[row_t[9]] = row_t[0].title()
            print "\t\t* Oponente: (%s) %s - %s medallas on %s competiciones (%s,%s,%s) - %.2f %% exito, score: %s."%(row_t[1].title(), row_t[0].title(), 
                     row_t[4], (row_t[3]-1), row_t[5], row_t[6], row_t[7], 100.0 * (1.0 * row_t[4]/(row_t[3]-1)), row_t[8])
        else:
            print "\t\t* Oponente: (%s) %s - NO SE ENCONTRO EXPERIENCIA PREVIA."%(row_t[1].title(), row_t[0].title())
            

    print "\n\t\t Historial oponentes."
    for row_op in oponents.keys():
        print "\t\t\t* Oponente: %s."%(oponents[row_op])
        
        if DEBUG_SQL or competitorID == DEBUG_COMPETITORID:
            print 100*'='
            print stmD%(row_op)
            print 100*'='
            
        for row_opd in my_db.execute(stmD%(row_op)):
            medal = row_opd[10].replace("N/A","")
            medal = medal.replace("GOLD"," - Medalla de ORO")
            medal = medal.replace("SILVER"," - Medalla de PLATA")
            medal = medal.replace("BRONZE","- Medalla de BRONCE")
            print "\t\t\t\t* [%s] '%s' %s - (%s/%s/%s)."%(row_opd[1], row_opd[0], medal, row_opd[7].lower(), row_opd[8].lower(), row_opd[9].lower())
            
sys.exit(0)            
my_db.execute("delete from result where id like 'FAKE%%'")
my_db.commit()