'''
Created on 16 Oct 2017

@author: s1144899
'''
import nrrd2,pickle,numpy as np


from constants import STACKTYPE,ID,CHAN,BRAIN,VNC,FLIP,LAB
class smootheComp:
    # generate a reverseLookUp Dictionary:
    def revLookUp(self,listIn,thisType):
        # let's just look into the folders as the ground truth for now:
        reverseLookUp = {}
        for i in range(len(listIn)):
            thisEntry = listIn[i]
            if thisEntry[0] not in reverseLookUp:
                reverseLookUp[thisEntry[0]]={'R':{'':{},'F':{}},
                                             'G':{'':{},'F':{}}}
            reverseLookUp[thisEntry[0]][thisEntry[1]][thisEntry[2]][thisEntry[3]]=i
            # store dict-Type dictionary:
            self.typeDict[thisEntry[0]] = thisType
        return reverseLookUp
    
    def __init__(self,locOfInput):
        self.storage = {VNC:None,BRAIN:None}
        self.lists = {}
        self.revLU = {}
        self.iSums = {}
        self.typeDict = {}
        for thisType in self.storage:
            self.storage[thisType] = nrrd2.read(locOfInput+thisType.replace("*","")+".nrrd")[0]
            fI = open(locOfInput+thisType.replace("*","")+".pkl")
            self.lists[thisType] = pickle.load(fI)
            fI.close()
            self.revLU[thisType] = self.revLookUp(self.lists[thisType],thisType)
            self.lists[thisType] = np.array(self.lists[thisType])

    def getTypeForID(self,thisID):
        if thisID in self.typeDict:
            return self.typeDict[thisID]
        else:
            return -1;
    def doRevLU(self,iI):
        try:
            revID = self.revLU[iI[STACKTYPE]][iI[ID]][iI[CHAN]][iI[FLIP]][iI[LAB]]
        except:
            revID = -1
        return revID
    
    def findSimilar(self,iI,returnThreshold,findReverse):
        returnList= []
        # find the key:
        iKey = self.doRevLU(iI)
        if iKey >=0:
            # only those voxels with signal:
            iSelector = self.storage[iI[STACKTYPE]][iKey]==3
            # just look at the ones the signal (normalisation):
            ithsum = np.sum(iSelector)*1.0
            if ithsum==0:
                ithsum = 1.0
            # batch sizes:
            selF = 1000
            iSelectorM = np.tile(iSelector,(selF,1))
            for j in range(0,self.storage[iI[STACKTYPE]].shape[0],selF):
                jselector = self.storage[iI[STACKTYPE]][j:j+selF,:]==3
                ijSelector = np.logical_and(jselector,iSelectorM[:jselector.shape[0]])
                thisPropRes = np.sum(ijSelector,axis=1)/ithsum
                if findReverse == True:
                    jthsum = np.sum(jselector,axis=1)*1.0
                    jthsum[jthsum==0]=1.0
                    thisPropRes = np.sum(ijSelector,axis=1)/jthsum*thisPropRes
                retSel = thisPropRes>returnThreshold
                thisPropRes = thisPropRes[retSel]
                infoRes = self.lists[iI[STACKTYPE]][j:j+selF][retSel]
                returnList+=zip(thisPropRes,infoRes)
            # sort the return list by the score:
            returnList.sort(key=lambda x:x[0],reverse=True)
        return returnList