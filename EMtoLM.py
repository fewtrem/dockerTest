'''
Created on 11 Nov 2017

@author: fewtrem

# A class to implement the search for EM skeletons....
'''
TITLE = "**TITLE**"
BODY = "**BODY**"
defaultPage = "<HTML><HEAD><TITLE>"+TITLE+"</TITLE></HEAD><BODY>"+BODY+"<BR><BR><BR><BR><P><A HREF=\"http://www.virtualflybrain.org\">VirtualFlyBrain.org</A> Larval Query Script Simple Web Interface</P></BODY></HTML>"

from flask import request,flash
from StringIO import StringIO
import pandas as pd, numpy as np,pickle,os
from EMtoLMsearchLM import getAllForOne
from constants import BRAIN, replacer,chanDict,flipDict
#"/media/s1144899/My Passport/Lineages/30OCt2017MapEMtoLM.pkl"
mapDataPath = "30OCt2017MapEMtoLM.pkl"

with open(mapDataPath) as fI:
    modelsEM2LM = pickle.load(fI)

def getDir(a):
    b = np.matrix(a-np.mean(a,axis=0))
    c = b.transpose()*b
    return np.linalg.svd(c)[0][:,0]

def get150Points(indToKeep,thisSP):
    viewOut = np.zeros((977,801,336),dtype=np.int16)
    width = 10
    thisMax= 1
    stillToDo = indToKeep
    posKeep = []
    # keep adding to the viewOut and the list to keep if away from previous adds (below viewOut threshold)
    # until we have enough:
    while len(posKeep)<150 and len(stillToDo)>0:
        newStillToDo = []
        for iTK in stillToDo:
            pos = thisSP[iTK]
            if viewOut[tuple(pos)]<thisMax:
                viewOut[pos[0]-width:pos[0]+width+1,pos[1]-width:pos[1]+width+1,pos[2]-width:pos[2]+width+1]+=1
                posKeep.append(iTK)
            else:
                newStillToDo.append(iTK)
        stillToDo = newStillToDo
        thisMax+=1
    return posKeep[:150]

def uploadCSV():
    # strings copy in python...:
    thisPage = defaultPage
    thisPage = thisPage.replace(TITLE,"Simple EM CSV Upload")
    bodyHTML = "<font size=5>Upload a CSV file of a Central Brain neuron to search for neurons</font>"
    bodyHTML +="<form action=\"em2lmView\" method=\"post\" enctype=\"multipart/form-data\">"
    bodyHTML += "<input type=\"file\" name=\"fileToUploadVFB\" id=\"fileToUploadVFB\">"
    bodyHTML += "<BR><input type=\"submit\" value=\"Upload CSV\" name=\"submit\">"
    bodyHTML += "</form>"
    thisPage = thisPage.replace(BODY,bodyHTML)
    return thisPage

def viewList(mU150,simList,metaData,pathToScoreFile):
    thisType = BRAIN
    html = ""
    if len(simList)>0:
        html+= "<TABLE><TR><TD>Channel</TD><TD>Flipped Or Not</TD><TD>Matching Score</TD><TD>Alignment Score</TD><TD>Image</TD><TD>GMR</TD></TR>"   
        for j in range(300 if 300<len(simList) else len(simList)):
            jKey = simList[j][0]
            thisScore = simList[j][1]+simList[j][0]
            thisInfo = mU150.infoC[thisType][jKey]
            resPath = replacer(pathToScoreFile,thisInfo[0],"","","")
            thisAlScore = ""
            if os.path.isfile(resPath):
                with open(resPath) as fI:
                    scoreInfo = pickle.load(fI)
                    if int(thisInfo[3]) in scoreInfo[thisInfo[2]]:
                        thisAlScore = '{0:.3f}'.format(scoreInfo[thisInfo[2]][int(thisInfo[3])]['singleScore']) 
            html+="<TR><TD>"+chanDict[thisInfo[2]]+"</TD><TD>"+flipDict[thisInfo[1]]+"</TD><TD>"+str(thisScore)+"</TD><TD>"+str(thisAlScore)+"</TD><TD><IMG src='../getProj?id="+thisInfo[0]+"&chan="+thisInfo[2]+"&flip="+thisInfo[1]+"&lab="+str(thisInfo[3])+"' height='20%'></TD><TD>"+metaData[thisInfo[0]]['fileGMRa']+"</TD></TR>"
        html+="</TABLE>"
    return html

