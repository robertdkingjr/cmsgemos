import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db.settings")
import django
django.setup()
import datetime

from time import sleep,gmtime,strftime
from ldqm_db.models import *
from ldqm_db.amcmanager import *

RUN_LOCATION = "CERN904"
#RUN_LOCATION = "TIF"


def configure_db():
    # amc_list=[1,2,3,4,5,6,7,8,9,10,11,12]
    amc_list=[10]
    geb_list=[[0,1],[0,1],[0,1],[0,1],[0,1],[0,1],[0,1],[0,1],[0,1],[0,1],[0,1],[0,1],]
    zlist = zip(amc_list, geb_list)
    a_list = []
    for amcN, gtx_list in zlist:
      print "Trying to connect to AMC # %s\n" %(amcN)
      m_AMCmanager = AMCmanager()
      g_list = []
      try:
        m_AMCmanager.connect(int(amcN))
      except ValueError as ve:
        print "AMC unaccessible, Value Error reported"
        continue
      # retrieve VFAT slot numberd and ChipIDs from HW
      for gtx in gtx_list:
        if m_AMCmanager.checkGTX(gtx):  
          try:
            chipids = m_AMCmanager.getVFATs(gtx)
          except TypeError as te:
            print "VFATS unaccessible, Type Error reported"
            continue
          # retrieve VFAT slot numberd and ChipIDs from DB
          vfats = VFAT.objects.all()
          # Check if the VFATs are in DB, add if not
          v_list = []
          for chip in chipids.keys():
            t_chipid = "0x%04x"%(chipids[chip])
            if t_chipid in vfats.filter(Slot=chip).values_list("ChipID", flat=True):
              pass
            else:
              print "Adding VFAT(ChipID = %s, Slot = %d)"%(t_chipid,chip)
              v = VFAT(ChipID = t_chipid, Slot = chip)
              v.save()
            v_list.append(VFAT.objects.get(ChipID = t_chipid, Slot = chip))
          #t_chamberID = 'OHv2aM'#hard code now, read from HW later when available
          t_chamberID = 'GTX-'+str(gtx) #use gtx link number now, read from HW later when available
          print "t_chamberID = %s" %(t_chamberID)
          gebs = GEB.objects.filter(ChamberID=t_chamberID)
          t_flag = False
          for geb in gebs:
            if v_list == list(geb.vfats.all()):
              t_flag = True
              g_list.append(geb)
              break
          if t_flag:
            pass
          else:
            print "Update DB: adding new GEB"
            g = GEB(Type="Long",ChamberID = t_chamberID)
            g.save()
            for v in v_list:
              g.vfats.add(v)
              g_list.append(g)
    
      t_flag = False
      t_boardID = "AMC-"+str(amcN)#hard code now, read from HW later when available
      amcs = AMC.objects.filter(BoardID = t_boardID)
      for amc in amcs:
        if g_list == list(amc.gebs.all()):
          t_flag = True
          a_list.append(amc)
      if t_flag:
        pass
      else:
        print "Update DB: adding new AMC with Board ID %s" %(t_boardID)
        a = AMC(Type="GLIB",BoardID = t_boardID)
        a.save()
        for g in g_list:
          a.gebs.add(g)
          a_list.append(a)
    
    # create a new run. Some values are hard-coded for now
    runs = Run.objects.filter(Period = "2016T", Type = "teststand", Station = RUN_LOCATION)
    rns = list(int(x) for x in list(runs.values_list("Number", flat=True)))
    try:
      nrs = u'%s'%(max(rns)+1)
    except ValueError as ve:
      nrs = u'%s'%(1)
    nrs = nrs.zfill(6)
    # t_date = str(datetime.date.today())
    t_date = strftime("%Y-%m-%d",gmtime())

    m_filename = "run"+str(nrs)+""+"_teststand_"+RUN_LOCATION+"_"+t_date
    newrun = Run(Name=m_filename, Type = "teststand", Number = str(nrs), Date = t_date, Period = "2016T", Station = RUN_LOCATION)
    newrun.save()
    for a in a_list:
      print "Adding to the run AMC %s" %(a.BoardID)
      newrun.amcs.add(a)
    sleep(2)
