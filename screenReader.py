import globalVar


import pyautogui

import time
from multiprocessing import Pool, Process
from collections import OrderedDict

TIME_IMAGE_MAP = {
    "0" : "images/time0.png",
    "1" : "images/time1.png",
    "2" : "images/time2.png",
    "3" : "images/time3.png",
    "4" : "images/time4.png",
    "5" : "images/time5.png",
    "6" : "images/time6.png",
    "7" : "images/time7.png",
    "8" : "images/time8.png",
    "9" : "images/time9.png",
    ":" : "images/timeColon.png"
}

FPS_IMAGE_MAP = {
    "0" : "images/fps0.png",
    "1" : "images/fps1.png",
    "2" : "images/fps2.png",
    "3" : "images/fps3.png",
    "4" : "images/fps4.png",
    "5" : "images/fps5.png",
    "6" : "images/fps6.png",
    "7" : "images/fps7.png",
    "8" : "images/fps8.png",
    "9" : "images/fps9.png",
}

FPS_IMAGE = "images/fps.png"

class FPSLevelFinder():
    lastResult = None
    topRange = 5
    height = 30
    def __init__(self):
        pyautogui.screenshot(region=globalVar.FPS_REGION).save("fpsRegion.png")
    def Get(self) -> int:
        foundLevel = pyautogui.locateOnScreen(FPS_IMAGE, grayscale=True, region=globalVar.FPS_REGION, confidence=.91)
        if not foundLevel:
            return self.lastResult
        asTop = foundLevel.top - self.topRange
        asRegion = [x for x in globalVar.FPS_REGION]
        asRegion[1] = asTop
        asRegion[2] = asRegion[2]
        asRegion[3] = self.height
        self._SetLast(asRegion)
        return asRegion

    def _SetLast(self, newResult):
        self.lastResult = newResult


def FindFPSNumber(argTup):
    givenNumber, givenRegion = argTup
    return (givenNumber, list(pyautogui.locateAllOnScreen(FPS_IMAGE_MAP[givenNumber], grayscale=True, region=givenRegion, confidence=.91)))

def FindNumber(givenNumber):
    return (givenNumber, list(pyautogui.locateAllOnScreen(TIME_IMAGE_MAP[givenNumber], grayscale=True, region=timeRegion, confidence=.91)))


class FPSFinder():
    def __init__(self, threads):
        self.threads = threads
        self.fpsLevelFinder = FPSLevelFinder()
        self.fpsLevel = None
        self.pool = Pool(self.threads)
        self.MAX_BELIVEABLE_FPS = 400
    def Get(self) -> int:
        self.UpdateFPSLevel()
        if not self.fpsLevel:
            return None
        results = self.pool.map(FindFPSNumber, [(x, self.fpsLevel) for x in FPS_IMAGE_MAP.keys()])
        givenString = ArrangeResults(results)
        if givenString:
            asInt = int(givenString)
            if asInt < self.MAX_BELIVEABLE_FPS:
                return int(givenString)
        return None
    def UpdateFPSLevel(self):
        self.fpsLevel = self.fpsLevelFinder.Get()

def ArrangeResults(givenResults):
    actualResults = {}
    for result in givenResults:
        if len(result[1]) > 0:
            for foundInstance in result[1]:
                actualResults[foundInstance.left] = result[0]
    givenString = ""
    actualResults = OrderedDict(sorted(actualResults.items()))
    for x in actualResults.values():
        givenString += x
    # print(actualResults.keys())
    return givenString

class Buffer():
    def __init__(self, length):
        self.length = length
        self.asList = []
        self.index = -1
    def add(self, elem):
        if len(self.asList) == self.length:
            self.index += 1
            if self.index >= self.length:
                self.index = 0
            self.asList[self.index] = elem
        else:
            self.asList.append(elem)

    def get(self):
        return self.asList
    
class TimeUpdater():
    def __init__(self, threads):
        from multiprocessing import Pool
        assert isinstance(threads, int) and threads > 0
        self.threads = threads
        self.pool = Pool(self.threads)
        self.time = None
        self._closed = False
        self.ready = True
        self.lastSecondGot = Buffer(3)
        pyautogui.screenshot(region=globalVar.TIME_REGION).save("timeRegion.png")

    def getTime(self):
        return self.time

    def run(self):
        while not self.ready:
            print("Waiting, not yet ready")
            time.sleep(.01)
        try:
            results = ArrangeResults(self.pool.map(FindNumber, TIME_IMAGE_MAP.keys()))[::-1].split(":")
            results = [int(x[::-1]) for x in results]
            # print("RESULTS:", results)
        except:
            self.time = None
            return
        totalTime = 0
        multiplier = 1
        for r in results:
            totalTime += multiplier * r
            multiplier *= 60
        self.time = totalTime

    def __del__(self):
        try:
            self.pool.close()
        except AttributeError:
            pass
        self._closed = True



def GetTimeProcess(threads, sleepTime, intPipe, killingPipe):
    updater = TimeUpdater(threads)
    while True:
        updater.run()
        intPipe[0] = updater.getTime()
        time.sleep(sleepTime)
        if killingPipe.qsize() > 0:
            del updater
            return

def GetFpsProcess(threads, sleepTime, intPipe, killingPipe):
    updater = FPSFinder(threads)
    while True:
        result = updater.Get()
        intPipe[0] = result
        time.sleep(sleepTime)
        if killingPipe.qsize() > 0:
            del updater
            return

