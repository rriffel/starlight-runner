#!/home/riffel/anaconda3/envs/astroconda/bin/python/
import os, glob
from matplotlib.pylab import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from scipy import interpolate
import re
import time
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
#import pystarlight.io.starlighttable; 
from ReadStarlightParameters import starlightPars
from ReadStarlightParameters import popVectors
from ReadStarlightParameters import StSyntesis
import importlib.machinery
import gc
#import atpy; 
start_time = time.time()
localtime = time.asctime(time.localtime(time.time()) )
version='4.0 - stable working in Python 3'
from PyPopStarsLogo import Logo
Logo()



###################################################################
#                                                                 #
#              Configuration to run pylight                       #
#                                                                 #
###################################################################
my_conf_file=sys.argv[1]

# Getting the confuration key from the config file

#key = imp.load_source('data','',open(my_conf_file))

key = importlib.machinery.SourceFileLoader('confiFile',my_conf_file).load_module() 


print("\n^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.\n")
print("\t\t You are running pylight version: "+str(version))
print("\n^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.^.\n")
print("\n\t If you are doing the plots and movies it my take 10 seconds per file\n\n")

print("*******************************************************************************\n")

print("Started at :", localtime)

print("....................................\n")

rrfail=open('fail.txt','w+')



#######################  Main Program ###########################
#                                                               #
#              Header of the output file                        #
#                                                               #
##################################################################

######## DO NOT CHANGE ##############
y=0  # NOT CHANGE
x=0  # NOT CHANGE
failFile=0 # only to correct the cube possition.
movelist=[]
exception=False
######## DO NOT CHANGE ##############


if key.doPlots:
    if (os.path.exists(key.figsdir)==False): 
        os.mkdir(key.figsdir)


spaces='       '
formf='{:.2F}'
forme='{:.2E}'
savefile = open(key.outfile,'w+')
savefile.write ("#File                                  ")

Table=open(key.datafile)
inputfiles = Table.readlines()

if key.datacube:
        if (len(inputfiles)) != ((key.xcol+1)*(1+key.ycol)):
           key.datacube=False
           print('Number xcol and ycols are inconsistent with the number of files in the inputfile. Setting datacube=False')

if key.IsAGNComp:

        for w in key.BinFCVecLab:
            savefile.write (str(w))
            sp=10-len(str(w))
            for s in range(sp):
              savefile.write(' ')


        for w in key.BinHDVecLab:
            savefile.write (str(w))
            sp=10-len(str(w))
            for s in range(sp):
              savefile.write(' ')

#  End of if block

for w in key.BinPopVecLab:
    savefile.write (str(w))
    sp=10-len(str(w))
    for s in range(sp):
      savefile.write(' ')


for w in key.BinPopVecMassLab:
    savefile.write (str(w))
    sp=10-len(str(w))
    for s in range(sp):
      savefile.write(' ')

if key.SaveDist:
        savefile.write ("Av        Mage_L    Mage_M    MZ_L      MZ_M      M*        M*in      ")
        for w in key.BinSFRLabs:
            savefile.write (w)
            sp=15-len(str(w))
            #print sp
            for s in range(sp):
              savefile.write(' ')
        savefile.write ("F_Norm    Adev      ChiSqrt   SNR   GalDist\n")
else:
        savefile.write ("Av        Mage_L    Mage_M    MZ_L      MZ_M      M*        M*in      ")
        for w in key.BinSFRLabs:
            savefile.write (w)
            sp=15-len(str(w))
            for s in range(sp):
              savefile.write(' ')
        savefile.write ("F_Norm    Adev      ChiSqrt   SNR \n")
        
# Variation over all files.

for filein_i in inputfiles:
        filTemp=re.sub('\n','',filein_i)
        (filein,gal_D) = re.split(" ",filTemp)
        outname=filein.rsplit('\.',1)
        savefile.write(filein)
        spc=40-len(filein)
        if spc <=0:
          spc=2
        for s in range(spc):
             savefile.write(" ")


