startYear = 18
dayToIndexRatio = 1 / (4 * 24)
indexToDayRatio = 4 * 24


# FIXME!!! THIS CODE IS SUUUUPER inefficient somehow. It makes the entire program almost unusable


def getDaysInYear(year):
    if year % 4 == 0:
        daysInYear = 366
    else:
        daysInYear = 365
    return daysInYear


def dateToIndex(year, month, day, startYear):
    # calculates the number of days since October 1, start year (2018)
    # will not work properly for any dates prior to that

    # year, month, day = date.split("-")
    year = int(year)
    month = int(month)
    day = int(day)

    index = -1

    if year % 4 == 0:  # if it is a leap year
        monthToDays = {1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    else:
        monthToDays = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    # print(index)
    monthVal = int(month)
    if startYear == year:
        # print(index)

        # then just calculate the day it is in the year and subract 304
        for preMonth in range(10, monthVal):  # add the previous months
            index += monthToDays[preMonth]

        index += day  # add the days

        return index

    elif year > startYear:
        # add the residual from the first year
        for preMonth in range(10, 13):
            index += monthToDays[preMonth]

        startYear += 1
        # now treat as if we were calculating days since Jan 1, (startYear + 1)

        # add the years
        numYears = year - startYear
        currentYear = startYear
        for yearSinceStart in range(numYears):
            if currentYear % 4 == 0:
                daysInYear = 366
            else:
                daysInYear = 365
            currentYear += 1

            index = index + daysInYear

        # add the months
        if year % 4 == 0:  # if it is a leap year
            monthToDays = {1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
        else:
            monthToDays = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}

        monthVal = int(month)

        if monthVal > 1:
            for month in range(1, monthVal):  # don't include the current month because it isn't over yet!
                index = index + monthToDays[month]

        index = index + day

        return index


def indexToDatetime(index, startYear):
    # index must represent days since Oct 1, startYear

    # put everything back into the framework of normal years (Jan 1, startYear)
    if (startYear % 4) == 0:  # if it is a leap year
        monthToDays = {1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    else:
        monthToDays = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}

    for month in range(1, 10):
        index += monthToDays[month]
    index += 1
    currentIndex = 0

    timeIndex = index - int(index)

    index = int(index)
    startYear = int(startYear)

    year = startYear
    while currentIndex < index:
        daysInYear = getDaysInYear(year)
        currentIndex += daysInYear
        year += 1

    year = year - 1
    currentIndex = currentIndex - daysInYear

    if getDaysInYear(year) == 366:  # if it is a leap year
        monthToDays = {1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    else:
        monthToDays = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}

    month = 1
    while currentIndex < index:
        currentIndex += monthToDays[month]
        month += 1

    month = month - 1
    currentIndex -= monthToDays[month]

    day = 1
    while currentIndex < index:
        currentIndex += 1
        day += 1
    day = day - 1

    hour = int(timeIndex * 24)
    timeIndex = timeIndex - (hour / 24)
    minute = int(timeIndex * 24 * 60)
    timeIndex = timeIndex - ((minute / 24) / 60)
    second = int(timeIndex * 24 * 60 * 60)

    return year, month, day, hour, minute, second

def timeToIndex(hour, minute, second, index):
    # add hours
    index += int(hour) / 24
    # add minutes
    index += int(minute) / (24 * 60)
    # add seconds
    index += float(second) / (24 * 60 * 60)
    return index

def datetimeToIndex(year, month, day, hour, minute, second):
    index1 = dateToIndex(year, month, day, startYear)
    index = timeToIndex(hour, minute, second, index1)

    return index

startIndex = datetimeToIndex(str(startYear), "10", "01", "00", "00", "00")
startIndex = round(startIndex / dayToIndexRatio) * dayToIndexRatio

def getDaysInYear(year):
    #sees if it's a leap year or not
    if year % 4 == 0:
        daysInYear = 366
    else:
        daysInYear = 365
    return daysInYear

oldIndices = []
newIndices = []
numOff = 0
for i in range(0,600):
    index = i
    for j in range(int(1 / dayToIndexRatio)):

        year, month, day, hour, minute, second = indexToDatetime(index, startYear)

        date = str(year) + "-" + str(month) + "-" + str(day) + " " + str(hour) + ":" + str(minute) + ":" + str(second)

        if month == "13":
            print(month)
        newIndex = datetimeToIndex(year, month, day, hour, minute, second)

        newIndices.append(newIndex)
        oldIndices.append(index)
        if newIndex - index != 0:
            numOff += 1
