from matrixbase import MatrixBase
from rgbmatrix import graphics
import time
from datetime import datetime

import python_weather
import asyncio

import urllib.request


#globals
EXTERNALIP = urllib.request.urlopen('https://ident.me').read().decode('utf8')
WEATHER = None

async def getweather():
    while True:
        # declare the client. format defaults to the metric system (celcius, 
        # km/h, etc.)
        async with python_weather.Client(format=python_weather.IMPERIAL) as client:

            # fetch a WEATHER forecast from a city
            global WEATHER
            WEATHER = await client.get("@" + EXTERNALIP)
            
            # get the WEATHER forecast for a few days
            # for forecast in WEATHER.forecasts:
            #   print(forecast)
        
            #   # hourly forecasts
            #   for hourly in forecast.hourly:
            #     print(f' --> {hourly}')

            await asyncio.sleep(10)


class rgbGen():
    rgbVal = [0, 0, 0]
    incColor = 0
    decColor = 0
    
    def __init__(self):
        self.rgbVal = [255, 0, 0]
        self.incColor = 1
        self.decColor = 0


    def update(self):
        if(self.rgbVal[self.incColor] == 255 
           or self.rgbVal[self.decColor] == 0):
            self.incColor = (self.incColor + 1) % 3
            self.decColor = (self.decColor + 1) % 3
        
        self.rgbVal[self.incColor] += 1
        self.rgbVal[self.decColor] += -1

        return self.rgbVal
        
        
    def get(self):
        return self.rgbVal    




class clockMatrix(MatrixBase):
    rgb = rgbGen()

    canvas = None

    timeFont  = graphics.Font()
    timeFont.LoadFont("fonts/LodeSans-15.bdf")
    timeColor = graphics.Color(255, 255, 255)

    dateFont  = graphics.Font()
    dateFont.LoadFont("fonts/4x6.bdf")
    dateColor = graphics.Color(255, 255, 255)

    tempFont  = graphics.Font()
    tempFont.LoadFont("fonts/LodeSans-15.bdf")
    tempColor = graphics.Color(255, 255, 255)
    tempText  = "N/A"

    tickerFont = graphics.Font()
    tickerFont.LoadFont("fonts/5x8.bdf")
    tickerColor = graphics.Color(255, 255, 255)
    tickerPos = 0;

    tickerText = "Weather"
    timeText = datetime.now().strftime("%H:%M:%S")
    dateText = datetime.now().strftime("%b %-d")

    tlastDraw = 0
    tlastClockTimeGet = 0
    tlastTickerPosUpd = 0
    tickerLen = 0


    def __init__(self, *args, **kwargs):
        super(clockMatrix, self).__init__(*args, **kwargs)
        
        
        if (not self.process()):
            self.print_help()

        self.canvas = self.matrix.CreateFrameCanvas()
        self.tickerPos = self.canvas.width


    async def update(self):

        self.tNow = time.time()
        
        # Clock update condition
        if(self.tNow - self.tlastClockTimeGet > 1.0):
            self.timeText = datetime.now().strftime("%H:%M:%S")
            self.dateText = datetime.now().strftime("%b %-d").upper()
            self.yearText = datetime.now().strftime("%Y")
            
            if(WEATHER is not None):
                self.tempText = str(WEATHER.current.temperature) + "F"

            self.tlastClockTimeGet = self.tNow
        
        if(self.tNow - self.tlastTickerPosUpd > 0.05):
            # handle ticker pos
            self.tickerPos -= 1
            # handle screen wrap
            if (self.tickerPos + self.tickerLen < 0):
                self.tickerPos = self.canvas.width 
                #update ticker text when offscreen
                if(WEATHER is not None):
                    self.tickerText = (f"{WEATHER.current.description} "
                                       f"RH:{WEATHER.current.humidity}%")
            
            self.tlastTickerPosUpd = self.tNow
        
        # Draw condition
        if(self.tNow - self.tlastDraw > 0.01):
            self.canvas.Clear()
            
            #update the RGB value
            rgbVal = self.rgb.update()
            rgbColor = graphics.Color(rgbVal[0], rgbVal[1], rgbVal[2])
                
            # draw time
            graphics.DrawText(self.canvas, self.timeFont, 2, 11, self.timeColor, 
                              self.timeText)

            #draw Date
            graphics.DrawText(self.canvas, self.dateFont, 6, 17, self.dateColor, 
                              self.dateText)
            graphics.DrawText(self.canvas, self.dateFont, 10, 23, 
                              self.dateColor, self.yearText)
            
            
            # draw WEATHER
            if(WEATHER is not None):
                graphics.DrawText(self.canvas, self.tempFont, 37, 22, 
                                  self.tempColor, self.tempText)

                # draw ticker
                self.tickerLen = graphics.DrawText(self.canvas, self.tickerFont, 
                                                  self.tickerPos, 30, 
                                                  self.tickerColor, 
                                                  self.tickerText)


            #update border
            graphics.DrawLine(self.canvas, 0,  0, 63, 0, rgbColor)
            graphics.DrawLine(self.canvas, 63, 0, 63, 31, rgbColor)
            graphics.DrawLine(self.canvas, 63, 31, 0, 31, rgbColor)
            graphics.DrawLine(self.canvas, 0,  31, 0, 0, rgbColor)

            self.tlastDraw = self.tNow
            self.canvas = self.matrix.SwapOnVSync(self.canvas)

        await asyncio.sleep(0.001)



    async def run(self):
        while True:
            await self.update()


# Main function
if __name__ == "__main__":
    
    clkMatrix = clockMatrix()

    loop = asyncio.get_event_loop()
    loop.create_task(clkMatrix.run())
    loop.create_task(getweather())
    loop.run_forever()