#########################################################
#                                                       #
#    Getting the necessary parameters to make the       #
#    plots and analysis of the synthesis output         #
#########################################################

        try:
                
                # Getting the genneral fits paramenters.
                pars=starlightPars(filein)
                print('doing file: '+filein+' computed with Starlight version '+ pars[-1])
                # getting some paramenters of interest
                if pars[-1]=='V4':
                    chi2= pars[0][0]
                    fobs_norm= pars[0][1]
                    adev= pars[0][2]
                    Mini_tot=pars[0][4]
                    Mcor_tot=pars[0][5]
                    av= pars[0][6]
                    SNR=pars[0][13]
                    SumPopVecs=pars[0][15]
                    # Making some calculations for the SFR and total mass, see STARLIGHT manual, page: 22
                    # 1 Mpc = 3.08567758E24 centimeters assuming it.
                    gd= (3.08567758E24)*float(gal_D)
                    Mini_t = key.NormFac*(Mini_tot * 4.0*np.pi)*gd**2/ 3.826E33 
                    Mcor_t = key.NormFac*(Mcor_tot * 4.0*np.pi)*gd**2/ 3.826E33 
                elif pars[-1]=='V5':
                    chi2= pars[0][0]
                    fobs_norm= pars[0][3]
                    adev= pars[0][6]
                    av= pars[0][10]
                    SNR=pars[0][16]
                    SumPopVecs=pars[0][18]
                    # Making some calculations for the SFR and total mass, see STARLIGHT manual, page: 22
                    # 1 Mpc = 3.08567758E24 centimeters assuming it. 
                    #
                    # IMPORTANT: For V5 the values of Mini_t and Mcor_t are taken from the output file.
                    if float(pars[0][5]) != float(gal_D):
                       # Testing if distance is OK. If not using starlight input distance.
                       print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
                       print("The distance informed in the input file and in the config files are not equal:\n")
                       print("Distance in Starlight: " +str(pars[0][5])+" Distance in ConfigFile: "+str(gal_D))
                       print("For consistency I'm setting value to Starlight output = "+str(pars[0][5]))
                       print("Check this value or do not consider all values depending on distance.")
                       print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
                       gal_D=pars[0][5]
                    gd= (3.08567758E24)*float(gal_D)
                    Mini_t = pars[0][8]#key.NormFac*(Mini_tot * 4.0*np.pi)*gd**2/ 3.826E33 
                    Mcor_t =pars[0][9] #key.NormFac*(Mcor_tot * 4.0*np.pi)*gd**2/ 3.826E33 



                # getting the population vectors paramenters.
                popVecs=popVectors(filein)
               #Separating the population vectors parameters in arrays.
                popx=popVecs[0][:,0] * (100./ sum(popVecs[0][:,0])) # renormalized to 100%
                popMi=popVecs[0][:,1] * (100./ sum(popVecs[0][:,1])) # renormalized to 100%
                popm=popVecs[0][:,2] * (100./ sum(popVecs[0][:,2]))  # renormalized to 100%
                
               # print sum(popx), sum(popm), SumPopVecs
                
                popage=popVecs[0][:,3]
                popZ=popVecs[0][:,4]
                components=popVecs[1]
                # Getting the observed and synthetic spectra. This will be used in the plots
                sintRes=StSyntesis(filein)
                l_obs=sintRes[:,0]
                f_obs=sintRes[:,1]
                f_syn=sintRes[:,2] 
                wei=sintRes[:,3]

                #########################################################
                #                                                       #
                #                Saving residuals                       #
                #                                                       #
                #########################################################
                if key.SaveResidual:
                     restemp=(f_obs-f_syn)*fobs_norm
                     resSave=np.column_stack((l_obs,restemp))
                     np.savetxt(outname[0]+'.res',resSave)
                     print("Residual spectrum saved:",outname[0]+'.res')


                #########################################################
                #                                                       #
                #    Extracting the Bined population Vectors            #
                #                                                       #
                #########################################################
                PopBin=[]
                PopBinLAge=[]
                PopBinL=[]
                PopBinMAge=[]
                for bins in key.BinPopVecLab:
                      PopBini= (np.sum( popx[(popage >  key.BinPopVec[bins][0]) & (popage <= key.BinPopVec[bins][1] )]) )
                      PopBin.append(PopBini)
                #     Only for the plot 
                      PopBinL.append(PopBini)
                      PopBinLAge.append((key.BinPopVec[bins][0] + key.BinPopVec[bins][1])/2)
                # I'm adding the mass fractions to the same vector of light fractions, it helps in storring them below.
                PopBinM=[]
                PopBiniM=[]
                for mass in key.BinPopVecLab:
                      PopBiniM=(np.sum( popm[(popage >  key.BinPopVec[mass][0]) & (popage <=key.BinPopVec[mass][1] )]) )
                #     Only for the plot 
                      PopBin.append(PopBiniM)
                      PopBinM.append(PopBiniM)
                      PopBinMAge.append((key.BinPopVec[mass][0] + key.BinPopVec[mass][1])/2)


                #########################################################
                #                                                       #
                #    Extracting mean AGE and Mean Metallicities         #
                #                                                       #
                #########################################################
                l=0
                sumvec=[]
                for component in components:
                    if ('BB_') not in component:
                        if ('Power') not in component:
                               sumvec.append(l)
                    l=l+1
                meanAgex=sum(((100*(popx[sumvec])/sum(popx[sumvec]))/100)*np.log10(popage[sumvec])) # here it was renormalized in order to the stellar fraction sum 100%, since only it gives mean SP age.
                meanZx= sum(((100*(popx[sumvec])/sum(popx[sumvec]))/100)*popZ[sumvec]) # here it was renormalized in order to the stellar fraction sum 100%

                meanAgem= sum(((100*(popm[sumvec])/sum(popm[sumvec]))/100)*np.log10(popage[sumvec])) # here it was renormalized in order to the stellar fraction sum 100%
                meanZm=sum(((100*(popm[sumvec])/sum(popm[sumvec]))/100)*popZ[sumvec]) # here it was renormalized in order to the stellar fraction sum 100%


                #########################################################
                #                                                       #
                #            Extracting SFR paramenters                 #
                #                                                       #
                #########################################################
                
                SFR=[]
                for bins in key.BinSFRLabs:
                      SFR_t=(np.sum( popMi[ (popage >  key.BinSFR[bins][0]) & (popage <= key.BinSFR[bins][1] )]))
                      SF=key.BinSFR[bins][1] - key.BinSFR[bins][0]
                      SFR.append(( (SFR_t/100) * Mini_t)/SF)
            





                if key.IsAGNComp or key.OnlyFC:
                        #########################################################
                        #                                                       #
                        #              Extracting AGN Components                #
                        #                                                       #
                        #########################################################