def readCSV(mU150,metaData,pathToScoreFile):
    thisPage = defaultPage
    thisPage = thisPage.replace(TITLE,"Simple EM CSV Processing")
    fI = request.files['fileToUploadVFB']
    skeletons = pd.read_csv(StringIO(fI.read()))
    # map the column names over to remove the white space:
    skeletons.columns = map(lambda x:x.replace(" ",""),skeletons.columns.values)
    neuronIDs = skeletons.skeleton_id.unique()
    divisors = np.array([3.8,3.8,50])
    skelInfo = []
    skelPoints = []
    skelNBlast = []
    sI=0
    #Modify for multi-cell:
    for thisSkelID in [neuronIDs[0]]:
        sI+=1
        # Get the positions:
        thisSel = skeletons[skeletons.skeleton_id==thisSkelID]
        thisName = thisSel.neuron.unique()[0]
        thisPoints = thisSel[['x','y','z']].values
        thisPoints = thisSel[['x','y','z']].values/divisors
        thisSkel = []
        for dd in range(3):
            thisSkel.append(modelsEM2LM[dd].predict(thisPoints))
        thisSkel = np.array(thisSkel).transpose()
        thisSkel = np.array(thisSkel)
        # Do the NBlasting:
        nBlastDir = []
        for i in range(thisSkel.shape[0]):
            diff = np.sum(np.power(np.tile(thisSkel[i],(thisSkel.shape[0],1))-thisSkel,2),axis=1)
            nnI = np.argsort(diff)[:6]
            nBlastDir.append(np.array(getDir(thisSkel[nnI])).reshape((3)))
        nBlastDir = np.array(nBlastDir)
        skelInfo.append(thisName)
        skelPoints.append(np.round(thisSkel).astype(np.int16))
        skelNBlast.append(nBlastDir.astype(np.float32))
    # Reduce them to 150 points:
    xLim = [100,900]
    yLim = [0,450]
    zLim = [90,310]
    lims = [xLim,yLim,zLim]
    # select but 150 points within the appropriate range(!):
    skelPoints150 = []
    skelNBlast150 = []
    for i in range(len(skelInfo)):
        thisPoints = -2**14*np.ones((150,3),dtype=np.int16)
        thisNBlastDir = -2**14*np.ones((150,3),dtype=np.float32)
        selector = np.ones(skelPoints[i].shape[0])
        for pI in range(len(lims)):
            selector = np.logical_and(selector,skelPoints[i][:,pI]>=lims[pI][0])
            selector = np.logical_and(selector,skelPoints[i][:,pI]<=lims[pI][1])
        print np.sum(selector),"points (",skelInfo[i],")"
        indToKeep = np.random.permutation(np.where(selector==True)[0])
        indToKeep = get150Points(indToKeep,skelPoints[i])
        thisPoints[:len(indToKeep)]=skelPoints[i][indToKeep]
        thisNBlastDir[:len(indToKeep)]=skelNBlast[i][indToKeep]
        skelPoints150.append(thisPoints)
        skelNBlast150.append(thisNBlastDir)
    skelPoints150 = np.array(skelPoints150)
    skelNBlast150 = np.array(skelNBlast150)
    # do the search...
    skelPoints150[skelPoints150[:,:,0]==-2**14] = [1000,10000,10000]
    # correct shift:
    skelPoints150[:,:,2] = skelPoints150[:,:,2]-5
    # sort:
    for iKey in range(skelPoints150.shape[0]):
        skelPoints150[iKey] = skelPoints150[iKey][np.argsort(skelPoints150[iKey][:,0])]
        skelNBlast150[iKey] = skelNBlast150[iKey][np.argsort(skelPoints150[iKey][:,0])]
    # Only the first one!
    thisResList = getAllForOne(mU150,skelPoints150[0],skelNBlast150[0])
    np.random.shuffle(thisResList)
    thisResList.sort(key=lambda x:x[1]+x[2],reverse=True)
    html = "Searching for "+skelInfo[0]
    html += viewList(mU150,thisResList,metaData,pathToScoreFile)
    thisPage = thisPage.replace(BODY,html)
    return thisPage