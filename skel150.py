'''
Created on 16 Oct 2017

@author: s1144899
'''
from constants import STACKTYPE,ID,CHAN,BRAIN,VNC,FLIP,LAB
import pickle,nrrd2,numpy as np,ctypes,os
curDir = os.path.abspath(os.path.dirname(__file__))
# See "/afs/inf.ed.ac.uk/user/s11/s1144899/PhD/Python Projects/ml2017/compaingResults/CFunc" for c code:
lib = ctypes.cdll.LoadLibrary(os.path.join(curDir,"compareSkeletonPointsProd.so"))
getNBlastScore = lib.getNBlastScoreProd
# get the minimum distance for all points in C1 to those C2 lists:
def cGetNBlastScore(testC1,testC2,compDataA,compDataB):
    #Order C2 to search for points
    cGetOrderIndecies = lib.getOrderIndecies
    testB = np.ascontiguousarray(testC2.astype(np.intc))
    testBShape = np.array(testB.shape).astype(np.intc)
    outputB = np.zeros((1000+1))
    outputB = np.ascontiguousarray(outputB.astype(np.intc))
    outputBShape = np.array(outputB.shape).astype(np.intc)
    cGetOrderIndecies(ctypes.c_void_p(testB.ctypes.data),
             ctypes.c_void_p(testBShape.ctypes.data),
             ctypes.c_void_p(outputB.ctypes.data),
             ctypes.c_void_p(outputBShape.ctypes.data))
    #Next
    testCO = outputB
    testCO = np.ascontiguousarray(testCO.astype(np.intc))
    testC1 = np.ascontiguousarray(testC1.astype(np.intc))
    testC1Shape = np.array(testC1.shape).astype(np.intc)
    testC2 = np.ascontiguousarray(testC2.astype(np.intc))
    testC2Shape = np.array(testC2.shape).astype(np.intc)
    compDataA = np.ascontiguousarray(compDataA.astype(np.float32))
    compDataB = np.ascontiguousarray(compDataB.astype(np.float32))
    outputC = np.zeros((testC1.shape[0],4),dtype=np.float32)
    outputC = np.ascontiguousarray(outputC.astype(np.float32))
    getNBlastScore(ctypes.c_void_p(testCO.ctypes.data),
             ctypes.c_void_p(testC1.ctypes.data),
             ctypes.c_void_p(testC1Shape.ctypes.data),
             ctypes.c_void_p(compDataA.ctypes.data),
             ctypes.c_void_p(testC2.ctypes.data),
             ctypes.c_void_p(testC2Shape.ctypes.data),
             ctypes.c_void_p(compDataB.ctypes.data),
             ctypes.c_void_p(outputC.ctypes.data))
    # Return is DistanceSquared,Dot Product,PositionSquared BLAST Result, NBlast Result.
    return  outputC

class matchUp150:
    def __init__(self,inputLocPre):
        # Load in data:
        self.inputLocPre = inputLocPre
        self.infoC = {}
        self.pointsC = {}
        self.nBlastC = {}
        self.maxNo = {}
        for thisType in [BRAIN,VNC]:
            with open(self.inputLocPre+"Prod_NBlast_"+thisType.replace("*","")+"_Info.pkl") as fI:
                self.infoC[thisType] = pickle.load(fI)
            self.pointsC[thisType] = nrrd2.read(self.inputLocPre+"Prod_NBlast_"+thisType.replace("*","")+"_Loc.pkl")[0]
            self.nBlastC[thisType] = nrrd2.read(self.inputLocPre+"Prod_NBlast_"+thisType.replace("*","")+"_NBlast.pkl")[0]
            self.maxNo[thisType] = np.sum(self.pointsC[thisType][:,:,1]<10000,axis=1)
        # create the reverse look-up
        self.reverseLU = {BRAIN:{},VNC:{}}
        for thisType in [BRAIN,VNC]:
            for i in range(len(self.infoC[thisType])):
                thisEntry = self.infoC[thisType][i]
                if thisEntry[0] not in self.reverseLU[thisType]:
                    self.reverseLU[thisType][thisEntry[0]]={'R':{'':{},'F':{}},
                                                 'G':{'':{},'F':{}}}
                self.reverseLU[thisType][thisEntry[0]][thisEntry[2]][thisEntry[1]][str(thisEntry[3])]=i

    def doRevLU(self,iI,thisType):
        try:
            if isinstance(iI,dict):
                revID = self.reverseLU[thisType][iI[ID]][iI[CHAN]][iI[FLIP]][iI[LAB]]
            else:
                revID = self.reverseLU[thisType][iI[0]][iI[1]][iI[2]][str(iI[3])]
        except:
            revID = -1
        return revID
    def findSimilar(self,thisOne,simList):
        thisType = thisOne[STACKTYPE]
        iKey = self.doRevLU(thisOne,thisType)
        resultsList = []
        skipped = 0
        if iKey>=0:
            testC1 = np.copy(self.pointsC[thisType][iKey])
            compDataA = self.nBlastC[thisType][iKey]
            # reset this value's 1000s to something else so they don't equate!
            testC1[testC1==10000]=30000
            for j in range(len(simList)):
                jI = simList[j][1]
                jKey = self.doRevLU(jI,thisType)
                if jKey>=0:
                    if self.maxNo[thisType][iKey]>0 and self.maxNo[thisType][jKey]>0:
                        testC2 = self.pointsC[thisType][jKey]
                        compDataB = self.nBlastC[thisType][jKey]
                        compResAB = np.sum(cGetNBlastScore(testC1,testC2,compDataA,compDataB)[:self.maxNo[thisType][iKey],2:4],axis=0)
                        compResBA = np.sum(cGetNBlastScore(testC2,testC1,compDataB,compDataA)[:self.maxNo[thisType][jKey],2:4],axis=0)
                        resultsList.append([simList[j][1],simList[j][0],compResAB[0],compResAB[1],compResBA[0],compResBA[1]])
                else:
                    skipped+=1
        else:
            skipped=-1
        return resultsList,skipped