# Searching for the FC components. Here I'm using the string vector with the component_j names. serching for those with Power in the name, wich means the FC, nothe here that the power is multiplied by 100.
                        ind=0
                        nu=np.zeros(0)
                        fcind=[]
                        for comp in components:
                            if 'Power' in comp:
                                 ptmp=re.split('\_',comp)
                                 nui=float(ptmp[1])/100.
                                 nu=np.append(nu,nui)
                                 fcind.append(ind)
                            ind=ind+1
                        FCBin=[]
                        for fc in key.BinFCVecLab:
                              FCBini= (np.sum( popx[fcind][(nu >  key.BinFCVec[fc][0]) & (nu <=key.BinFCVec[fc][1] )]) )
                              FCBin.append(FCBini)

                        # Searching for the hot dust components, using the same idea as for the FC
                        # i = hdind
                        ind=0
                        BB=np.zeros(0)
                        hdind=[]
                        for comp in components:
                            if 'BB_' in comp:
                                 ptmp=re.split('\_',comp)
                                 BBi=float(ptmp[1])
                                 BB=np.append(BB,BBi)
                                 hdind.append(ind)
                            ind=ind+1
                        HDBin=[]
                        for Temp in key.BinHDVecLab:
                              HDBini=(np.sum( popx[hdind][(BB >  key.BinHDVec[Temp][0]) & (BB <=key.BinHDVec[Temp][1] )]) )
                              HDBin.append(HDBini)


                #############################################################
                #                                                           #
                #                Storing the extracted Parameters           #
                #                                                           #
                #############################################################

                #############################################################
                #                                                           #
                #                Storing the AGN Parameters                 #
                #                                                           #
                #############################################################

                if key.IsAGNComp: # or key.OnlyFC:
#                        print "Passou"
                        for fc in FCBin:
                            savefile.write(str(formf.format(fc)))
                            sp=10-len(str(formf.format(fc)))
                            for s in range(sp):
                              savefile.write(' ')
                              
                        for t in HDBin:
                            savefile.write(str(formf.format(t)))
                            sp=10-len(str(formf.format(t)))
                            for s in range(sp):
                              savefile.write(' ')
