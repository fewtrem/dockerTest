#!flask/bin/python
from flask import Flask
from flask import request,redirect,send_file,abort
import json
from flask_basicauth import BasicAuth
import numpy as np,pickle,os
from smootheComp import smootheComp
from skel150 import matchUp150

# Constants:
from constants import STACKTYPE,ID,CHAN,BRAIN,VNC,FLIP,LAB,replacer,chanDict,flipDict


# App config:
app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = 'vfb'
app.config['BASIC_AUTH_PASSWORD'] = 'toronto'
app.config['BASIC_AUTH_FORCE'] = True
basic_auth = BasicAuth(app)
app.secret_key = 'well it is in github so'

# Directories:
# "/media/s1144899/My Passport/QuickCondense/All_May2017_"
sootheCompDataPath = "/Data/All_May2017_"
# "/media/s1144899/My Passport/QuickCondense/productionised/"
matchUp150Path = "/Data/productionised/"
# "/media/s1144899/My Passport/Results/"
resPath = "/Results/"
pathToScoreFile = resPath+ID+"/Scores_.pkl"
pathToProj = resPath+ID+"/Projections/"+ID+"_"+CHAN+"_"+FLIP+"_"+LAB+".png"
# "/media/s1144899/My Passport/MetaData.pkl"
metaDataPath = "/Data/MetaData.pkl"

# Load the meta data:
with open(metaDataPath) as fI:
    metaData = pickle.load(fI)

# Load the map from stack name to stack ID:
reverseLookUpStacks = {}
for thisKey in metaData:
    thisInfo = metaData[thisKey]
    reverseLookUpStacks[str(os.path.basename(thisInfo['filePath']).split(".")[0])]=thisKey
        
# Load the comparison function:
sC = smootheComp(sootheCompDataPath)
mU150 = matchUp150(matchUp150Path)





# Request Tiff FileName:
# decorate our method index with the route method, param "/":
@app.route('/')
def index():
    html = "<html><head><title>Lookup registration data</title></head><body>"
    html+="Please input a TIFF filename:"
    html+="<form action='.' method='POST'>"
    html+="<input type='text' name='tiffName'>"
    html+="<input type='submit' value='go'>"
    html+="</form><BR><BR>Try the <a href=\"/em2lm\">EM to LM search tool (BETA)</a>"
    html+="</body>"
    return html

# Process Input of Stack to below:
@app.route('/', methods=['POST'])
def formProc():
    text = request.form['tiffName']
    processedText = text.split(".")[0]
    return redirect("/viewTiff/"+processedText)

# Helper function for below:
def getInfo(imgID,tU,tK):
    html= "<TABLE><TR><TH>Filename</TH><TH>GMR Line A</TH><TH>GMR Line B</TH><TH>FolderID</TH><TH>Full path</TH></TR>"
    html+="<TR><TD>"+imgID+"</TD><TD>"+tU['fileGMRa']+"</TD><TD>"+tU['gmrFileb']+" ("+tU['gmrFilebInfo']+")</TD><TD>"+tK+"</TD><TD>"+tU['filePath']+"</TD></TR></TABLE>"
    return html

@app.route('/viewTiff/<imgID>')
def fetchImage(imgID):
    html="<B>View Image From Tiff File</B><BR>"
    # Get the stack ID from input ID:
    if imgID in reverseLookUpStacks:
        stackID = reverseLookUpStacks[imgID]
        mD = metaData[stackID]
        html+=getInfo(imgID,mD,stackID)
        html+="<BR><BR>"
        html+= "<TABLE><TR><TD>Channel</TD><TD>Segment</TD><TD>Score</TD><TD>Image</TD><TD>Look for similarities</TD></TR>"
        # Get score info:
        with open(replacer(pathToScoreFile,stackID,"","","")) as fI:
            scoreInfo = pickle.load(fI)
        # Now show each neuron as a row entry:
        for thisChan in scoreInfo:
            for thisLab in scoreInfo[thisChan]:
                html+="<TR><TD>"+chanDict[thisChan]+"</TD><TD>"+str(thisLab)+"</TD><TD>"+'{0:.3f}'.format(scoreInfo[thisChan][thisLab]['singleScore'])+"</TD><TD><IMG src='../getProj?id="+stackID+"&chan="+thisChan+"&flip=&lab="+str(thisLab)+"' height='20%'></TD><TD><a href='../webFindSim?id="+stackID+"&chan="+thisChan+"&lab="+str(thisLab)+"&flip='>Original</a>  <a href='../webFindSim?id="+stackID+"&chan="+thisChan+"&lab="+str(thisLab)+"&flip=F'>Flip</a></TD></TR>"
        html+="</TABLE>"
    else:
        html+="Not found:<BR>"+imgID
    return html


