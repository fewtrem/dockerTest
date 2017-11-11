'''
Created on 16 Oct 2017

@author: s1144899
'''
from smootheComp import smootheComp
from skel150 import matchUp150
from constants import STACKTYPE,ID,CHAN,BRAIN,VNC,FLIP,LAB

sC = smootheComp("/media/s1144899/My Passport/QuickCondense/All_May2017_")
mU150 = matchUp150("/media/s1144899/My Passport/QuickCondense/productionised/")

thisOne = {STACKTYPE:BRAIN,
           ID:'5302640',
           FLIP:'F',
           CHAN:'G',
           LAB:'1'}

simList = sC.findSimilar(thisOne,0.25,False)
simListRef = mU150.findSimilar(thisOne, simList)

print simListRef[1],"Skipped"
print simListRef[0][:10]


