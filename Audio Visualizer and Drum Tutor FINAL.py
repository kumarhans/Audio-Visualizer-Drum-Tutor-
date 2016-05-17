from Tkinter import *
import numpy
import pyaudio
import wave
from pydub import AudioSegment
import pydub
from scipy.io.wavfile import write
import time
from array import array
from struct import pack
import threading
import math
import string



######### Classes being Defined ########

class rudiment(object):     #initializes a rudiment
    def __init__(self, name,beatDictionary,initialBPM,tip):
        self.name = name
        self.beatDictionary = beatDictionary
        self.selected = False
        self.initialBPM = initialBPM
        self.tip = tip

#all thread functions allow for play/record
class recordThread (threading.Thread):
    def __init__(self, data):
        threading.Thread.__init__(self)
        self.data = data
    def run(self):
        record(self.data)

class moveNotesThread(threading.Thread):
    def __init__(self, data):
        threading.Thread.__init__(self)
        self.data = data

    def run(self):
        changeColors(self.data)

class playNotesThread(threading.Thread):
    def __init__(self, data):
        threading.Thread.__init__(self)
        self.data = data
    def run(self):
        playNotes(self.data)

class playMusicThread (threading.Thread):
    def __init__(self, data):
        threading.Thread.__init__(self)
        self.data = data
        self.songList = self.data.songList
    def run(self):
        playMusic(self.data, self.songList[self.data.songNumber])

class metranomeThread(threading.Thread):
    def __init__(self, data):
        threading.Thread.__init__(self)
        self.data = data
    def run(self):
        changeMetranome(self.data)

class beatDetectionclass(threading.Thread):
    def __init__(self, data):
        threading.Thread.__init__(self)
        self.data = data
    def run(self):
        beatDetection(self.data)

class progressclass(threading.Thread):
    def __init__(self, data):
        threading.Thread.__init__(self)
        self.data = data
    def run(self):
        ProgressTrack(self.data)

class clicksclass(threading.Thread):
    def __init__(self, data):
        threading.Thread.__init__(self)
        self.data = data
    def run(self):
        recordclicks(self.data)

######### Classes being Defined ########





####### Non Data Functions Used Throughout #####


#speed function adapted from Course notes
#https://www.cs.cmu.edu/~112/notes/notes-graphics.html
def rgbString(red, green, blue):    #creats color string to be read
    return "#%02x%02x%02x" % (red, green, blue)

#adapted from pyAudio website
#https://people.csail.mit.edu/hubert/pyaudio/
def exportToFile(sound, file):  #exports sound
    sound.export(file, format="wav")
    return file


#speed function adapted from
#http://zulko.github.io/blog/2014/03/29/soundstretching-and-pitch-shifting-
# in-python/
def speedx(sound_array, factor):
    """ Multiplies the sound's speed by some `factor` """
    indices = numpy.round( numpy.arange(0, len(sound_array), factor) )
    indices = indices[indices < len(sound_array)].astype(int)
    return sound_array[ indices.astype(int) ]

#speed function adapted from Course notes
#https://www.cs.cmu.edu/~112/notes/notes-data-and-exprs.html#FloatingPointApprox
def almostEqual(d1, d2):
    epsilon = .0000001
    return (abs(d2 - d1) < epsilon)


#speed function adapted from Course notes
#https://www.cs.cmu.edu/~112/notes/notes-graphics.html
def make2DList(value,n):
    list = []
    for row in range(n):
        row = []
        for col in range(n):
            row += [value]
        list += [row]
    return list

def speedUpFile(file,factor,destinationFile):#speeds up a file by certain factor
    sound = pydub.AudioSegment.from_wav(file)
    data = sound.raw_data
    data = numpy.fromstring(data, numpy.int16)
    data = speedx(data,factor)
    write(destinationFile, 44100, data)

def listToBeats(peaklist):  #takes 16 index list and makes beatdictionary
    beatDictionary = dict()
    count = 0
    for value in range(len(peaklist)):
        if peaklist[value] != 0:
            count += 1
            duration = quantize(value,peaklist)
            sticking = ["RL","R","L"][peaklist[value]]
            beatDictionary[count] = ("regular stroke", duration, sticking, 0, 1)
    return beatDictionary

def quantize(index, list):  #finds duration between beats on list
    if index % 2 == 1 or list[index+1] != 0 or len(list) - index == 1:
        return "sixteenth"
    elif (len(list)>index + 2 and  list[index + 2] != 0) or \
            (len(list) - index == 2):
        return "eighth"
    elif len(list)>index + 4 and list[index + 4] != 0 or \
            (len(list) - index == 4):
        return "quarter"


def listIntoPeaks(list, localRange,noteAmp):    #finds local maxes in amplitude
    listofPeaks = [0]* len(list)
    threshold = 10000
    for value in range(1,len(list)-2):
        print max(list[value-localRange:value])
        if list[value][0] > (max(list[value-localRange:value]))[0] and\
                (list[value][0] > (max(list[value+1:value+localRange + 1]))[0]):
            listofPeaks[value] = list[value]
    for value in listofPeaks:
        if type(value) != int and value[0] > threshold: #eliminates noise
            break
        else:
            add = listofPeaks[0]
            listofPeaks = listofPeaks[1:] + [add]
            print 1
    return listInto16(listofPeaks,noteAmp)


def listInto16(list1,noteAmp):  #takes big list and makes it into 16 index list
    newList = [0]*16
    pitch = 400
    for value in range(len(list1)):
        if type(list1[value]) != int and list1[value][0] > noteAmp:
            distance = (value / float(len(list1)))
            newDistance = int(round(distance*16))
            if newDistance<len(newList):    #left or right hand
                if list1[value][1] < pitch:
                    newList[newDistance] = 1
                else:
                    newList[newDistance] = 2
    return newList

def listIntoPeaksSimple(list, localRange):  #simply used to count notes
    listofPeaks = []                        #no frequency recoginition
    for value in range(1, len(list) - 2):
        if list[value] > max(list[value - localRange:value]) and \
                (list[value] > max(
                list[value + 1:value + localRange + 1])):
            listofPeaks += [list[value]]
    return listofPeaks


####### Non Data Functions Used Throughout #####






####### Recording and Playing Functions #######

# record and play function were modified
# from https://people.csail.mit.edu/hubert/pyaudio/
def record(data): #takes in live audio and filters out low amplitudes
    CHUNK = 1024            #sends data to be drawn in visualization
    WIDTH = 2
    CHANNELS = 2
    RATE = 44100
    RECORD_SECONDS = 10000

    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(WIDTH),
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    output=True,
                    frames_per_buffer=CHUNK)

    print("* recording")
    #
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data1 = stream.read(CHUNK)
        threshhold = 20
        data.amplitudeList = numpy.fromstring(data1, numpy.int16)
        averageAmplitude = abs(numpy.average(data.amplitudeList))
        data.frequencyList = (numpy.fft.fft(data.amplitudeList))**2
        if data.mode != "audioVisualizer" or (data.mode == "audioVisualizer" and
                            (data.playingMusic == False)):
            if averageAmplitude > threshhold:
                data.amplitude = averageAmplitude
    print("* done")

    stream.stop_stream()
    stream.close()

    p.terminate()


