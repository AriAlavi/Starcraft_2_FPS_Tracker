
from screenReader import GetTimeProcess, GetFpsProcess
import globalVar

from PIL import Image
import PIL.ImageOps 
import pytesseract

import multiprocessing
import csv
import time
import os








def GetFPS(FPS_RECT, RESOURCE_STALL_RECT, save=False):
    def GetFPSInterior(Rect, save=False):
        fpsImage = getRectAsImage(Rect)
        fpsImage = PIL.ImageOps.grayscale(fpsImage) 
        if save:
            fpsImage.save("{}fps.png".format(str(Rect)))
        asString = pytesseract.image_to_string(fpsImage)
        lastNum = False
        stringWithNumsOnly = ""
        for char in asString:
            try:
                int(char)
            except:
                if lastNum:
                    break
                else:
                    continue
            lastNum = True
            stringWithNumsOnly += char
        if len(stringWithNumsOnly) > 0:
            return int(stringWithNumsOnly)
    if save:
        time.sleep(2)
    return GetFPSInterior(FPS_RECT, save) or GetFPSInterior(RESOURCE_STALL_RECT, save)

class TimeGetter():

    TIME_DIFFERENCE_TOLERANCE = 30

    lastTime = None
    lastTimeTime = None

    def __init__(self):
        self.communicator = multiprocessing.Manager().list([None,])
        self.killer = multiprocessing.Manager().Queue()
        self.updater = multiprocessing.Process(target=GetTimeProcess, args=(globalVar.THREADS, .1, self.communicator, self.killer))
        self.updater.start()

    def Get(self, useFallback):
        asTime = self.communicator[0]
        # print("Updater time:", asTime)
        fallbackTime = self._Fallback()        
        if not asTime:
            return fallbackTime
        if not (fallbackTime - self.TIME_DIFFERENCE_TOLERANCE <= asTime <= fallbackTime + self.TIME_DIFFERENCE_TOLERANCE):
            print("Got time is {} but it's too far from the expected time of {}".format(asTime, fallbackTime))
            if useFallback:
                return fallbackTime
        self._NewFallback(asTime)
        return asTime


    def _GetTime(self) -> int:
        return int(time.perf_counter() * globalVar.SIMULATION_SPEED)

    def _NewFallback(self, newTime):
        self.lastTime = newTime
        self.lastTimeTime = self._GetTime()
    def _Fallback(self):
        if self.lastTime:
            return self.lastTime + self._GetTime() - self.lastTimeTime
        return self._GetTime()

    def __del__(self):
        try:
            self.killer.put(True)
        except AttributeError:
            pass

class FPSGetter():
    def __init__(self):
        self.communicator = multiprocessing.Manager().list([None,])
        self.killer = multiprocessing.Manager().Queue()
        self.updater = multiprocessing.Process(target=GetFpsProcess, args=(globalVar.THREADS, .1, self.communicator, self.killer))
        self.updater.start()
    def Get(self):
        return self.communicator[0]



def getUniqueSqliteFileName():
    def createName(i):
        basename = "DATA"
        return "{}_{}.csv".format(basename, str(i).zfill(3))
    incrementor = 0
    while createName(incrementor) in os.listdir():
        incrementor += 1
    return createName(incrementor)




# GetFPS(FPS_AREA, FPS_AREA_RESOURCE_STALLS, True)
def main(writer):
    timeGetter = TimeGetter()
    fpsGetter = FPSGetter()
    lastTime = None
    while True:
        gotTime = timeGetter.Get(True)
        time.sleep(.5)
        # print(time)
        if gotTime and gotTime != lastTime:
            if lastTime and gotTime < lastTime:
                print("Got {} but last time was {}. Cannot go back in time.".format(gotTime, lastTime))
                continue
            lastTime = gotTime
            fps = fpsGetter.Get()
            if fps:
                writer.writerow([gotTime, fps])
                print([gotTime, fps])
            

if __name__ == "__main__":
    csvfile = open(getUniqueSqliteFileName(), "w", newline="")
    writer = csv.writer(csvfile, delimiter=',')
    writer.writerow(["Time (seconds)", "FPS"])
    try:
        main(writer)
    finally:
        csvfile.close()


