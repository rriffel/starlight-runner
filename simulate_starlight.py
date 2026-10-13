#!/usr/bin/python
import os, glob
from pylab import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from scipy import interpolate
import re
import time
import pandas as pd


#gals = glob.glob('../*.spec')
#gals=[re.sub('../','',g) for g in gals]

gals = glob.glob('./agns_Xshoot_NIR/*.spec')
gals=[re.sub('./agns_Xshoot_NIR/','',g) for g in gals]

def create_spec(run=False, gals=gals):
  if run:
    for gl in gals:
            print('Doing File: '+gl)
            gal=re.sub('\n','',gl)
            (lam,flx,eflx)=np.loadtxt('../'+gal,unpack=True)

            tmp=re.split('\.',gal)
            for i in range(1,100):
                name=tmp[0]+'_model_'+str(i)+'.'+tmp[-1]
                eflx[where(eflx <= 0)]=1e-20
                sflx=np.random.normal(flx,(eflx))
                save=np.column_stack((lam,sflx,eflx))
                np.savetxt(gal.replace('.spec','_model_'+str(i)+'.spec'),
                           save,fmt='%.2F   %.2E    %.2E')


def run_pylight(lista,config):
    f=open(config).readlines()
    galaxies=np.loadtxt(lista,dtype='U100, float')
    for g,d in galaxies:
       lst=open('list.temp','w+')
       lst.write('./synt/'+g+' '+str(d)+'\n')
       go = re.sub('.out','',g)
       for k in range(1,100):
             lst.write('./synt/'+go+'_model_'+str(k)+'.out '+str(d)+'\n')
       lst.close()
       inp=open('ConfigPylight.temp','w+')
       for i in f:
           if 'outfile=' in i: inp.write('outfile=\''+re.split('_',g)[0]+'.props\'\n')
           elif 'datafile=' in i: inp.write('datafile=\'list.temp\' \n')
           elif 'doPlots' in i: inp.write('doPlots=False \n')
           else: inp.write(i)
       inp.close()
       t=open('run.sh','w+')
       t.write('python pylight.py '+'ConfigPylight.temp' +'\n')
       t.close()
       os.system('sh run.sh')

def mean_values(gals,outname):
     out=open(outname,'w+')
     df=pd.read_table(gals[0],delim_whitespace=True)
     column_headers = list(df.columns.values)[1:]
     out.write('#Source           ')
     for p in column_headers:
           out.write(p+'   std_'+p+'  ') 
     out.write('\n')
 
     for gal in gals:
       df=pd.read_table(gal,delim_whitespace=True)
       column_headers = list(df.columns.values)[1:]
       out.write('{:<15}'.format(gal.split('.props')[0]))
       for p in column_headers:
           if 'Mage' in p: out.write('   {:.2E}'.format(np.nanmean(10**df[p])/1E9)+'  {:.2E}'.format(np.nanstd(10**df[p]/1E9)) )
           else: out.write('   {:.2E}'.format(np.nanmean(df[p]))+'  {:.2E}'.format(np.nanstd(df[p])) )
       out.write('\n')
 

def create_lists(galaxies,listname,config,outdir,sufix):
    f=open(config).readlines()
    gals=np.loadtxt(galaxies,dtype='str')
    lst=open(listname,'w+')
    for gs,dis in gals:
        go = re.sub('.out','',gs)
        lst.write(outdir+gs+' '+dis+'\n')
        for k in range(1,100):
           lst.write(outdir+go+'_model_'+str(k)+'.out '+dis+'\n')
    lst.close()
    inp=open('ConfigPylight.temp','w+')
    for i in f:
       if 'outfile=' in i: inp.write('outfile=\''+listname.split('.')[0]+sufix+'_props.dat\'\n')
       elif 'datafile=' in i: inp.write('datafile=\''+listname+'\'\n')
       elif 'doPlots' in i: inp.write('doPlots=False \n')
       else: inp.write(i)
    inp.close()
    t=open('run.sh','w+')
    t.write('python pylight.py '+'ConfigPylight.temp' +'\n')
    t.close()
    os.system('sh run.sh')


      

config='ConfigPylight_simulated'
#lista='../synt/list_All_sources.txt'
#gals = glob.glob('./agns_Xshoot_NIR/*3717*.spec') + glob.glob('./agns_Xshoot_NIR/*3749*.spec') 


#gals=[re.sub('./agns_Xshoot_NIR/','',g) for g in gals]

#create_spec(True,gals)


agns='../synt/list_AGNs.txt'
ctrl='../synt/list_CTR.txt'
#ctrl2='../synt/list_CTR_short.txt'

agn=[re.split('_',g)[0]+'.props' for g in np.loadtxt(agns,unpack=True,usecols=(0,),dtype='U100')]

ctr=[re.split('_',g)[0]+'.props' for g in np.loadtxt(ctrl,unpack=True,usecols=(0,),dtype='U100')]

run_pylight(ctrl,config)
run_pylight(agns,config)
mean_values(agn,'MeanPars_AGNsFULLONPT.dat')
mean_values(ctr,'MeanPars_CTRsFULLONPT.dat')

create_lists(agns,'simulated_AGNsONPT.txt',config,'synt/','FULLONPT')

create_lists(ctrl,'simulated_CTRLONPT.txt',config,'synt/','FULLONPT')

#create_lists(ctrl2,'simulated_CTRL2.txt',config,'synt/','FULL')
