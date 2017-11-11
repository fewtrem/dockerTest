'''
Created on 11 Nov 2017

@author: fewtrem
'''
# let's calculate the mins first!
from constants import BRAIN
import numpy as np,os

import ctypes
curDir = os.path.abspath(os.path.dirname(__file__))
lib = ctypes.cdll.LoadLibrary(os.path.join(curDir,"compareSkeletonPointsC.so"))
getMinDiffCOnlyNNNBlastTube = lib.getMinDiffCOnlyNNNBlast
# get the minimum distance for all points in C1 to those C2 lists:
def cGetMinNBlast(testC1,testC2,xAxis,regionThresh,compDataA,compDataB,compThreshold):
    #Order C2 to search for points
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
    compDataA = np.ascontiguousarray(compDataA.astype(np.float32))
    compDataB = np.ascontiguousarray(compDataB.astype(np.float32))
    sizeOfComp = int(compDataA.shape[1])
    compThreshold = int(compThreshold)
    outputC = np.zeros((testC1.shape[0],2),dtype=np.float32)
    outputC = np.ascontiguousarray(outputC.astype(np.float32))
    # region to look around in X!:
    expThresh=np.intc(regionThresh)
    # xaxis width:
    xAxisc = np.intc(xAxis)
    scoreIfNone = 1000.0
    getMinDiffCOnlyNNNBlastTube(ctypes.c_void_p(testCO.ctypes.data),
             ctypes.c_void_p(testC1.ctypes.data),
             ctypes.c_void_p(testC1Shape.ctypes.data),
             ctypes.c_void_p(compDataA.ctypes.data),
             ctypes.c_void_p(testC2.ctypes.data),
             ctypes.c_void_p(testC2Shape.ctypes.data),
             ctypes.c_void_p(compDataB.ctypes.data),
             ctypes.c_void_p(outputC.ctypes.data),
             ctypes.c_int(sizeOfComp),
             ctypes.c_int(expThresh),
             ctypes.c_int(xAxisc),
             ctypes.c_int(int(compThreshold)),
             ctypes.c_float(scoreIfNone),
             ctypes.c_void_p(np.ascontiguousarray(np.array([1,1,1.707],dtype=np.float32)).ctypes.data))
    return  outputC

def newFunc(xList):
    toRet = (1/(1+np.exp((-30000+xList.astype(np.float32))/5000)))
    toRet[xList>40000]=0
    return toRet

def getAllForOne(mU150,testC1,compDataA):
    cT = 200
    xAxis = 1000
    compThreshold = cT*cT
    thisType = BRAIN
    # reset this value's 1000s to something else so they don't equate!
    testC1[testC1==10000]=30000
    selectorAB = testC1[:,1]!=10000
    thisResList = []
    for jKey in range(mU150.pointsC[thisType].shape[0]):
        if jKey%10000==0:
            print jKey
        #if goodOrNot[jKey]==True:
        if True:
            testC2 = mU150.pointsC[thisType][jKey]
            selectorBA = testC2[:,1]!=10000
            compDataB = mU150.nBlastC[thisType][jKey]
            thisRes = cGetMinNBlast(testC1,testC2,xAxis,cT,compDataA,compDataB,compThreshold)
            compResAB = thisRes[selectorAB]
            thisResInv = cGetMinNBlast(testC2,testC1,xAxis,cT,compDataB,compDataA,compThreshold)
            compResBA = thisResInv[selectorBA]
            thisPredAB = np.sum(newFunc(compResAB[:,0]))
            thisPredBA = np.sum(newFunc(compResBA[:,0]))
            thisResList.append([jKey,thisPredAB,thisPredBA])
    return thisResList