def recordclicks(data):
    CHUNK = 1024
    WIDTH = 2
    CHANNELS = 2
    RATE = 44100
    RECORD_SECONDS = 10000

    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(WIDTH),
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    output=True,
                    frames_per_buffer=CHUNK)

    print("* recording")
    start = 0
    count = 0

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data1 = stream.read(CHUNK)
        amplitudeList = numpy.fromstring(data1, numpy.int16)
        fourier = numpy.abs(numpy.fft.fft(amplitudeList))
        frequency = (numpy.fft.fftfreq(len(fourier)))
        maxAmplitude = numpy.amax(amplitudeList)
        maxfourier = numpy.argmax(fourier)
        maxFrequency = frequency[maxfourier]
        maxFrequency = abs(maxFrequency * 44100)
        currentTime = time.time()
        interval = .75
        threshhold = 22500
        #this code changes the buttons selcted and also selects them
        if abs((currentTime - start)) > interval and count > 0 \
                and data.playingMusic == False:
            if (data.mode == "audioVisualizer") or (data.mode== "rudimentList")\
                or (data.mode == "drumTutor") or (data.mode == "addRudiments"):
                if count == 1:
                    if data.mode == "audioVisualizer":
                        data.homeButtons += 1
                        if data.homeButtons == 3:
                            data.homeButtons = 0
                    elif data.mode == "rudimentList":
                        data.selectedIndex += 1
                        if data.selectedIndex >= len(data.rudimentList):
                            data.selectedIndex = 0
                    elif data.mode == "addRudiments":
                        data.contributeButtons += 1
                        if data.contributeButtons == 2:
                            data.contributeButtons = 0
                elif count == 2:
                    if data.mode == "audioVisualizer":
                        if data.homeButtons == 0:
                            data.mode = "addRudiments"
                            data.currentBeatDictionary = None
                        elif data.homeButtons == 1:
                            data.mode = "rudimentList"
                        else:
                            thread2 = playMusicThread(data)
                            thread2.start()
                            data.songList = thread2.songList
                    elif data.mode == "rudimentList":
                        data.mode = "drumTutor"
                        data.currentBeatDictionary = \
                        ((data.rudimentList)[data.selectedIndex]).beatDictionary
                        data.currentRudimentName =\
                        ((data.rudimentList)[data.selectedIndex]).name
                        data.tip =((data.rudimentList)[data.selectedIndex]).tip
                        data.bpm =\
                            ((data.rudimentList)[data.selectedIndex]).initialBPM
                        data.noteAccuracy = ""
                    elif data.mode == "drumTutor":
                        thread1 = moveNotesThread(data)
                        thread1.start()
                        thread2 = playNotesThread(data)
                        thread2.start()
                        thread3 = metranomeThread(data)
                        thread3.start()
                        thread4 = progressclass(data)
                        thread4.start()
                    elif data.mode == "addRudiments":
                        if data.contributeButtons == 0:
                            data.mode = "saveScreen"
                        elif data.contributeButtons == 1:
                            data.bpm = 80                   #default BPM
                            thread5 = playNotesThread(data)
                            thread5.start()
                            thread4 = metranomeThread(data)
                            thread4.start()
                            thread6 = beatDetectionclass(data)
                            thread6.start()
            if count > 2 and data.mode != "audioVisualizer":
                data.mode = "audioVisualizer"   #back to home screen
            count = 0
            start = 0
        if maxAmplitude > threshhold and data.playingMusic == False:
            maxFrequency = frequency[maxfourier]
            maxFrequency = abs(maxFrequency * 44100)  #conversion to Hz
            pitch = 1200
            if maxFrequency > pitch:
                count += 1
                if count == 1:
                    start = time.time()

    print("* done")

    stream.stop_stream()
    stream.close()

    p.terminate()

def beatDetection(data):
    CHUNK = 1024
    WIDTH = 2
    CHANNELS = 2
    RATE = 44100
    beatTime = 1 / float(data.bpm) * 60     #conversions to beats
    RECORD_SECONDS = beatTime * 4

    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(WIDTH),
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    output=True,
                    frames_per_buffer=CHUNK)

    print("* recording")
    notes = 0
    totalAmplitude = 0      #filters background noise
    data.playingMusic = True
    for i in range(0, int(RATE / CHUNK * (RECORD_SECONDS))):
        data1 = stream.read(CHUNK)
        data.recordingInstruction = \
            "Listening to Background Noise... Be Quiet if Possible"
        amplitudeList = numpy.absolute(numpy.fromstring(data1, numpy.int16))
        averageAmplitude = numpy.average(amplitudeList)
        totalAmplitude += averageAmplitude

    backgroundAMP = \
        float(totalAmplitude) / float(RATE / CHUNK * (RECORD_SECONDS))

    print "calibrating play one note"

    AVamplitudeList = []    #calibrates to user note
    for i in range(0, int(RATE / CHUNK * (RECORD_SECONDS))):
        data.recordingInstruction = "Calibrating, Play One Note"
        data1 = stream.read(CHUNK)
        amplitudeList = numpy.absolute(numpy.fromstring(data1, numpy.int16))
        maxAmplitude = numpy.amax(amplitudeList)
        AVamplitudeList += [maxAmplitude]

    noteAMP = max(AVamplitudeList) - backgroundAMP


    ampRange = (noteAMP - 15000)
    maxAmplitudeList = []
    print("play now")       #reads what is actually being played
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data.recordingInstruction = "Recording, Play Now"
        data1 = stream.read(CHUNK)
        amplitudeList = numpy.fromstring(data1, numpy.int16)
        fourier = numpy.abs(numpy.fft.fft(amplitudeList))
        frequency = (numpy.fft.fftfreq(len(fourier)))
        maxAmplitude = numpy.amax(amplitudeList)
        maxfourier = numpy.argmax(fourier)
        maxFrequency = frequency[maxfourier]
        maxFrequency = abs(maxFrequency * 44100)
        amplitudeList = numpy.absolute(numpy.fromstring(data1, numpy.int16))
        averageAmplitude = numpy.average(amplitudeList) - backgroundAMP
        maxAmplitude = numpy.amax(amplitudeList)
        maxAmplitudeList += [(maxAmplitude, maxFrequency)]


    data.recordingInstruction = "Press the Record Button To Begin"


    peaklist = listIntoPeaks(maxAmplitudeList, 1, ampRange)
    for value in range(len(peaklist)):
        if peaklist[value] < 1:
            peaklist[value] = 0 #finds peaks

    print("* done")
    data.currentBeatDictionary = listToBeats(peaklist) #converts to drum beat
    data.playingMusic = False
    stream.stop_stream()
    stream.close()

    p.terminate()

def saveToLibrary(data, rudimentName, currentBeatDictionary):
    for letter in data.startingBPM:     #adds rudiment to library
        if letter in string.ascii_letters:
            data.startingBPM = 180
    data.rudimentList += [rudiment(rudimentName,
                currentBeatDictionary, int(data.startingBPM), data.musicTip)]
    data.saveName = "name"
    data.musicTip = "write a tip about this rudiment"
    data.startingBPM = "starting tempo"


#play Music adapted from https://people.csail.mit.edu/hubert/pyaudio/
def playMusic(data,file):
    if file != "None":
        threshhold = 20
        CHUNK = 1024        #plays msuic file

        wf = wave.open(file, 'rb')

        p = pyaudio.PyAudio()

        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        data1 = wf.readframes(CHUNK)

        while (data1 != '') \
                and ((((data.mode == "audioVisualizer") and
                           (file == data.songList[data.songNumber])))
                     or (file not in data.songList)):
            data.playingMusic = True
            stream.write(data1)
            data1 = wf.readframes(CHUNK)
            data.amplitudeList = numpy.fromstring(data1, numpy.int16)
            averageAmplitude = abs(numpy.average(data.amplitudeList))
            if averageAmplitude > threshhold: #visual output changes
                data.amplitude = averageAmplitude

        data.playingMusic = False
        stream.stop_stream()
        stream.close()

        p.terminate()


def ProgressTrack(data):    #tells user how well they performed
    CHUNK = 1024
    WIDTH = 2
    CHANNELS = 2
    RATE = 44100
    beatTime = 1 / float(data.bpm) * 60
    RECORD_SECONDS = beatTime

    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(WIDTH),
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    output=True,
                    frames_per_buffer=CHUNK)

    print("* recording")

    totalAmplitude = 0

    for i in range(0, int(RATE / CHUNK * (RECORD_SECONDS* 4))):
        data1 = stream.read(CHUNK)
        amplitudeList = numpy.absolute(numpy.fromstring(data1, numpy.int16))
        averageAmplitude = numpy.average(amplitudeList)
        totalAmplitude += averageAmplitude


    backgroundAMP = float(totalAmplitude)/float(RATE / CHUNK * (RECORD_SECONDS))
    print backgroundAMP



    print "calibrating play one note"

    AVamplitudeList = []
    for i in range(0, int(RATE / CHUNK * (RECORD_SECONDS * 4))):
        data1 = stream.read(CHUNK)
        amplitudeList = numpy.absolute(numpy.fromstring(data1, numpy.int16))
        maxAmplitude = numpy.amax(amplitudeList)
        AVamplitudeList += [maxAmplitude]


    noteAMP = max(AVamplitudeList) - backgroundAMP

    print(noteAMP,"noteAmp")



    ampRange = (noteAMP - 3000)
    maxAmplitudeList = []
    print("play now")
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS * 16)):
        data1 = stream.read(CHUNK)
        amplitudeList = numpy.absolute(numpy.fromstring(data1, numpy.int16))
        averageAmplitude = numpy.average(amplitudeList) - backgroundAMP
        maxAmplitude = numpy.amax(amplitudeList)
        maxAmplitudeList += [maxAmplitude]

    #counts notes

    notes = 0
    peaklist = listIntoPeaksSimple(maxAmplitudeList, 1)
    for value in range(len(peaklist)):
        if peaklist[value] > ampRange:
            notes += 1
                                #finds error in what they played
    difference = (abs(notes - len(data.currentBeatDictionary)*4))
    error = difference/float((len(data.currentBeatDictionary))*4)
    data.noteAccuracy = abs(1.0 - error) * 100
    stream.stop_stream()
    stream.close()

    p.terminate()

