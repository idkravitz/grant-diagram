from PyQt4 import QtCore

class CountHours(object):
    def __init__(self):
        self.hours = 0

    @classmethod
    def hoursBetween(cls, begin, end):
        b = QtCore.QDateTime.fromString(begin, QtCore.Qt.ISODate)
        e = QtCore.QDateTime.fromString(end, QtCore.Qt.ISODate)

        days = b.daysTo(e)
        weeks = days // 7
        days -= weeks * 2 + 1

        if b.date().dayOfWeek() > e.date().dayOfWeek():
            days -= 2

        # hours from not full days, working time is 8:00 - 16:00
        additional = (16 - b.time().hour()) + (e.time().hour() - 8)
        return days * 8 + additional

    def step(self, begin, end):
        self.hours += self.hoursBetween(begin, end)

    def finalize(self):
        return self.hours
