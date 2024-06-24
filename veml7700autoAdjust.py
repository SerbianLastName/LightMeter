def setBestValues(lux, it, gain):
    newIt = it
    newGain = gain
    if lux < 100:
        if gain == 1/8:
            newGain = 1/4
        elif gain == 1/4:
            newGain = 1
        elif gain == 1:
            newGain = 2
        else:
            if it == 100:
                newIt = 200
            elif it == 200:
                newIt = 400
            else:
                newIt = 800
    if lux > 100:
        newIt = 100
        newGain = 1/8
        if lux >= 30000 and lux < 60000:
            newIt = 50
        elif lux >= 60000:
            newIt = 25
        else:
            pass
    return [newIt, newGain]