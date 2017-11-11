'''
Created on 10 Jun 2017

@author: s1144899
'''
# cell type properties
FLIP = "**F**"
CHAN = "**S**"
ID = "**ID**"
LAB = "**LAB**"
KEY = "**KEY**"
CON = "**CONTRAST**"

# Stack types:
VNC = "**VNC**"
BRAIN = "**BRAIN**"
# stack storage pickle stuff:
STACKTYPE = "**ST**"
ENTRYSET = "**ENTRYSET**"
CELLTYPE = "**CELLTYPE**"
MATCHQUALITY = "**MATCHQUALITY**"
OUTPUTID = "**OUTPUTID**"
REF = "ref"
LABEL = "lab"
SKEL = "skel"
PROJ = "proj"
SCORES = "scores"
SKELREP = "skelRep"
RESPATH = "/media/s1144899/My Passport/Results/"
PATHSHACHIKO = {REF:RESPATH+ID+"/Reformat"+FLIP+CHAN+".nrrd",
                LABEL:RESPATH+ID+"/S_Labels_"+FLIP+CHAN+".nrrd",
                SKEL:RESPATH+ID+"/skel_"+FLIP+CHAN+".nrrd",
                SKELREP:RESPATH+ID+"/skelRepPruneTubed/prunedSave_"+ID+"_"+FLIP+"_"+CHAN+"_"+LAB+".pkl",
                SCORES:RESPATH+ID+"/Scores_.pkl",
                PROJ:RESPATH+ID+"/Projections/"+ID+"_"+CHAN+"_"+FLIP+"_"+LAB+".png"}

# Helper function to replace generic paths with labels etc.:
def replacer(sIn,thisID,thisChan,thisFlip,thisLab):
    return sIn.replace(ID,thisID).replace(FLIP,thisFlip).replace(CHAN,thisChan).replace(LAB,thisLab)
chanDict = {'R':'Red','G':'Green'}
flipDict = {'F':'Fliped','':'Original'}