@app.route('/webFindSim')
def searchSim():
    thisID = request.args.get('id')
    thisChan = request.args.get('chan')
    thisLab = request.args.get('lab')
    thisFlip = request.args.get('flip')
    thisType = sC.getTypeForID(thisID)
    html="<B>Searching for similar cells</B><BR>"
    tU = metaData[thisID]
    html+=getInfo(thisID,tU,thisID)
    html+="<TABLE><TR><TH>Original/Flip:</TH><TH>Channel:</TH><TH>Label:</TH></TH></TR>"
    html+="<TR><TD>"+flipDict[thisFlip]+"</TD><TD>"+chanDict[thisChan]+"</TD><TD>"+thisLab+"</TD></TR></TABLE>"
    if thisType != -1:
        thisOne = {STACKTYPE:thisType,
                   ID:thisID,
                   FLIP:thisFlip,
                   CHAN:thisChan,
                   LAB:thisLab}
        simList = sC.findSimilar(thisOne,0.25,False)
        if len(simList)>0:
            simListRef = mU150.findSimilar(thisOne, simList)
            if simListRef[1] != -1:
                html+= "<TABLE><TR><TD>Channel</TD><TD>Flipped Or Not</TD><TD>Matching Score</TD><TD>Alignment Score</TD><TD>Image</TD><TD>GMR</TD></TR>"
                for i in range(10):
                    thisInfo = simListRef[0][i]
                    fI = open(replacer(pathToScoreFile,thisInfo[0][0],"","",""))
                    scoreInfo = pickle.load(fI)
                    fI.close()
                    html+="<TR><TD>"+chanDict[thisInfo[0][1]]+"</TD><TD>"+flipDict[thisInfo[0][2]]+"</TD><TD>"+str(thisInfo[1])+"</TD><TD>"+'{0:.3f}'.format(scoreInfo[thisInfo[0][1]][int(thisInfo[0][3])]['singleScore'])+"</TD><TD><IMG src='../getProj?id="+thisInfo[0][0]+"&chan="+thisInfo[0][1]+"&flip="+thisInfo[0][2]+"&lab="+str(thisInfo[0][3])+"' height='20%'></TD><TD>"+metaData[thisInfo[0][0]]['fileGMRa']+"</TD></TR>"
                html+="</TABLE>"
            else:
                html+="Search failed due to input data not found in skel150NBlastProc"
        else:
            html+="Search failed due to input data not found in smootheProc"
    else:
        html+="Search failed due to input data not found in smootheProc"
    return html

@app.route('/getProj')
def get_image():
    thisID = request.args.get('id')
    thisChan = request.args.get('chan')
    thisLab = request.args.get('lab')
    thisFlip = request.args.get('flip')
    fileOut = replacer(pathToProj,thisID,thisChan,thisFlip,thisLab)
    return send_file(fileOut, mimetype='image/gif')
    
    
# And also a restful api:
@app.route('/api/findsimilar', methods=['POST'])
def get_tasks():
    if not request.json:
        abort(400)
    for thisCheck in ['stackID','channel','cellID']:
        if not thisCheck in request.json:
            return json.dumps({'success':False,
                        'error':'missing info - need stackID, channel and cellID fields (flip optional)'})
    if not 'flip' in request.json:
        request.json['flip'] = ''
    thisType = sC.getTypeForID(request.json['stackID'])
    if thisType != -1:
        thisOne = {STACKTYPE:thisType,
                   ID:request.json['stackID'],
                   FLIP:request.json['flip'],
                   CHAN:request.json['channel'],
                   LAB:request.json['cellID']}
        simList = sC.findSimilar(thisOne,0.25,False)
        if len(simList)>0:
            simListRef = mU150.findSimilar(thisOne, simList)
            if simListRef[1] != -1:
                limitRet = len(simListRef[0])
                if 'limit' in request.json:
                    limitRet = int(request.json['limit'])
                # Sorting type:
                sortIndex = 3
                if 'sortMethod' in request.json:
                    if request.json['sortMethod'] == 'RPAB':
                        sortIndex = 2
                    elif request.json['sortMethod'] == 'RPABBA':
                        sortIndex = 4
                    elif request.json['sortMethod'] == 'NBlastABBA':
                        sortIndex = 5
                    elif request.json['sortMethod'] == 'sCAB':
                        sortIndex = 1
                if sortIndex == 3:
                    request.json['sortMethod'] = 'NBlastAB'
                simListRef[0].sort(key=lambda x:x[sortIndex],reverse=True)
                simListOut = simListRef[0][:limitRet]
                for thisEntry in simListOut:
                    thisEntry[0] = list(thisEntry[0])
                    for i in range(1,6):
                        thisEntry[i] = float(thisEntry[i])
                return json.dumps({'success':True,
                                'inSCnotinNBlast':int(simListRef[1]),
                                'similarList':simListOut,
                                'sortMethod':request.json['sortMethod'],
                                'colNames':['ID','sCAB','RPAB','NBlastAB','RPABBA','NBlastABBA']})
            else:
                return json.dumps({'success':False,
                                'error':'Could not find stack in NBlast'})
        else:
            return json.dumps({'success':False,
                            'error':'Could not find stack in sC'})
    else:
        return json.dumps({'success':False,
                        'error':'Could not find stack'})
        
# Add a CSV uploader:        
from EMtoLM import uploadCSV
@app.route('/em2lm')
def uploadCSVAdd():
    print "EM2LM loading"
    return uploadCSV()

# Add a CSV viewer:
from EMtoLM import readCSV
@app.route('/em2lmView',methods=['POST'])
def readCSVAdd():
    return readCSV(mU150,metaData,pathToScoreFile)

if __name__ == '__main__':
#    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=True,host='0.0.0.0', port=80)