def playNotes(data):        #combines notes and metranome
    if data.mode == "drumTutor":         #Values were Experimentally Calibrated
        speedUpFile(data.metranomeSource,data.bpm/float(80)*180/float(165)
                    ,"metranome.wav")
        speedUpFile(playRudiment(data.currentBeatDictionary, data),
                    2* data.bpm/float(148) * 197/float(200),
                    "rudimentAtTempo.wav")

        sound1 = AudioSegment.from_file("metranome.wav") + 20
        sound2 = AudioSegment.from_file("rudimentAtTempo.wav")

        played_togther = sound1.overlay(sound2,
                                        position=(1/float(data.bpm)*60*1000*8))

        playMusic(data, (exportToFile(played_togther, "playedtogether.wav")))

    if data.mode == "addRudiments":
        speedUpFile(data.metranomeSource,
                    data.bpm / float(80) * 180 / float(165), "metranome.wav")

        sound1 = AudioSegment.from_file("metranome.wav") + 20
        sound1 = sound1[:9500]

        playMusic(data, (exportToFile(sound1, "metContribute.wav")))

####### Recording and Playing Functions #########





####### Main Data Functions ######

def init(data):
    data.timer = 0
    data.amplitude = 0
    data.timeSign = "4/4"
    data.amplitudeList = [1]
    data.waves = True
    data.circles = True
    data.colorArray = make2DList(1,8)
    data.col = 0
    data.angleShift = 0
    data.mode = "audioVisualizer"
    data.bpm = 200
    data.changeColors = False
    data.handAngle = 0
    data.switch = 1
    data.currentBeatDictionary = dict()
    data.currentRudimentName = ""
    data.rudimentList = []
    data.rudimentList += [rudiment("ParaDiddle",
                                {1: ("regular stroke", "eighth", "R", 1, 1),
                                 2: ("regular stroke", "eighth", "L", 0, 1),
                                 3: ("regular stroke", "eighth", "R", 0, 1),
                                 4: ("regular stroke", "eighth", "R", 0, 1),
                                 5: ("regular stroke", "eighth", "L", 1, 1),
                                 6: ("regular stroke", "eighth", "R", 0, 1),
                                 7: ("regular stroke", "eighth", "L", 0, 1),
                                 8: ("regular stroke", "eighth", "L", 0, 1)},
                                220,"play the accents out")]
    data.rudimentList += [rudiment("hertaDiddle",
                             {1: ("regular stroke", "sixteenth", "L", 0, 1),
                              2: ("regular stroke", "sixteenth", "L", 0, 1),
                              3: ("regular stroke", "eighth", "L", 0, 1),
                              4: ("regular stroke", "eighth", "R", 0, 1),
                              5: ("regular stroke", "sixteenth", "L", 0, 1),
                              6: ("regular stroke", "sixteenth", "L", 0, 1),
                              7: ("regular stroke", "eighth", "L", 0, 1),
                              8: ("regular stroke", "eighth", "R", 0, 1),
                              9: ("regular stroke", "sixteenth", "L", 0, 1),
                              10: ("regular stroke", "sixteenth", "L", 0, 1),
                              11: ("regular stroke", "sixteenth", "L", 0, 1),
                              12: ("regular stroke", "sixteenth", "L", 0, 1)},
                              180,"keep your rhythms open")]
    data.metranomeSource = "bottle_80bpm_1-4time_32beats_stereo_BQDVvY.wav"
    data.metranome = "metranome.wav"
    data.snareDrum = "Snare Drum Sound .1 Seconds"
    data.snareSound = pydub.AudioSegment.from_wav(data.snareDrum)
    data.accentedSnareSound = data.snareSound + 25
    data.selectedIndex = 0
    data.saveName = "name"
    data.musicTip = "write a tip about this rudiment"
    data.startingBPM = "starting tempo"
    data.entryList = [data.saveName, data.musicTip, data.startingBPM]
    data.entry = 0
    data.red = rgbString(225,95, 86)
    data.green = rgbString(163,211,156)
    data.lightBlue = rgbString(122, 204, 200)
    data.blueGreen = rgbString(74, 170, 165)
    data.darkBlue = rgbString(53,64,79)
    data.homeButtons = 0
    data.tip = ""
    data.playingMusic = False
    data.songList = ["None", "Thinking Out Loud.wav",
                     "Work from Home.wav", "watchme.wav"]
    data.songNumber = 1
    data.recordingInstruction = "Press the Record Button To Begin"
    data.contributeButtons = 0
    data.noteAccuracy = ""


def playRudiment(beatDictionary,data):  #makes rudiment sound from dictionary
    finalSound = 0
    dynamic = 300000
    multiple = 3
    for note in (beatDictionary):
        if beatDictionary[note][3] == True:
            finalSound += data.accentedSnareSound
        elif beatDictionary[note][3] == False:
            finalSound += data.snareSound
        if beatDictionary[note][1] == "eighth":
            finalSound += (data.snareSound - dynamic )
        elif beatDictionary[note][1] == "quarter":
            finalSound += (data.snareSound - dynamic ) * multiple
    finalSound *= multiple + 1
    return exportToFile(finalSound,"rudiment.wav")


def Flash(data):        #values for flash were experimentally deterimed
    if data.mode == "saveScreen":
        if data.entry % 3 == 0:
            if data.saveName == "name" and data.timer % 12 < 6:
                data.saveName = ""
            elif data.saveName == "" and data.timer % 12 >= 6:
                data.saveName = "name"
        if data.entry % 3 == 1:
            if (data.musicTip == "write a tip about this rudiment") \
                    and (data.timer % 12 < 6):
                 data.musicTip = ""
            elif data.musicTip == "" and data.timer % 12 >= 6:
                data.musicTip = "write a tip about this rudiment"
        if data.entry % 3 == 2:
            if data.startingBPM == "starting tempo" and data.timer % 12 < 6:
                data.startingBPM = ""
            elif data.startingBPM == "" and data.timer % 12 >= 6:
                data.startingBPM = "starting tempo"
        if data.saveName == "" and data.entry % 3 != 0:
            data.saveName = "name"
        if data.musicTip == "" and data.entry % 3 != 1:
                            data.musicTip = "write a tip about this rudiment"
        if data.startingBPM == "" and data.entry % 3 != 2:
                            data.startingBPM = "starting tempo"

def changeColors(data):     #changes the note color when played
    beatTime = 1 / float(data.bpm) * 60 * 1
    time.sleep(beatTime * 8)
    for i in range(4):
        noteValue = int(data.timeSign[2])
        for note in data.currentBeatDictionary:
            type = (data.currentBeatDictionary)[note][0]
            duration = (data.currentBeatDictionary)[note][1]
            sticking = (data.currentBeatDictionary)[note][2]
            accent = (data.currentBeatDictionary)[note][3]
            if duration == "quarter":
                (data.currentBeatDictionary)[note] = (type,
                                                duration, sticking, accent, -1)
                time.sleep(noteValue / float(4) * beatTime)
                (data.currentBeatDictionary)[note] = (type,
                                                duration, sticking, accent, 1)
            elif duration == "eighth":
                (data.currentBeatDictionary)[note] = (type,
                                                duration, sticking, accent, -1)
                time.sleep(noteValue / float(8) * beatTime)
                (data.currentBeatDictionary)[note] = (type,
                                                duration, sticking, accent, 1)
            elif duration == "sixteenth":
                (data.currentBeatDictionary)[note] = (type,
                                                duration, sticking, accent, -1)
                time.sleep(noteValue / float(16) * beatTime)
                (data.currentBeatDictionary)[note] = (type,
                                                duration, sticking, accent, 1)