#                        print fc

                #############################################################
                #                                                           #
                #                Storing the Default Parameters             #
                #                                                           #
                #############################################################


                for p in PopBin:
                    savefile.write(str(formf.format(p)))
                    sp=10-len(str(formf.format(p)))
                    for s in range(sp):
                      savefile.write(' ')

                sp=10-len(str(formf.format(av)))
                savefile.write(str(formf.format(av)))
                for s in range(sp):
                      savefile.write(' ')


                sp=10-len(str(formf.format(meanAgex)))
                savefile.write(str(formf.format(meanAgex)))
                for s in range(sp):
                      savefile.write(' ')

                sp=10-len(str(formf.format(meanAgem)))
                savefile.write(str(formf.format(meanAgem)))
                for s in range(sp):
                      savefile.write(' ')


                sp=10-len(str('{:.4}'.format(meanZx)))
                savefile.write(str('{:.4}'.format(meanZx)))
                for s in range(sp):
                      savefile.write(' ')

                sp=10-len(str('{:.4}'.format(meanZm)))
                savefile.write(str('{:.4}'.format(meanZm)))
                for s in range(sp):
                      savefile.write(' ')

        #M*        M*in      SFR

                sp=10-len(str(forme.format(Mcor_t)))
                savefile.write(str(forme.format(Mcor_t)))
                for s in range(sp):
                      savefile.write(' ')

                sp=10-len(str(forme.format(Mini_t)))
                savefile.write(str(forme.format(Mini_t)))
                for s in range(sp):
                      savefile.write(' ')

                for sf_t in SFR:
                    sp=15-len(str(forme.format(sf_t)))
                    savefile.write(str(forme.format(sf_t)))
                    for s in range(sp):
                      savefile.write(' ')

                sp=10-len(str(forme.format(fobs_norm)))
                savefile.write(str(forme.format(fobs_norm)))
                for s in range(sp):
                      savefile.write(' ')




                sp=10-len(str(formf.format(adev)))
                savefile.write(str(formf.format(adev)))
                for s in range(sp):
                      savefile.write(' ')
                sp=10-len(str(formf.format(chi2)))
                savefile.write(str(formf.format(chi2)))
                for s in range(sp):
                      savefile.write(' ')

                if key.SaveDist:
                        sp=10-len(str(formf.format(SNR)))
                        savefile.write(str(formf.format(SNR)))
                        for s in range(sp):
                              savefile.write(' ')
                        savefile.write(str(formf.format(float(gal_D)))+"\n")
                else:
                        savefile.write(str(formf.format(SNR))+"\n")
                failFile=0 # only to correct the cube possition.
        except Exception as e: 
                print(e) 
                plotsAns=key.doPlots
                key.doPlots=False
                exception=True
                errortoprint= "===>>> Problem with input file: "+filein+" <<<=== :(  "
                rrfail.write(filein+'\n')
               
                if key.SaveDist:
                        temp=12
                else:
                        temp=11
                if key.IsAGNComp:
                        test=len(key.BinPopVecMassLab)+len(key.BinPopVecLab)+len(key.BinFCVecLab)+len(key.BinHDVecLab) + temp
                else:
                        test=len(key.BinPopVecMassLab)+len(key.BinPopVecLab) + temp
                for el in range(0,int(test)):
                     savefile.write('NaN       ')
                savefile.write('\n')
                if key.datacube:
                    failFile=failFile+1 # only to correct the cube possition.
                #########################################################
                #                                                       #
                #                Saving residuals                       #
                #                                                       #
                #########################################################
                if key.SaveResidual:
                   try:
                        sintRes=StSyntesis(filein)
                        l_obs=sintRes[:,0]
                        f_obs=sintRes[:,1]
                        f_syn=sintRes[:,2] 
                        wei=sintRes[:,3]
                        restemp=(f_obs-f_syn)*fobs_norm
                        resSave=np.column_stack((l_obs,restemp))
                        np.savetxt(outname[0]+'.res',resSave)
                        errortoprint= "===>>> Problem with input file: "+filein+" <<<=== :( BUT RESIDUAL WAS SAVED "
                   except Exception as e:
                       print(e)
                       errortoprint= "===>>> Problem with input file: "+filein+" <<<=== :( NOT POSSIBLE TO SAVE RESIDUAL "
                print(errortoprint)

################  END EXTRACTION PART #####################################

        if key.doPlots:
                #########################################################
                #                                                       #
                #    Ploting the Observed and Sinthetic Spectra         #
                #                                                       #
                #########################################################
                
                if not key.inter:
                        if key.IsAGNComp:
                                fig=plt.figure(figsize=(7.9,10))
                        else:
                                fig=plt.figure(figsize=(7.9,8.5))
                        title=outname[0]
                        fig.suptitle(title, fontsize=16)

                sintPlt=axes([0.1,0.75,0.85,0.2])
                setp(sintPlt.get_xticklabels(), visible=False)
                # Setting limits
                sintPlt.set_xlim((np.min(l_obs)-150),(np.max(l_obs)+150))
                # Plotting the observed spectrum
                sintPlt.plot(l_obs,f_obs,color='black',label='obs')


