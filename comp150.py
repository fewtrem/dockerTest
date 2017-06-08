'''
Created on 8 Jun 2017

@author: s1144899
'''
import ctypes,numpy as np,nrrd2,pickle
lib = ctypes.cdll.LoadLibrary("/app/compareSkeletonPoints.so")



def getRevLookUp(infoList):
    reverseLookUp = {}
    for i in range(len(infoList)):
        thisEntry = infoList[i]
        if thisEntry[0] not in reverseLookUp:
            reverseLookUp[thisEntry[0]]={'R':{'':{},'F':{}},
                                         'G':{'':{},'F':{}}}
        reverseLookUp[thisEntry[0]][thisEntry[1]][thisEntry[2]][thisEntry[3]]=i
    return reverseLookUp


# get the minimum distance between points in C1 and C2:
def cGetMin(testC1,testC2,xAxis):
    cGetMinDiffB = lib.getMinDiffB
    #Order
    cGetOrderIndecies = lib.getOrderIndecies
    testB = np.ascontiguousarray(testC2.astype(np.intc))
    testBShape = np.array(testB.shape).astype(np.intc)
    outputB = np.zeros((xAxis+1))
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
    outputC = np.zeros((testC1.shape[0]))
    outputC = np.ascontiguousarray(outputC.astype(np.intc))
    # region to look around (Not thresh, must be equal to it!):
    expThresh=np.intc(30)
    xAxisc = np.intc(xAxis)
    cGetMinDiffB(ctypes.c_void_p(testCO.ctypes.data),
             ctypes.c_void_p(testC1.ctypes.data),
             ctypes.c_void_p(testC1Shape.ctypes.data),
             ctypes.c_void_p(testC2.ctypes.data),
             ctypes.c_void_p(testC2Shape.ctypes.data),
             ctypes.c_void_p(outputC.ctypes.data),
             ctypes.c_int(expThresh),
             ctypes.c_int(xAxisc))
    return  outputC

def preLoad():
    infoCond = nrrd2.read("/media/s1144899/My Passport/CondensedLabels/condensedLabels150_All.nrrd")[0]
    fI = open("/media/s1144899/My Passport/CondensedLabels/condensedLabels_All.pkl")
    infoList = pickle.load(fI)
    fI.close()
    # fill in missing data with value in range:
    infoCond[infoCond==-2**14] = 1000
    # sort data by x value for C min function
    for i in range(infoCond.shape[0]):
        dA1Sort = np.argsort(infoCond[i,:,0])
        infoCond[i] = infoCond[i,dA1Sort]
    revLookUp = getRevLookUp(infoList)
    return infoList,infoCond,revLookUp

def getResults(threshLab,infoCond,ofInterest):
    # axis width for X:
    xAxis = 1000
    # results array will be extended:
    #resultsArray = np.zeros((infoCond.shape[0],infoCond.shape[0],1),dtype=np.uint8)
    resultsArray = np.zeros(infoCond.shape[0],dtype=np.float32)
    # go through the data:
    # LABEL
    testC1 = np.copy(infoCond[ofInterest])
    # reset this value's 1000s to something else so they don't equate!
    testC1[testC1==1000]=30000
    # get the valid selector: 
    validCondSelector = infoCond[ofInterest,:,0]<1000
    divisor = np.sum(validCondSelector)+0.00001
    for j in range(infoCond.shape[0]):
        # compare to SKELs:
        testC2 = infoCond[j]
        thisLocRes = cGetMin(testC1,testC2,xAxis)
        # select from the local results:
        condResSel = thisLocRes[validCondSelector]
        # get the threshold 
        condRes = np.sum(condResSel<threshLab)/divisor
        # only look at lab ones that have values!: (should not be necessary as should always have enough...)
        resultsArray[j] = condRes
    return resultsArray
