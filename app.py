#!flask/bin/python
from flask import Flask
from flask import request
from flask import redirect
from flask import send_file
import numpy as np,sys
import comp150 as comp150
ID = "**ID**"
FLIP = "**F**"
CHAN = "**S**"
LAB = "**LAB**"
chanDict = {'R':'Red','G':'Green'}
flipDict = {'F':'Fliped','':'Original'}
app = Flask(__name__)
resPath = "/media/s1144899/My Passport/Results/"
pathToScoreFile = resPath+ID+"/Scores_.pkl"
pathToProj = resPath+ID+"/Projections/"+ID+"_"+CHAN+"_"+FLIP+"_"+LAB+".png"
def replacer(sIn,thisID,thisChan,thisFlip,thisLab):
    return sIn.replace(ID,thisID).replace(FLIP,thisFlip).replace(CHAN,thisChan).replace(LAB,thisLab)
import pickle,os
fI=open("/media/s1144899/My Passport/MetaData.pkl")
infoData = pickle.load(fI)
fI.close()
reverseLookUp = {}
for thisKey in infoData:
    thisInfo = infoData[thisKey]
    reverseLookUp[str(os.path.basename(thisInfo['filePath']).split(".")[0])]=thisKey
infoList,infoCond,revLookUp = comp150.preLoad()


# decorate our method index with the route method, param "/":
@app.route('/')
def index():
    html = "<html><head><title>Lookup registration data</title></head><body>"
    html+="Please input a TIFF filename:"
    html+="<form action='.' method='POST'>"
    html+="<input type='text' name='tiffName'>"
    html+="<input type='submit' value='go'>"
    html+="</form>"
    html+="</body>"
    return html
@app.route('/', methods=['POST'])
def formProc():
    text = request.form['tiffName']
    processedText = text.split(".")[0]
    return redirect("/viewTiff/"+processedText)


@app.route('/searchSim')
def searchSim():
    thisID = request.args.get('id')
    thisChan = request.args.get('chan')
    thisLab = request.args.get('lab')
    thisFlip = request.args.get('flip')
    html="<B>Searching for similar cells</B><BR>"
    tU = infoData[thisID]
    html+=getInfo(thisID,tU,thisID)
    html+="<TABLE><TR><TH>Original/Flip:</TH><TH>Channel:</TH><TH>Label:</TH></TH></TR>"
    html+="<TR><TD>"+flipDict[thisFlip]+"</TD><TD>"+chanDict[thisChan]+"</TD><TD>"+thisLab+"</TD></TR></TABLE>"
    # get the ID:
    thisMatID = -1
    if thisID in revLookUp:
        if thisChan in revLookUp[thisID]:
            if thisFlip in revLookUp[thisID][thisChan]:
                if int(thisLab) in revLookUp[thisID][thisChan][thisFlip]:
                    thisMatID = revLookUp[thisID][thisChan][thisFlip][int(thisLab)]
    # Do the search:
    if thisMatID != -1:
        resArray = comp150.getResults(900,infoCond,thisMatID)
	orderedArr = np.argsort(resArray)[::-1]
	html+= "<TABLE><TR><TD>Channel</TD><TD>Flipped Or Not</TD><TD>Matching Score</TD><TD>Alignment Score</TD><TD>Image</TD></TR>"
	for i in range(10):
            thisInfo = infoList[orderedArr[i]]
	    fI = open(replacer(pathToScoreFile,thisInfo[0],"","",""))
	    scoreInfo = pickle.load(fI)
	    fI.close()
	    html+="<TR><TD>"+chanDict[thisInfo[1]]+"</TD><TD>"+flipDict[thisInfo[2]]+"</TD><TD>"+str(resArray[orderedArr[i]])+"</TD><TD>"+'{0:.3f}'.format(scoreInfo[thisInfo[1]][thisInfo[3]]['singleScore'])+"</TD><TD><IMG src='../getProj?id="+thisInfo[0]+"&chan="+thisInfo[1]+"&flip="+thisInfo[2]+"&lab="+str(thisInfo[3])+"' height='20%'></TD></TR>"
	html+="</TABLE>"
    else:
        html+="No results found!"

    
    return html

def getInfo(imgID,tU,tK):
    html= "<TABLE><TR><TH>Filename</TH><TH>GMR Line A</TH><TH>GMR Line B</TH><TH>FolderID</TH><TH>Full path</TH></TR>"
    html+="<TR><TD>"+imgID+"</TD><TD>"+tU['fileGMRa']+"</TD><TD>"+tU['gmrFileb']+" ("+tU['gmrFilebInfo']+")</TD><TD>"+tK+"</TD><TD>"+tU['filePath']+"</TD></TR></TABLE>"
    return html

@app.route('/viewTiff/<imgID>')
def fetchImage(imgID):
    html="<B>View Image From Tiff File</B><BR>"
    if imgID in reverseLookUp:
        tK = reverseLookUp[imgID]
        tU = infoData[tK]
        html+=getInfo(imgID,tU,tK)
	html+="<BR><BR>"
	html+= "<TABLE><TR><TD>Channel</TD><TD>Segment</TD><TD>Score</TD><TD>Image</TD><TD>Look for similarities</TD></TR>"
	fI = open(replacer(pathToScoreFile,tK,"","",""))
	scoreInfo = pickle.load(fI)
	fI.close()
	for thisChan in scoreInfo:
	    for thisLab in scoreInfo[thisChan]:
		html+="<TR><TD>"+chanDict[thisChan]+"</TD><TD>"+str(thisLab)+"</TD><TD>"+'{0:.3f}'.format(scoreInfo[thisChan][thisLab]['singleScore'])+"</TD><TD><IMG src='../getProj?id="+tK+"&chan="+thisChan+"&flip=&lab="+str(thisLab)+"' height='20%'></TD><TD><a href='../searchSim?id="+tK+"&chan="+thisChan+"&lab="+str(thisLab)+"&flip='>Original</a>  <a href='../searchSim?id="+tK+"&chan="+thisChan+"&lab="+str(thisLab)+"&flip=F'>Flip</a></TD></TR>"
	html+="</TABLE>"
    else:
        html+="Not found:<BR>"+imgID
    return html
@app.route('/getProj')
def get_image():
    thisID = request.args.get('id')
    thisChan = request.args.get('chan')
    thisLab = request.args.get('lab')
    thisFlip = request.args.get('flip')
    fileOut = replacer(pathToProj,thisID,thisChan,thisFlip,thisLab)
    return send_file(fileOut, mimetype='image/gif')
if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=80)