#                #########################################################
#                #                                                       #
#                #    Ploting the Synthetic Spectrum                     #
#                #                                                       #
#                #########################################################



                sintPlt.plot(l_obs,f_syn,color='red',label='synt.')
                sintPlt.legend(loc=0,frameon=False,ncol=1,prop={'size':12})
                sintPlt.set_ylabel('Norm. Flux')

                #############################################################
                #                                                           #
                #                  Ploting Residuals                        #
                #                                                           #
                #############################################################

                sintres=axes([0.1,0.63,0.85,0.12])
                sintres.set_xlim((np.min(l_obs)-150),(np.max(l_obs)+150))
                sintres.plot(l_obs,(f_obs - f_syn),color='black',label='residual')
                zero=np.zeros(len(l_obs))
                sintres.plot(l_obs,zero, color='blue',ls='--')
                #########################################################
                #                                                       #
                #    Ploting the masked point on the Spectrum           #
                #                                                       #
                #########################################################
                if key.pltmask:
                        lst = []
                        lastpixmask=False
                        if (wei<=0)[-1]==True:
                           wei=np.append(wei[:-1],[1.0])
                           lastpixmask=True
                        for i in range(len(wei)-1):
                        # Testing true or false in the arrays to get the indexes where f_obs is masked 
                          if (wei<=0)[i]==(wei<=0)[i+1]:
                              continue
                          else:
                              lst.append(i)

                        # Making the plots of the masked parts. In the case where the first pixel is masked.
                        if (wei<=0)[0]==True:
                            sintres.plot(l_obs[0:lst[0]],(f_obs[0:lst[0]]-f_syn[0:lst[0]]),ls='solid',color='magenta',lw=1,label='mask')
                            for i in range(1,len(lst)-1,2):
                              sintres.plot(l_obs[lst[i]:lst[i+1]],(f_obs[lst[i]:lst[i+1]]-f_syn[lst[i]:lst[i+1]]),ls='solid',color='magenta',lw=1)

                        # Making the plots of the masked parts. In the case where the first pixel is NOT masked.
                        if ((wei<=0)[0]==False ):
                            sintres.plot(l_obs[lst[0]:lst[1]],(f_obs[lst[0]:lst[1]]-f_syn[lst[0]:lst[1]]),ls='solid',color='magenta',lw=1,label='mask')
                            for i in range(1,len(lst)-1,2):
                              sintres.plot(l_obs[lst[i+1]:lst[i+2]],(f_obs[lst[i+1]:lst[i+2]] - f_syn[lst[i+1]:lst[i+2]]),ls='solid',color='magenta',lw=1)
                            if lastpixmask:
                              sintres.plot(l_obs[-2:,],(f_obs[-2:,]-f_syn[-2:,]),ls='solid',color='magenta',lw=1)