def changeMetranome(data):  #changes hand of metranome to click
    beatTime = 1 / float(data.bpm) * 60 * 1000 * 2
    timeStart = time.time()
    while True:
        data.handAngle = (int((timeStart - time.time())*1000) % beatTime)\
                         / float(beatTime)
        if ((time.time() - timeStart)*1000 >= beatTime * 12)\
                and (data.mode == "drumTutor"):
            break
        elif ((time.time() - timeStart) * 1000 >= beatTime * 6) \
                and (data.mode == "addRudiments"):
            break



########### Mouse Functions ##########
def mousePressed(event, data):
    x = event.x
    y = event.y
    if data.mode == "saveScreen":
        actuallySave(x, y, data)
    if data.mode == "rudimentList":
        clickRudiment(x, y, data)
    if data.mode == "audioVisualizer":
        pressLearnButton(x,y,data)
        pressContributeButton(x, y, data)
        pressPlayButton(x,y,data)
    if data.mode == "drumTutor":
        changeBPM(x, y, data)
        pressPlayRudiment(x, y, data)
    if data.mode == "addRudiments":
        pressSaveButtton(x,y,data)
        pressRecordButtton(x, y, data)

def changeBPM(x,y,data):    #click changes Tempo
    yMargin = 25
    boxWidth = 100
    if (data.width / float(2) - boxWidth < x < data.width / float(2)
        - boxWidth / float(2)) \
            and (data.height - yMargin -20 < y <  data.height - yMargin):
        data.bpm -= 10
    elif (data.width / float(2) - boxWidth < x < data.width / float(2)
        - boxWidth / float(2)) \
            and (data.height - yMargin - 50 < y < data.height - yMargin - 30):
        data.bpm += 10


def pressPlayRudiment(x,y,data): #presses play button
    boxWidth = 100
    if data.width / 6 * 5 - boxWidth / float(2)< x < data.width / 6 * 5\
            + boxWidth / float(2) and \
                        data.height * .75 -\
            boxWidth / float(4) < y < data.height * .75 + boxWidth / float(4):
        thread1 = moveNotesThread(data)
        thread1.start()
        thread2 = playNotesThread(data)
        thread2.start()
        thread3 = metranomeThread(data)
        thread3.start()
        thread4 = progressclass(data)
        thread4.start()

def pressSaveButtton(x,y,data): #clicks on save Button
    boxWidth = 200
    yMargin = 75
    if (data.width / float(2) - boxWidth / float(2)
            -150< x < data.width / float(2) + boxWidth / float(2)-150) and \
            (data.height - yMargin < y < data.height - yMargin + 50):
        data.mode = "saveScreen"

def pressRecordButtton(x,y,data): #clicks on record Button
    boxWidth = 200
    yMargin = 75
    print(x,y)
    if (data.width / float(2) -
            boxWidth / float(2) + 150< x < data.width / float(2) +
            boxWidth / float(2) + 150) and \
            (data.height - yMargin < y < data.height - yMargin + 50):
        data.bpm = 80
        thread5 = playNotesThread(data)
        thread5.start()
        thread4 = metranomeThread(data)
        thread4.start()
        thread6 = beatDetectionclass(data)
        thread6.start()

def actuallySave(x,y,data): #clicks on save in save screen
    yMargin = 50
    boxWidth = 100
    if data.width / float(2) - \
        boxWidth / float(2) < x <  data.width / float(2) \
            + boxWidth / float(2) and \
                        data.height - yMargin - 50 < y <data.height - yMargin:
        saveToLibrary(data, data.saveName, data.currentBeatDictionary)
        data.mode = "audioVisualizer"



def pressLearnButton(x,y,data): #clicks on learn tab
    boxWidth = 75
    if data.width * 5 / float(8) + boxWidth - \
            110 < x <data.width * 5 / float(8) + 2 * boxWidth - 110 and \
                         data.height / float(5) < y < data.height / float(4):
        data.mode = "rudimentList"

def pressContributeButton(x,y,data): #clicks on contribute tab
    boxWidth = 75
    if data.width * 5 / float(8) - 2 * boxWidth - \
            110 < x < data.width * 5 / float(8) - boxWidth - 110 and \
                        data.height / float(5) < y < data.height / float(4):
        data.mode = "addRudiments"
        data.currentBeatDictionary = dict()

def pressPlayButton(x,y,data): #clicks on Play tab
    boxWidth = 75
    if data.width * 5 / float(8) + 4 * boxWidth - \
            110 < x < data.width * 5 / float(8) + 4.5 * boxWidth - 110 and \
                            data.height / float(5) < y < data.height / float(4):
        thread2 = playMusicThread(data)
        thread2.start()
        data.songList = thread2.songList
        #changes song
    elif data.width * 5 / float(8) + 4.5 * boxWidth - \
            110 < x < data.width * 5 / float(8) + 6 * boxWidth - 110 and \
     data.height / float(5) < y < (data.height / float(4) -
                    data.height / float(5)) / float(3) + data.height / float(5):
        data.songNumber += 1
        if data.songNumber >= len(data.songList):
            data.songNumber = 0
    elif data.width * 5 / float(8) + 4.5 * boxWidth - \
            110 < x < data.width * 5 / float(8) + 6 * boxWidth - 110 and \
        (data.height / float(4) -
            data.height / float(5)) / float(4) * 3 +\
                        data.height / float(5) < y < data.height / float(4):
        data.songNumber -= 1
        if data.songNumber < 0:
            data.songNumber = len(data.songList) -1


def clickRudiment(x,y,data):    #Clicks rudiment from display
    rudiments = 0
    boxWidth = 100
    boxHeight = 50
    row = 1
    for rudiment in data.rudimentList:
        rudiments += 1
        if rudiments > 4:
            rudiments -= 4
            row += 1
        if (data.width / float(5) * rudiments -
                boxWidth / float(2) < x < data.width / float(5) * rudiments +
                boxWidth / 2) \
                and (data.height / float(4) * row -
                    boxHeight / float(2) < y < data.height / float(4) * row +
                        boxHeight / float(2)):
            data.mode = "drumTutor"
            data.currentBeatDictionary = rudiment.beatDictionary
            data.currentRudimentName = rudiment.name
            data.tip = rudiment.tip
            data.bpm = rudiment.initialBPM
            data.noteAccuracy = ""

########### Mouse Functions ##########




########## Key Functions ############
def keyPressed(event, data,canvas):
    if data.mode == "audioVisualizer":
        if (event.keysym) == "l":
            if data.waves:
                data.waves = False
            else:
                data.waves = True
        if (event.keysym) == "c":
            if data.circles:
                data.circles = False
            else:
                data.circles = True
    if event.keysym == "Escape":
        data.mode = "audioVisualizer"

    # controls typing bar to look realistic
    if data.mode == "saveScreen":
        if data.entry % 3 == 0:
            if str(event.keysym) in string.ascii_letters:
                if data.saveName != "name":
                    data.saveName += str(event.keysym)
                if data.saveName == "name":
                    data.saveName = str(event.keysym)
            if str(event.keysym) == "BackSpace" and data.saveName != "name":
                data.saveName = data.saveName[0:-1]
            if str(event.keysym) == "space" and data.saveName != "name":
                data.saveName += " "
        if data.entry % 3 == 1:
            if str(event.keysym) in string.ascii_letters:
                if data.musicTip!= "write a tip about this rudiment":
                    data.musicTip += str(event.keysym)
                if data.musicTip == "write a tip about this rudiment":
                    data.musicTip = str(event.keysym)
            if (str(event.keysym) == "BackSpace") and\
                    (data.musicTip != "write a tip about this rudiment"):
                data.musicTip = data.musicTip[0:-1]
            if (str(event.keysym) == "space") and \
                    (data.musicTip != "write a tip about this rudiment"):
                data.musicTip += " "
        if data.entry % 3 == 2:
            if str(event.keysym) in string.digits:
                if data.startingBPM != "starting tempo":
                    data.startingBPM += str(event.keysym)
                if data.startingBPM == "starting tempo":
                    data.startingBPM = str(event.keysym)
            if (str(event.keysym) == "BackSpace") and\
                    (data.startingBPM != "starting tempo"):
                data.startingBPM = data.startingBPM[0:-1]
        if event.keysym == "Return":
            data.entry += 1
