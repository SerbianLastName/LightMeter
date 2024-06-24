# STANDARD LIBRARIES
from machine import Pin, I2C, SoftI2C
import utime as time
import _thread
from veml7700autoAdjust import setBestValues

# 3RD PARTY LIBRARIES
import veml7700
import ssd1306

# DISPLAY
displayi2c = SoftI2C(sda=Pin(16), scl=Pin(17))
display = ssd1306.SSD1306_I2C(128, 64, displayi2c)

# LIGHT SENSOR
sensori2c = SoftI2C(sda=Pin(21), scl=Pin(22))
vemlSettings = [100, 1/8]
veml = veml7700.VEML7700(address=0x10, i2c=sensori2c, it=vemlSettings[0], gain=vemlSettings[1])

# ROTARY ENCODER 
# DON'T FORGET 10K RESISTORS AND REVERSE -/+
rotarySwPin = Pin(34, Pin.IN)
rotaryDtPin = Pin(35, Pin.IN)
rotaryClkPin = Pin(32, Pin.IN)

# CONSTANTS
SETTINGS = [100,200,400,800,1600,3200,6400,128000], ["60", "30", "15", "5", "2.5", "1", "1/2", "1/4", "1/12", "1/24", "1/30", "1/48", "1/50", "1/60", "1/125", "1/500", "1/1,000", "1/1,250", "1/2,500", "1/5,000", "1/10,000"], [1.8, 2.8, 4, 5.6, 8, 11, 22]
SHUTTER_SPEEDS = [60, 30, 15, 5, 2.5, 1, 1/2, 1/4, 1/12, 1/24, 1/30, 1/48, 1/50, 1/60, 1/125, 1/500, 1/1000, 1/1250, 1/2500, 1/5000, 1/10000]
SETTINGS_LABELS = ["ISO - ", "SS - ", "F"]
MAIN_MENU = 0
SELECT_MENU = 1
ADJUST_MENU = 2

# VARIABLES
lastClick = 0
lastClickTime = time.ticks_ms()
lastStatus = (rotaryDtPin.value() <<1 | rotaryClkPin.value())
lastStatusTime = time.ticks_ms()
lastInput = time.ticks_ms()
currentSelection = 0
currentValues = [0,13,1]
menuState = MAIN_MENU



def drawDisplay(lightIntake):
    display.fill(0)
    display.fill_rect(0,46,128,64,1)
    display.text("LIN - " + str(lightIntake), 5, 4, 1)
    for x in range(len(currentValues)):
        if menuState == SELECT_MENU and currentSelection == x:
            display.text("> " + str(SETTINGS_LABELS[x]) + str(SETTINGS[x][currentValues[x]]), 4, 17 + (x * 10), 1)
        elif menuState == ADJUST_MENU and currentSelection == x:
            display.fill_rect(0, 15 + (x*10),128,10,1)
            display.text("> " + str(SETTINGS_LABELS[x]) + str(SETTINGS[x][currentValues[x]]) + " <", 4, 17 + (x * 10), 0)
        else:
            display.text(str(SETTINGS_LABELS[x]) + str(SETTINGS[x][currentValues[x]]), 4, 17 + (x * 10), 1)
    display.show()

def checkMenuDelay():
    global menuState
    if abs(time.ticks_diff(time.ticks_ms(), lastInput)) > 7500:
        menuState = MAIN_MENU

def run():
    global vemlSettings
    global veml
    while True:
        lux = veml.read_lux()
        newVemlSettings = setBestValues(lux, vemlSettings[0], vemlSettings[1])
        if newVemlSettings != vemlSettings:
            vemlSettings = newVemlSettings
            veml = veml7700.VEML7700(address=0x10, i2c=sensori2c, it=newVemlSettings[0], gain=newVemlSettings[1])
            lux = veml.read_lux()
        lightSensitivity = SETTINGS[0][currentValues[0]] * SHUTTER_SPEEDS[currentValues[1]] / SETTINGS[2][currentValues[2]]
        lightIntake = round(lux * lightSensitivity / 10, 2)
        drawDisplay(lightIntake)
        checkMenuDelay()
        time.sleep(0.1)

def doClick():
    global menuState
    global lastInput
    lastInput = time.ticks_ms()
    if menuState == MAIN_MENU:
        menuState = SELECT_MENU
        return
    if menuState == SELECT_MENU:
        menuState = ADJUST_MENU
        return
    if menuState == ADJUST_MENU:
        menuState = SELECT_MENU
        return
    pass

def incrimentList(listLen, currentVal, up):
    if up:
        if currentVal < listLen -1:
            return currentVal + 1
        return 0
    if not up:
        if currentVal >= 1:
            return currentVal - 1
        return listLen -1

def doSpin(up):
    global currentSelection
    global currentValues
    global lastInput
    lastInput = time.ticks_ms()
    if menuState == MAIN_MENU:
        return
    if menuState == SELECT_MENU and up:
        currentSelection = incrimentList(3, currentSelection, True)
    if menuState == SELECT_MENU and not up:
        currentSelection = incrimentList(3, currentSelection, False)
    if menuState == ADJUST_MENU and up:
        currentValues[currentSelection] = incrimentList(len(SETTINGS[currentSelection]), currentValues[currentSelection], True)
    if menuState == ADJUST_MENU and not up:
        currentValues[currentSelection] = incrimentList(len(SETTINGS[currentSelection]), currentValues[currentSelection], False)
    pass

def handleClick(pin):
    global lastClick
    global lastClickTime
    newClick = rotarySwPin.value()
    if lastClick == newClick:
        return
    now = time.ticks_ms()
    if abs(time.ticks_diff(lastClickTime, now)) <= 250:
        return
    transition = (lastClick << 2 ) | newClick
    if transition == 0b01:
        lastClickTime = now
        doClick()
        return
    lastClick = newClick 
    time.sleep(0.15)



def handleSpin(pin):
    global lastStatus
    global lastStatusTime    
    newStatus = (rotaryDtPin.value() << 1 | rotaryClkPin.value())
    if newStatus == lastStatus:
        return
    now = time.ticks_ms()
    if abs(time.ticks_diff(lastStatusTime, now)) <= 150:
        return
    transition = (lastStatus << 2 ) | newStatus
    lastStatus = newStatus  
    if transition == 0b1000 or transition == 0b0111:
        lastStatusTime = now
        doSpin(True)
        return
    if transition == 0b1011 or transition == 0b0100:
        lastStatusTime = now
        doSpin(False)
        return


rotarySwPin.irq(handler=handleClick, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)
rotaryClkPin.irq(handler=handleSpin, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)
rotaryDtPin.irq(handler=handleSpin, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)
        
run()