#                Closing the plot of the residuals
                sintres.legend(loc=0,frameon=False,ncol=1,prop={'size':12})
                sintres.set_xlabel(r'$\lambda (\AA)$')
                ytictmp = sintres.get_yticks()[:-2]
                sintres.set_yticks(ytictmp)

                
                
                
                
                
                #############################################################
                #                                                           #
                #                 Age/Mass x Fractions histograms           #
                #                                                           #
                #############################################################

                # Histograms - Summed ages 

                xlim=[1e5,20e9]  # do not change
                ylim=[0,100] # do not change

                ############## Making log scale in the x axis ###############
                if key.IsAGNComp:
                    axlog=axes([0.1,0.38,0.2125,0.2],frameon=True,facecolor=None)
                else:
                    axlog=axes([0.1,0.1,0.2125,0.4],frameon=True,facecolor=None)
                axlog.set_xlim(xlim)
                axlog.set_xscale('log')
                axlog.set_ylim(ylim)
                axlog.set_xlabel('Age')
                axlog.set_ylabel('%')
                if key.IsAGNComp:
                    ages=axes([0.1,0.38,0.2125,0.2],frameon=False)
                else:
                   ages=axes([0.1,0.1,0.2125,0.4],frameon=False)
                setp(ages.get_xticklabels(), visible=False)
                setp(ages.get_xminorticklabels(), visible=False)
                setp(ages.get_yticklabels(), visible=False)
                setp(ages.get_yminorticklabels(), visible=False)
                ages.get_xaxis().set_ticks([])
                ages.get_yaxis().set_ticks([])



                ages.set_xlim(np.log10(xlim))
                ages.set_ylim(ylim)
                #Summing Fractions for all ages in Zs.
                summedpopx=[]
                summedpopxTemp=[]
                summedpopm=[]
                summedpopmTemp=[]

                for z in key.Zs:
                    if(len(popZ[popZ==z]) ==0):
                        print('Metallicity',z,' is not in the base, I hope you know wath you are doing!')
                    summedpopxTemp.append(popx[popZ==z])
                    summedpopxTemp2=np.column_stack(summedpopxTemp)
                    summedpopmTemp.append(popm[popZ==z])
                    summedpopmTemp2=np.column_stack(summedpopmTemp)

                for ind in range(0,len(summedpopxTemp2)):
                      summedpopx=np.append(summedpopx,sum(summedpopxTemp2[ind]))
                      summedpopm=np.append(summedpopm,sum(summedpopmTemp2[ind]))

                summedpopages=popage[popZ==key.Zs[0]]
                ages.bar(np.log10(summedpopages),summedpopx,width=0.4,align='center',color='None',edgecolor='blue',label='$\Sigma x_j$')
                ages.bar(np.log10(summedpopages),summedpopm,width=0.2,align='center',color='None',edgecolor='red',label=r'$\Sigma\mu_j$',ls='dotted')
                ages.legend(loc=0,frameon=False,ncol=1,prop={'size':12})

                ############## Making log scale in the x axis ###############
                if key.IsAGNComp:
                    axlogz=axes([0.3125,0.38,0.2125,0.2],frameon=True,facecolor=None)
                else:
                    axlogz=axes([0.3125,0.1,0.2125,0.4],frameon=True,facecolor=None)
                axlogz.set_xlim(xlim)
                axlogz.set_xscale('log')
                axlogz.set_ylim(ylim)
                setp(axlogz.get_yticklabels(), visible=False)

                # Using a function to set the minor tickmarkers.
                axlogz.set_xticks([1e6,1e7,1e8,1e9,1e10])

                axlogz.set_xlabel('Age')
                if key.IsAGNComp:
                    agesZ=axes([0.3125,0.38,0.2125,0.2],frameon=False)
                else:
                    agesZ=axes([0.3125,0.1,0.2125,0.4],frameon=False)
                setp(agesZ.get_xticklabels(), visible=False)
                setp(agesZ.get_xminorticklabels(), visible=False)
                setp(agesZ.get_yticklabels(), visible=False)
                setp(agesZ.get_yminorticklabels(), visible=False)
                agesZ.get_xaxis().set_ticks([])
                agesZ.get_yaxis().set_ticks([])



                agesZ.set_xlim(np.log10(xlim))
                agesZ.set_ylim(ylim)
                setp(agesZ.get_yticklabels(), visible=False)

                # Variation over all metalicities, weigthed by zsun=0.0
                c=0
                p=100
                Zscolor=['red','magenta','blue','black','cyan','green','yellow']
                Zswidth=[0.3,0.4,0.5,0.6,0.7,0.8,0.9]
                for z in key.Zs:
                    if(len(popZ[popZ==z]) ==0):
                        print('Metallicity',z,' is not in the base, I hope you know wath you are doing!')
                    agesZ.bar(np.log10(popage[popZ==z]),popx[popZ==z],width=Zswidth[c],align='center',color='None',edgecolor=Zscolor[c])
                    agesZ.bar(np.log10(popage[popZ==z]),popm[popZ==z],width=(Zswidth[c]/1.5),align='center',color='None',edgecolor=Zscolor[c],ls='dotted')
                    c=c+1
                    p=p-12.
                    if p > 27:    
                       agesZ.text(5.2,p, '{:.2f}'.format(z/key.zsun)+'Z$\odot$', fontsize=9, color=Zscolor[c-1])
                    if p < 27:
                      print("Z labels were truncated ")


                #############################################################
                #                                                           #
                #                Binned Age/Mass x Fractions histograms     #
                #                                                           #
                #############################################################

                ############## Making log scale in the x axis ###############
                if key.IsAGNComp:
                    Mage_hist=axes([0.525,0.38,0.2125,0.2],frameon=True,facecolor=None)
                else:
                    Mage_hist=axes([0.525,0.1,0.2125,0.4],frameon=True,facecolor=None)
                Mage_hist.set_xlim(xlim)
                Mage_hist.set_xscale('log')
                Mage_hist.set_ylim(ylim)
                setp(Mage_hist.get_yticklabels(), visible=False)

                # Using a function to set the minor tickmarkers.
                Mage_hist.set_xticks([1e6,1e7,1e8,1e9,1e10])

                Mage_hist.set_xlabel('Age')
                if key.IsAGNComp:
                    Mages=axes([0.525,0.38,0.2125,0.2],frameon=False)
                else:
                   Mages=axes([0.525,0.1,0.2125,0.4],frameon=False)
                setp(Mages.get_xticklabels(), visible=False)
                setp(Mages.get_xminorticklabels(), visible=False)
                setp(Mages.get_yticklabels(), visible=False)
                setp(Mages.get_yminorticklabels(), visible=False)
                Mages.get_xaxis().set_ticks([])
                Mages.get_yaxis().set_ticks([])



                Mages.set_xlim(np.log10(xlim))
                Mages.set_ylim(ylim)
                setp(Mages.get_yticklabels(), visible=False)

                #PopBinLAge=PopBinL=PopBinMAge=PopBinM=[]

                c=0
                p=100
                Macolor=['blue','magenta','red','black','cyan','green','yellow']


                for agf in range(len(PopBinLAge)):
                   Mages.bar(np.log10(PopBinLAge[agf]),PopBinL[agf],width=0.4,align='center',color='None',edgecolor=Macolor[c])
                   Mages.bar(np.log10(PopBinMAge[agf]),PopBinM[agf],width=0.2,align='center',color='None',edgecolor=Macolor[c],ls='dotted')
                   c=c+1
                   p=p-12.
                   if p > 27:
                       Mages.text(5.2,p, str(key.BinPopVecLab[agf]), fontsize=9, color=Macolor[c-1])
                   if p < 27:
                      print("Bined vectors Labels were truncated ")

                #############################################################
                #                                                           #
                #                Synthesis Informations                     #
                #                                                           #
                #############################################################