########## Key Functions ############




########## Timer Fired ############
def timerFired(data):   #changes met angles and starts recording immediately
    data.timer += 1
    if data.mode == "audioVisualizer":
        data.angleShift += 1
        if data.timer == 1:
            thread1 = recordThread(data)
            thread1.start()
            thread2 = clicksclass(data)
            thread2.start()
########## Timer Fired ############







########## Draw Functions ############

def drawCircle(canvas,data):        #draws circle visualization
    if data.circles:
        if len(data.amplitudeList) == 2048:
            try:
                for x in range(0,len(data.amplitudeList) - 1,200):
                    r = abs(data.amplitudeList[x]//float(400))
                    for angle in range(12):
                        cx = 1.25 * data.width // 2 + \
        math.cos((angle-data.angleShift/float(8))/float(12) * 2 * math.pi)*200
                        cy = 1.25 * data.height // 2 +\
        math.sin((angle+data.angleShift/float(8))/float(12) * 2 * math.pi)*200
                        canvas.create_oval(cx-r,cy-r,cx+r,cy+r,
                                           fill= data.darkBlue)
                    for angle in range(12):
                        cx = 1.25 *data.width // 2 + \
    math.cos((angle+data.angleShift/float(8)) / float(12) * 2 * math.pi) * 100
                        cy = 1.25 *data.height // 2 + \
    math.sin((angle-data.angleShift/float(8))/ float(12) * 2 * math.pi) * 100
                        canvas.create_oval(cx - r/float(2), cy - r/float(2),
                        cx + r/float(2), cy+ r/float(2), fill=data.blueGreen)
                    for angle in range(12):
                        cx = 1.25 *data.width // 2 +\
    math.cos((angle+data.angleShift/float(8)) / float(12) * 2 * math.pi) * 50
                        cy = 1.25 *data.height // 2 +\
    math.sin((angle+data.angleShift/float(8))/ float(12) * 2 * math.pi) * 50
                        canvas.create_oval(cx - r / float(4),
    cy - r / float(4), cx + r / float(4), cy + r / float(4),fill=data.green)
            except:
                print"sorry"


def drawFrequencyLine(canvas,data,width,cx,cy): #creats wave on side screen
    if data.waves:
        if len(data.amplitudeList) == 2048:
            try:
                r = int(width/float(140))
                for x in range(0,len(data.amplitudeList) - 1,r*2):
                    cxx = (cx - width/float(2)) + x * width // float(2048)
                    cyy = \
            data.amplitudeList[x]/(float(120000/float(width)))/float(1.35) + cy
                    cxx1 =\
                (cx - width/float(2)) + (x+r*2)* width // float(2048)
                    canvas.create_oval(cyy-r,cxx-r,cyy+r,cxx+r,
                                       fill= data.darkBlue)
                    if x + r*2 < len(data.amplitudeList):
                        cyy1 = \
data.amplitudeList[x + r*2] / (float(120000 / float(width))) / float(1.5) + cy
                        canvas.create_line(cyy,cxx,
                                    cyy1,cxx1,width=10, fill = data.blueGreen)
            except:
                print "sorry"


def drawHomeScreen(canvas,data): #draws all buttons on home
    boxWidth = 75
    canvas.create_text(data.width*5/float(8)- 20, data.height/float(8) - 20,
    text = "PARADIDDLES FOR DAYS", font = "Times 30 bold", fill = data.darkBlue)
    canvas.create_text(data.width * 5 / float(8), data.height / float(8),
                       text="PARADIDDLES FOR DAYS",
                       font="Times 30 bold", fill= data.blueGreen)
    canvas.create_text(data.width * 5 / float(8) + 20,
                       data.height / float(8) + 20, text="PARADIDDLES FOR DAYS",
                       font="Times 30 bold", fill= data.green)
    canvas.create_text(data.width * 5 / float(8),
                    data.height * 9 / float(10), text="I'm Listening to You...",
                       font="Times 20 italic bold", fill= data.darkBlue)
    if data.homeButtons == 1 :
        contributeColor = data.green
        playColor = data.green
        if data.timer % 10 < 5:
            learnColor = data.red
        else:
            learnColor = data.green
    elif data.homeButtons == 0:
        learnColor = data.green
        playColor = data.green
        if data.timer % 10 < 5:
            contributeColor = data.red
        else:
            contributeColor = data.green
    else:
        learnColor = data.green
        contributeColor = data.green
        if data.timer % 10 < 5:
            playColor = data.red
        else:
            playColor = data.green

    canvas.create_rectangle(data.width*5/float(8)- 2*boxWidth - 110,
            data.height/float(4), data.width*5/float(8)- boxWidth- 110,
            data.height/float(5), fill = contributeColor,
                            outline = data.darkBlue, width = 3)
    canvas.create_rectangle(data.width*5/float(8) + boxWidth - 110,
            data.height/float(4), data.width*5/float(8)+ 2*boxWidth-110,
            data.height/float(5), fill= learnColor,
                            outline = data.darkBlue, width = 3)
    canvas.create_rectangle(data.width * 5 / float(8) + 4 *boxWidth - 110,
            data.height / float(4),
            data.width * 5 / float(8) + 4.5 * boxWidth - 110,
                        data.height / float(5), fill=playColor,
                            outline=data.darkBlue, width=3)
    canvas.create_rectangle(data.width * 5 / float(8) + 4.5 * boxWidth - 110,
                            data.height / float(4),
                            data.width * 5 / float(8) + 6 * boxWidth - 110,
                            data.height / float(5), fill=data.green,
                            outline=data.darkBlue, width=3)
    canvas.create_line(data.width * 5 / float(8) + 4.5 * boxWidth - 110,
                (data.height / float(4) - data.height / float(5)) / float(3) +
                       data.height / float(5),
                       data.width * 5 / float(8) + 5.5 * boxWidth - 110,
                (data.height / float(4) - data.height / float(5)) / float(3) +
                       data.height / float(5),fill=data.darkBlue, width=2)
    canvas.create_line(data.width * 5 / float(8) + 4.5 * boxWidth - 110,
                (data.height / float(4) - data.height / float(5)) / float(4)*3 +
                       data.height / float(5),
                       data.width * 5 / float(8) + 5.5 * boxWidth - 110,
                (data.height / float(4) - data.height / float(5)) / float(4)*3 +
                       data.height / float(5), fill=data.darkBlue, width=2)
    canvas.create_text(data.width*5/float(8)- 1.5*boxWidth- 110,
                    data.height/float(4.5), font = "times 10 bold",
                       text= "Contribute", fill = data.darkBlue)
    canvas.create_text(data.width*5/float(8) + boxWidth* 1.5 - 110,
                data.height/float(4.5), text = "Learn",
                       font = "times 10 bold", fill = data.darkBlue)
    canvas.create_text(data.width * 5 / float(8) + boxWidth * 4.25 - 110,
                       data.height / float(4.5), text="Play",
                       font="times 10 bold", fill=data.darkBlue)
    canvas.create_text(data.width * 5 / float(8) + 5.25 * boxWidth - 110,
                       (data.height / float(4) -
        data.height / float(5)) / float(2) + data.height / float(5),
                    fill=data.darkBlue,
                font = "times 7 bold", text = data.songList[data.songNumber])
    canvas.create_polygon(data.width * 5 / float(8) + 4.5 * boxWidth - 110,
            (data.height / float(4) - data.height / float(5)) / float(3) +
                          data.height / float(5),
                          data.width * 5 / float(8) + 6 * boxWidth - 110,
            (data.height / float(4) - data.height / float(5)) / float(3) +
                          data.height / float(5),
                          data.width * 5 / float(8) + 5.25 * boxWidth - 110,
                         data.height / float(5), fill=data.darkBlue)
    canvas.create_polygon(data.width * 5 / float(8) + 4.5 * boxWidth - 110,
                          (data.height / float(4) -
                           data.height / float(5)) / float(4)*3 +
                          data.height / float(5),
                          data.width * 5 / float(8) + 6* boxWidth - 110,
                          (data.height / float(4) -
                           data.height / float(5)) / float(4)*3 +
                          data.height / float(5),
                          data.width * 5 / float(8) + 5.25 * boxWidth -
                          110, data.height / float(4), fill=data.darkBlue)
    canvas.create_text(data.width / float(8) * 5,
                       data.height - 30,
                       fill=data.darkBlue,
                       font= "times 10 bold",
            text="Navigation Key: 1 Stick Click = Next Button   2 Stick " +
            "Clicks = Select Option   3 Stick Clicks = Back to Home Screen")



def drawRudimentScreen(canvas,data):    #draws all rudiments
    canvas.create_text(data.width / float(2) , data.height / float(8) ,
                       text="Pick A Rudiment",
                       font = "Times 30 bold", fill = data.darkBlue)
    rudiments = 0
    row = 1
    boxWidth = 100
    boxHeight = 50
    for rudiment in data.rudimentList:
        if rudiments == data.selectedIndex:
            rudiment.selected = True
        else:
            rudiment.selected = False
        color = data.green
        if rudiment.selected == True:
            if data.timer % 24 < 12:
                color = data.red
        rudiments += 1
        if rudiments > 4:
            rudiments -= 4
            row += 1
        canvas.create_rectangle(data.width / float(5) * rudiments -
                                boxWidth/float(2),
                    (data.height / float(4)* row - boxHeight/float(2)) ,
                                data.width / float(5) * rudiments + boxWidth/2,
                    (data.height / float(4) * row + boxHeight/float(2)) ,
                            fill = color, outline = data.darkBlue, width = 3)
        canvas.create_text(data.width / float(5) * rudiments,
                           data.height / float(4) * row, text=rudiment.name,
                           font="Times 12 bold",
                           fill= data.darkBlue)


def drawStaff(canvas, data):    #draws staff
    xMargin = 50
    yMargin = 200
    staffDistance = 50

    # staff Lines
    canvas.create_line(xMargin, yMargin, data.width - xMargin, yMargin)
    canvas.create_line(xMargin, yMargin + staffDistance,
                       data.width - xMargin, yMargin + staffDistance)
    canvas.create_line(xMargin, yMargin + staffDistance * 2,
                       data.width - xMargin, yMargin + staffDistance * 2)
    canvas.create_line(xMargin, yMargin + staffDistance * 3,
                       data.width - xMargin, yMargin + staffDistance * 3)
    canvas.create_line(xMargin, yMargin + staffDistance * 4,
                       data.width - xMargin, yMargin + staffDistance * 4)
    canvas.create_line(data.width - xMargin, yMargin,
                       data.width - xMargin, yMargin + staffDistance * 4)

    # draw Time Signiture
    canvas.create_text(xMargin * 1.5, yMargin - xMargin / 2,
                       font=("Times", 100), anchor="n", text=data.timeSign[0])
    canvas.create_text(xMargin * 1.5,
                       yMargin + staffDistance * 2 - xMargin / 2,
                       font=("Times", 100),
                       anchor="n", text=data.timeSign[2])

def drawNotes(canvas, data):
    totalNotes = int(data.timeSign[0])
    noteValue = int(data.timeSign[2])
    noteNumberSoFar = 0
    if (data.currentBeatDictionary) != None: #get info from dictionary
        for note in data.currentBeatDictionary:
            type = (data.currentBeatDictionary)[note][0]
            duration = (data.currentBeatDictionary)[note][1]
            sticking = (data.currentBeatDictionary)[note][2]
            accent = (data.currentBeatDictionary)[note][3]
            color = (data.currentBeatDictionary)[note][4]
            if type == "regular stroke":    #makes sure no more than 1 measure
                if (duration == "quarter") and\
                    (noteNumberSoFar + 1 / float(4) * noteValue) <= totalNotes:
                    drawQuarterNote(canvas, data, noteNumberSoFar,
                                    totalNotes, sticking, accent, color)
                    noteNumberSoFar += 1 / float(4) * noteValue
                elif (duration == "eighth") and\
                    (noteNumberSoFar + 1 / float(8) * noteValue) <= totalNotes:
                    noteNumberSoFar += 1 / float(8) * noteValue
                    if note + 1 > len(data.currentBeatDictionary):
                        if data.currentBeatDictionary[note - 1][1] == "eighth":
                            bar = 2
                        else:
                            bar = 0
                    elif (data.currentBeatDictionary[note + 1][1] != "eighth") \
        and (note != 1 and data.currentBeatDictionary[note - 1][1] == "eighth")\
        and (almostEqual(noteNumberSoFar , int(noteNumberSoFar)) == True)\
        or ( (note != 1)
             and (data.currentBeatDictionary[note + 1][1] == "eighth")
             and (data.currentBeatDictionary[note - 1][1] == "eighth")
             and (almostEqual(noteNumberSoFar , int(noteNumberSoFar)))):
                        bar = 2
                    elif (data.currentBeatDictionary[note + 1][1] == "eighth")\
            and (almostEqual(noteNumberSoFar , int(noteNumberSoFar)) == False):
                        bar = 1
                    else:
                        bar = 0
                    drawEighthNote(canvas, data,
            noteNumberSoFar - 1 / float(8) * noteValue,
                                   totalNotes, sticking, accent, color, bar)
                elif duration == "sixteenth" and (noteNumberSoFar +
                                    1 / float(16) * noteValue) <= totalNotes:
                    noteNumberSoFar += 1 / float(16) * noteValue
                    if note + 1 > len(data.currentBeatDictionary):
                        if data.currentBeatDictionary[note -
                                1][1] == "sixteenth":
                            bar = 2
                        else:
                            bar = 0
                    elif data.currentBeatDictionary[note +
                            1][1] == "sixteenth":
                        bar = 1
                    elif data.currentBeatDictionary[note +
                            1][1] != "sixteenth":
                        bar = 2
                    else:
                        bar = 0
                    drawSixteenthNote(canvas, data, noteNumberSoFar -
                                      1 / float(16) * noteValue,
                                      totalNotes, sticking,
                                   accent, color, bar)

def drawQuarterNote(canvas, data, noteNumberSoFar, totalNotes, sticking, accent,
                    color):
    noteWidth = 50
    xMargin = 150
    yMargin = 200
    staffDistance = 50
    if color == 1:
        noteColor = "black"
    else:
        noteColor = "gray"
    yStart = yMargin + staffDistance * 2.5
    xStart = noteNumberSoFar / float(totalNotes) * 800 + xMargin
    canvas.create_oval(xStart, yStart, xStart + noteWidth,
                       yStart + staffDistance, fill=noteColor)
    canvas.create_line(xStart + noteWidth, yMargin,
                       xStart + noteWidth, yMargin + staffDistance * 3, width=5,
                       fill=noteColor)
    canvas.create_text(xStart + noteWidth / 2,
                yMargin + staffDistance * 4.5, text=sticking, font="times 25",
                       fill=noteColor)
    if accent:
        canvas.create_line(xStart + noteWidth / 2,
                        yMargin - staffDistance / 4, xStart + noteWidth * 1.25,
                           yMargin - staffDistance / 4, width=2)
        canvas.create_line(xStart + noteWidth / 2,
                        yMargin - staffDistance / 4, xStart + noteWidth * 1.25,
                           yMargin - staffDistance / 2, width=2)

def drawEighthNote(canvas, data, noteNumberSoFar, totalNotes, sticking, accent,
                   color, bar):
    noteWidth = 50
    xMargin = 150
    yMargin = 200
    staffDistance = 50
    if color == 1:
        noteColor = "black"
    else:
        noteColor = data.green
    yStart = yMargin + staffDistance * 2.5
    xStart = noteNumberSoFar / float(totalNotes) * 800 + xMargin
    previousXStart = (noteNumberSoFar+.5) / float(totalNotes) * 800 + xMargin
    canvas.create_oval(xStart, yStart, xStart + noteWidth,
                       yStart + staffDistance, fill=noteColor)
    canvas.create_line(xStart + noteWidth, yMargin, xStart + noteWidth,
                       yMargin + staffDistance * 3, width=5,
                       fill=noteColor)
    canvas.create_text(xStart + noteWidth / 2, yMargin + staffDistance * 4.5,
                       text=sticking, font="times 25",
                       fill=noteColor)
    if bar == 0:
        canvas.create_polygon(xStart + noteWidth, yMargin, xStart + noteWidth,
                              yMargin + noteWidth,
                              xStart + noteWidth * 1.25,
                        yMargin + noteWidth * 1.125, xStart + noteWidth * 1.5,
                              yMargin + noteWidth * 1.25,
                        xStart + noteWidth * 1.75, yMargin + noteWidth * 1.75,
                              xStart + noteWidth * 1.75,
                              yMargin + noteWidth * 2.1,
                              xStart + noteWidth * 1.6,
                        yMargin + noteWidth * 2.4, xStart + noteWidth * 1.7,
                              yMargin + noteWidth * 2.4,
                        xStart + noteWidth * 1.85, yMargin + noteWidth * 2.1,
                              xStart + noteWidth * 1.9,
                        yMargin + noteWidth * 1.75, xStart + noteWidth * 1.25,
                              yMargin + noteWidth / 1.25, fill=noteColor)
    elif bar == 1:
        canvas.create_rectangle(xStart + noteWidth, yMargin,
                        previousXStart + noteWidth,
                                yMargin + staffDistance * .5, fill = "black")
    if accent:
        canvas.create_line(xStart + noteWidth / 2, yMargin - staffDistance / 4,
                           xStart + noteWidth * 1.25,
                           yMargin - staffDistance / 4, width=2)
        canvas.create_line(xStart + noteWidth / 2, yMargin - staffDistance / 4,
                           xStart + noteWidth * 1.25,
                           yMargin - staffDistance / 2, width=2)

def drawSixteenthNote(canvas, data, noteNumberSoFar, totalNotes, sticking,
                      accent, color, bar):
    noteWidth = 50
    xMargin = 150
    yMargin = 200
    staffDistance = 50
    if color == 1:
        noteColor = "black"
    else:
        noteColor = "gray"
    yStart = yMargin + staffDistance * 2.5
    xStart = noteNumberSoFar / float(totalNotes) * 800 + xMargin
    previousXStart = (noteNumberSoFar + .25) / float(totalNotes) * 800 + xMargin
    canvas.create_oval(xStart, yStart, xStart + noteWidth,
                       yStart + staffDistance, fill=noteColor)
    canvas.create_line(xStart + noteWidth, yMargin, xStart + noteWidth,
                       yMargin + staffDistance * 3, width=5,
                       fill=noteColor)
    canvas.create_text(xStart + noteWidth / 2, yMargin + staffDistance * 4.5,
                       text=sticking, font="times 25",
                       fill=noteColor)
    if bar == 0: #drawing the tails
        canvas.create_polygon(xStart + noteWidth, yMargin + 5,
                              xStart + noteWidth, yMargin + noteWidth + 5,
                              xStart + noteWidth * 1.25 - 15,
                              yMargin + noteWidth * 1.125 + 5,
                              xStart + noteWidth * 1.5 - 15,
                              yMargin + noteWidth * 1.25,
                              xStart + noteWidth * 1.75 - 15,
                              yMargin + noteWidth * 1.75,
                              xStart + noteWidth * 1.75 - 15,
                              yMargin + noteWidth * 2.1,
                              xStart + noteWidth * 1.6 - 15,
                              yMargin + noteWidth * 2.4,
                              xStart + noteWidth * 1.7 - 15,
                              yMargin + noteWidth * 2.4,
                              xStart + noteWidth * 1.85 - 15,
                              yMargin + noteWidth * 2.1 + 5,
                              xStart + noteWidth * 1.9 - 15,
                              yMargin + noteWidth * 1.75,
                              xStart + noteWidth * 1.25 - 15,
                              yMargin + noteWidth / 1.25, fill=noteColor)
        canvas.create_polygon(xStart + noteWidth, yMargin - 2,
                              xStart + noteWidth, yMargin + noteWidth - 25,
                              xStart + noteWidth * 1.25,
                              yMargin + noteWidth * 1.125 - 25,
                              xStart + noteWidth * 1.5,
                              yMargin + noteWidth * 1.25 - 25,
                              xStart + noteWidth * 1.75,
                              yMargin + noteWidth * 1.75 - 25,
                              xStart + noteWidth * 1.75,
                              yMargin + noteWidth * 2.1 - 25,
                              xStart + noteWidth * 1.6,
                              yMargin + noteWidth * 2.4 - 25,
                              xStart + noteWidth * 1.7,
                              yMargin + noteWidth * 2.4 - 25,
                              xStart + noteWidth * 1.85,
                              yMargin + noteWidth * 2.1 - 25,
                              xStart + noteWidth * 1.9,
                              yMargin + noteWidth * 1.75 - 25,
                              xStart + noteWidth * 1.25,
                              yMargin + noteWidth / 1.25 - 25, fill=noteColor)
    elif bar == 1:
        canvas.create_rectangle(xStart + noteWidth,
                                yMargin, previousXStart + noteWidth,
                                yMargin + staffDistance * .2,
                                fill="black")
        canvas.create_rectangle(xStart + noteWidth,
                                yMargin + staffDistance * .3,
                                previousXStart + noteWidth,
                                yMargin + staffDistance * .5,
                                fill="black")
    if accent:
        canvas.create_line(xStart + noteWidth / 2,
                           yMargin - staffDistance / 4,
                           xStart + noteWidth * 1.25,
                           yMargin - staffDistance / 4, width=2)
        canvas.create_line(xStart + noteWidth / 2, yMargin - staffDistance / 4,
                           xStart + noteWidth * 1.25,
                           yMargin - staffDistance / 2, width=2)




def drawSaveScreen(canvas,data):    #makes save pop up
    yMargin = 50
    boxWidth = 100
    canvas.create_text(data.width / 2, data.height / 4,
                       text="Save Your Contribution",
                       fill= data.darkBlue, font="times 50 bold")
    canvas.create_line(data.width / 4, 2 * data.height / 4, 3 * data.width / 4,
                       2 * data.height / 4, fill= data.darkBlue)
    canvas.create_line(data.width / 4, 5 * data.height / 8, 3 * data.width / 4,
                       5 * data.height / 8, fill= data.darkBlue)
    canvas.create_line(data.width / 4, 3 * data.height / 4, 3 * data.width / 4,
                       3 * data.height / 4, fill= data.darkBlue)
    name = data.saveName
    musicTip = data.musicTip
    startingBPM = data.startingBPM
    canvas.create_text(data.width / 4, 2 * data.height / 4, text=name,
                       anchor=SW, fill=data.blueGreen, font="Times 11")
    canvas.create_text(data.width / 4, 5 * data.height / 8, text=musicTip,
                       anchor=SW, fill= data.blueGreen,
                       font="Times 11")
    canvas.create_text(data.width / 4, 3 * data.height / 4, text=startingBPM,
                       anchor=SW, fill= data.blueGreen, font="Times 11")
    canvas.create_rectangle(data.width / float(2) - boxWidth / float(2),
                            data.height - yMargin,
                            data.width / float(2) + boxWidth / float(2),
                            data.height - yMargin - 50, fill = data.green,
                            outline = data.darkBlue, width = 3)
    canvas.create_text(data.width / float(2), data.height - yMargin - 25,
                       text = "Save", font = "times 13 bold")

def drawBPMsign(canvas, data):  #makes bpm sign
    yMargin = 25
    boxWidth = 100
    canvas.create_rectangle(data.width / float(2), data.height - yMargin,
                            data.width / float(2) + 2 * boxWidth / float(2),
                            data.height - yMargin - 50,
                            fill= data.blueGreen, width=3)
    canvas.create_rectangle(data.width / float(2) - boxWidth,
                            data.height - yMargin,
                            data.width / float(2) - boxWidth / float(2),
                            data.height - yMargin - 20,
                            fill= data.blueGreen, width=3)
    canvas.create_rectangle(data.width / float(2) - boxWidth,
                            data.height - yMargin - 30,
                            data.width / float(2) - boxWidth / float(2),
                            data.height - yMargin - 50,
                            fill= data.blueGreen, width=3)
    canvas.create_polygon(data.width / float(2) - boxWidth / float(2),
                          data.height - yMargin - 20,
                          data.width / float(2) - boxWidth,
                          data.height - yMargin - 20,
                          data.width / float(2) - boxWidth / (float(4) / 3),
                          data.height - yMargin, fill= data.darkBlue)
    canvas.create_polygon(data.width / float(2) - boxWidth / float(2),
                          data.height - yMargin - 30,
                          data.width / float(2) - boxWidth,
                          data.height - yMargin - 30,
                          data.width / float(2) - boxWidth / (float(4) / 3),
                          data.height - yMargin - 50, fill= data.darkBlue)
    canvas.create_text(data.width / float(2) + boxWidth / float(2),
                       data.height - yMargin - 25, text=str(data.bpm),
                       font="times 20 bold", fill= data.darkBlue)

def drawTutorScreen(canvas, data):  #draws tutor screen
    yMargin = 100
    boxWidth = 100
    if data.playingMusic == False:
        if data.timer % 10 < 5:
            playColor = data.red
        else:
            playColor = data.green
    else:
        playColor = data.green
    canvas.create_text(data.width / 2, yMargin,
                       font=("Times 60 italic bold"), fill= data.darkBlue,
                       text=data.currentRudimentName)
    canvas.create_text(data.width / 6, data.height*.75,
                       font=("Times 15 italic bold"), fill=data.darkBlue,
                       text="Rudiment Tip: ")
    canvas.create_text(data.width / 6, data.height * .8,
                       font=("Times 15 italic bold"), fill=data.darkBlue,
                       text =data.tip)
    canvas.create_rectangle(data.width / 6 * 5 - boxWidth/float(2),
                            data.height * .75 - boxWidth / float(4),
                            data.width / 6 * 5 + boxWidth/float(2),
                            data.height * .75 + boxWidth / float(4),
                            fill = playColor, outline = data.darkBlue,
                            width = 3)
    canvas.create_text(data.width / 6 * 5, data.height * .75,
                       font=("Times 10 bold"), fill=data.darkBlue,
                       text="Play Rudiment")
    if type(data.noteAccuracy) != str:
        canvas.create_text(data.width / 6 * 5, data.height * .85,
                           font=("Times 10 bold"), fill=data.darkBlue,
                           text= "You Hit Roughly " + str(data.noteAccuracy) +
                                 "% of All Notes!")


def drawContributeScreen(canvas,data):  #draws contribute screen
    yMargin = 75
    boxWidth = 200
    if data.contributeButtons == 0:
        recordColor = data.green
        if data.timer % 10 < 5:
            saveColor = data.red
        else:
            saveColor = data.green
    else:
        saveColor = data.green
        if data.timer % 10 < 5:
            recordColor = data.red
        else:
            recordColor = data.green

    canvas.create_text(data.width / 2, yMargin, font=("Times 40 italic bold"),
                       fill=data.darkBlue,
                       text="Contribute To The Library")
    canvas.create_text(data.width / 2, yMargin*2, font=("Times 20 italic bold"),
                       fill=data.darkBlue,
                       text= data.recordingInstruction)
    canvas.create_rectangle(data.width / float(2) - boxWidth / float(2)-150,
                            data.height - yMargin, data.width / float(2) +
                            boxWidth / float(2)-150, data.height -yMargin + 50,
                            fill = saveColor, outline = data.darkBlue,
                            width = 3)
    canvas.create_rectangle(data.width / float(2) - boxWidth / float(2) + 150,
                            data.height - yMargin,
                            data.width / float(2) + boxWidth / float(2) + 150,
                            data.height - yMargin + 50,
                            fill=recordColor, outline=data.darkBlue, width=3)
    canvas.create_text(data.width / float(2)- 150,data.height -yMargin +
                       25, font="times 12 bold", fill = data.darkBlue,
                       text="Save Rudiment to Library" )
    canvas.create_text(data.width / float(2) + 150, data.height - yMargin + 25,
                       font="times 12 bold", fill=data.darkBlue,
                      text="Record")

def drawMetranome(canvas, data):    #draws metranome
    rMet = 140
    rHand = 150
    yMargin = 100

    if data.switch == 1:
        angle = (1 - data.handAngle) * 2 * math.pi
    else:
        angle = (data.handAngle) * 2 * math.pi
    if angle >= math.pi and angle < 2 * math.pi - .01:
        data.switch *= -1
    if angle >= 3 * math.pi / float(2):
        angle = 0
    elif angle >= math.pi:
        angle = math.pi

    canvas.create_arc(data.width / 2 - rHand - 25, data.height -
                      yMargin - rHand - 15, data.width / 2 + rHand + 25,
                      data.height - yMargin + rHand + 25, start=0,
                      extent=180, fill= data.blueGreen, width=3)
    canvas.create_line(data.width / 2, data.height - yMargin,
                       data.width / 2 + math.cos(angle) * rMet,
                       data.height - yMargin - math.sin(angle) * rMet, width=4)
    canvas.create_oval(data.width / 2 + 5, data.height - yMargin + 10,
                       data.width / 2 - 5,
                       data.height - yMargin - 10, fill= data.darkBlue)
    for tickNumber in range(0, 210, 30):
        tickAngle = tickNumber / float(180) * math.pi
        canvas.create_line(data.width / 2 + (rMet + 10) * math.cos(tickAngle),
                           data.height -
                           yMargin - math.sin(tickAngle) * (rMet + 10),
                           data.width / 2 + (rMet) * math.cos(tickAngle),
                           data.height -
                           yMargin - math.sin(tickAngle) * (rMet), width=4)




def redrawAll(canvas, data): #redraws everything
    image = canvas.data["image"]
    canvas.create_image(data.width / 2, data.height / 2, image=image)
    if data.mode == "audioVisualizer":
        drawHomeScreen(canvas, data)
        drawCircle(canvas, data)
        drawFrequencyLine(canvas,data,data.width,400,150)
    if data.mode == "rudimentList":
        drawRudimentScreen(canvas,data)
    if data.mode == "drumTutor":
        drawTutorScreen(canvas, data)
        drawStaff(canvas, data)
        drawNotes(canvas, data)
        drawMetranome(canvas, data)
        drawBPMsign(canvas, data)
    if data.mode == "addRudiments":
        drawContributeScreen(canvas, data)
        drawMetranome(canvas, data)
        drawStaff(canvas, data)
        drawNotes(canvas, data)
    if data.mode == "saveScreen":
        drawSaveScreen(canvas,data)
        Flash(data)





####################################
# use the run function as-is
####################################

#run Function is adapted https://www.cs.cmu.edu/~112/notes/notes-animations.html
def ParradiddlesForDays(width=1000, height=750):
    def redrawAllWrapper(canvas, data):
        canvas.delete(ALL)
        redrawAll(canvas, data)
        canvas.update()

    def mousePressedWrapper(event, canvas, data):
        mousePressed(event, data)
        redrawAllWrapper(canvas, data)

    def keyPressedWrapper(event, canvas, data):
        keyPressed(event, data,canvas)
        redrawAllWrapper(canvas, data)

    def timerFiredWrapper(canvas, data):
        timerFired(data)
        redrawAllWrapper(canvas, data)
        # pause, then call timerFired again
        canvas.after(data.timerDelay, timerFiredWrapper, canvas, data)
    # Set up data and call init
    class Struct(object): pass
    data = Struct()
    data.width = width
    data.height = height
    data.timerDelay = 10 # milliseconds
    init(data)
    # create the root and the canvas
    root = Tk()
    canvas = Canvas(root, width=data.width, height=data.height)
    canvas.pack(fill = BOTH, expand = YES)
    root.canvas = canvas.canvas = canvas
    canvas.data = {}
    image = PhotoImage(file="whiteBackground.gif")
    canvas.data["image"] = image


    # set up events
    root.bind("<Button-1>", lambda event:
                            mousePressedWrapper(event, canvas, data))
    root.bind("<Key>", lambda event:
                            keyPressedWrapper(event, canvas, data))
    timerFiredWrapper(canvas, data)
    # and launch the app
    root.mainloop()  # blocks until window is closed
    print("bye!")


ParradiddlesForDays()