# ****
                if key.IsAGNComp:
                    Infos=axes([0.7375,0.38,0.2125,0.2],frameon=False,facecolor=None)
                    setp(Infos.get_xticklabels(), visible=False)
                    Infos.get_xaxis().set_ticks([],visible=False)
                    Infos.get_yaxis().set_ticks([],visible=False)
                    setp(Infos.get_xminorticklabels(), visible=False)
                    setp(Infos.get_yticklabels(), visible=False)
                    setp(Infos.get_yminorticklabels(), visible=False)

                if key.OnlyFC:
                        Infos=axes([0.8083,0.1,0.1417,0.4],frameon=False,facecolor=None)
                        setp(Infos.get_xticklabels(), visible=False)
                        Infos.get_xaxis().set_ticks([],visible=False)
                        Infos.get_yaxis().set_ticks([],visible=False)
                        setp(Infos.get_xminorticklabels(), visible=False)
                        setp(Infos.get_yticklabels(), visible=False)
                        setp(Infos.get_yminorticklabels(), visible=False)

                        FcAxes=axes([0.7375,0.1,0.0709,0.4])
                        FcAxes.bar(nu,popx[fcind],width=0.3,align='center',color='None',edgecolor='blue')

#                         Using a function to set the minor tickmarkers.
                        minorLocator   = MultipleLocator(0.125)
                        FcAxes.xaxis.set_minor_locator(minorLocator)
                        FcAxes.set_xlim(1,2)
                        FcAxes.set_xticks([1.25,1.50,1.75])
                        FcAxes.set_xticklabels(['1.25','1.50','1.75'], rotation=90,size=7)
                        FcAxes.set_ylim(0,100)
                        FcAxes.set_xlabel(r'$\alpha$')
                        setp(FcAxes.get_yticklabels(), visible=False)
                        FcAxes.text(1.5,70,r'FC (F$_\nu \propto \nu^{-\alpha}}$)' , fontsize=10, color='k',rotation='vertical')
#                       FcAxes.set_ylabel('%')

                    
                else:
                    Infos=axes([0.7375,0.1,0.2125,0.4],frameon=False,facecolor=None)
                    setp(Infos.get_xticklabels(), visible=False)
                    Infos.get_xaxis().set_ticks([],visible=False)
                    Infos.get_yaxis().set_ticks([],visible=False)
                    setp(Infos.get_xminorticklabels(), visible=False)
                    setp(Infos.get_yticklabels(), visible=False)
                    setp(Infos.get_yminorticklabels(), visible=False)
                
                Infos.set_xlim([0,1])
                Infos.set_ylim([0,1])


# ****
                Infos.text(0.2,0.9,'Synthesis Infos.' , fontsize=10, color='k')
                Infos.text(0.2,0.7,'Av='+str(av) , fontsize=10, color='k')
                Infos.text(0.2,0.6,'<$t_L$>='+str('{:.2F}'.format(meanAgex)) , fontsize=10, color='k')
                Infos.text(0.2,0.5,'<$t_M$>='+str('{:.2F}'.format(meanAgem)) , fontsize=10, color='k')
                Infos.text(0.2,0.4,'<$Z_L$>='+str('{:.4F}'.format(meanZx)) , fontsize=10, color='k')
                Infos.text(0.2,0.3,'<$Z_M$>='+str('{:.4F}'.format(meanZm)) , fontsize=10, color='k')
                Infos.text(0.2,0.2,'$\chi^{2}$='+str('{:.3F}'.format(chi2)) , fontsize=10, color='k')
                Infos.text(0.2,0.1,'Adev='+str('{:.2F}'.format(adev)) , fontsize=10, color='k')
                Infos.text(0.2,0.0,'SNR='+str('{:.0F}'.format(SNR)) , fontsize=10, color='k')


                if key.IsAGNComp:
                        # Including the AGN and FC components to the plot.
                        AGN=axes([0.1,0.1,0.2125,0.2])
                        #setp(AGN.get_yticklabels(), visible=False)
                        AGN.bar(nu,popx[fcind],width=0.1,align='center',color='None',edgecolor='blue')

                        # Using a function to set the minor tickmarkers.
                        minorLocator   = MultipleLocator(0.125)
                        AGN.xaxis.set_minor_locator(minorLocator)
                        AGN.set_xlim(1,2)
                        AGN.set_xticks([1.25,1.75])
                        AGN.set_ylim(0,100)
                        AGN.set_xlabel(r'$\alpha$')
                        AGN.text(1.2,90,r'FC (F$_\nu \propto \nu^{-\alpha}}$)' , fontsize=12, color='k')
                        AGN.set_ylabel('%')

                        # Hot dust 
                        HD=axes([0.3125,0.1,0.2125,0.2])
                        setp(HD.get_yticklabels(), visible=False)
                        # Using a function to set the minor tickmarkers.
                        majorLocator   = MultipleLocator(200)
                        majorFormatter = FormatStrFormatter('%d')
                        minorLocator   = MultipleLocator(50)
                        HD.xaxis.set_major_locator(majorLocator)
                        HD.xaxis.set_major_formatter(majorFormatter)
                        HD.xaxis.set_minor_locator(minorLocator)
                        HD.set_xlabel('T(K)')

                        HD.set_xlim(700,1400)
                        HD.set_xticks([800,1200])
                        HD.set_ylim(0,100)

                        HD.bar(BB,popx[hdind],width=50,align='center',color='None',edgecolor='red')

                if key.datacube:
                        if x > key.xcol:
                          x=0
                          y=y+1
                        cube=axes([0.625,0.1,0.325,0.2])
                        cube.set_title('Cube Position')
                        cube.set_xlim(0,key.xcol)
                        cube.set_ylim(0,key.ycol)
                        cube.plot((x+failFile),y,'ks',markersize=8)
                        cube.set_xlabel('Pixel')
                        cube.set_ylabel('Pixel')
                        x=x+1+failFile
        #                        print filein,x,y
                if key.doPlots:
                        figname=outname[0]
                        savefig(key.figsdir+figname+key.figext)
                        print("Figure: "+figname+key.figext+" saved in "+key.figsdir)
                if key.MakeMovie:
                      if key.figext !='.png':
                          savefig(key.figsdir+figname+'.png')
                      movelist.append(figname+'.png')
                if key.inter:
                        plt.show()

#  This part is to free memory
                if not key.inter:
                        fig.clf()
                        plt.close()
                        del popx,popMi,popZ,popm,l_obs,f_obs,f_syn,zero,popage
                        gc.collect()
        if exception:
        	key.doPlots=plotsAns

if key.MakeMovie:
        movlist = open('list.txt','w+')
        for mv in movelist:
                   movlist.write(key.figsdir+str(mv)+'\n')
        movlist.close()
        command = ('mencoder',
           'mf://@list.txt',
           '-mf',
           'type=png:w=800:h=600:fps='+str(key.FramesSecond),
           '-ovc',
           'lavc',
           '-lavcopts',
           'vcodec=mpeg4',
           '-oac',
           'copy',
           '-o',
           key.MovieName)
        print("\n ****************************************************")
        print("*                                                      *")
        print("*                 CREATING MOVIE                       *")
        print("*                                                      *")
        print("********************************************************\n")
        os.spawnvp(os.P_WAIT, 'mencoder', command)
        print("\n ****************************************************")
        print("*                                                      *")
        print("*                 Movie: "+key.MovieName+" saved")
        print("*                                                      *")
        print("********************************************************\n")
        
if key.figext !='.png':
        pngremove=key.figsdir+'*.png'
        os.system("rm -rf  %s"%(pngremove))


savefile.close()

timet=(time.time() - start_time)/60.0
print("\n ****************************************************")
print("Total running time: ")
print('%2.1f' %(fix(timet)), 'minutes', '%2.1f' %((timet-fix(timet))*60.0), 'seconds')
print("\n ****************************************************")

