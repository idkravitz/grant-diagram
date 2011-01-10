import time, sys, io
from math import ceil

from PyQt4 import QtCore
from grant_core.CountHours import CountHours

def cssSafe(s):
    # names might have a space in them, so replace spaces with '-'
    return s.replace(' ', '-')

class Task(object):
    tasks = {}
    def __init__(self, id, title, hours, status):
        self.id = id
        self.title = title
        self.hours = hours
        self.status = status
        self.depends = []
        self.depended = []
        self.begin = None
        self.end = None

    @classmethod
    def connect(cls, task, depends):
        cls.tasks[task].depends.append(depends) # depends on
        cls.tasks[depends].depended.append(task) # other depends on us

    def set_hours(self, begin, end):
        self.begin = begin
        if self.status == 'finished':
            self.end = end + begin
        else:
            self.end = begin + max(end, self.hours)

    def time_traversal(self):
        for d in self.depends:
            self.tasks[d].time_traversal()
        if self.begin is None:
            if len(self.depends) == 0:
                self.begin = 0
            else:
                self.begin = max(self.tasks[p].end for p in self.depends)
        if self.end is None:
            self.end = self.begin + self.hours

    @classmethod
    def lowestDepended(cls):
        return [t for t in cls.tasks.values() if len(t.depended) == 0]

    def __lt__(self, other):
        return self.begin < other.begin or (self.begin == other.begin and self.end < other.end)

class GanttGenerator(object):
    def __init__(self, project_id):
        Task.tasks = {}
        tasks = app.session.get_tasks_for_gantt(project_id)
        if len(tasks) == 0:
            return
        independed = set({})
        for id, title, hours, status in tasks:
            t = Task(id, title, hours, status)
            Task.tasks[id] = t
            independed.add(id)
        deps = app.grant.get_available_tasks_dependencies(tasks[0][0])
        for task, depends in deps:
            if task in independed:
                independed.remove(task)
            Task.connect(task, depends)
        activs = app.grant.get_activities_for_gantt(project_id)
        b, e = app.grant.get_project_info_for_gantt(project_id)
        for task, begin, end in activs:
            hbegin = CountHours.hoursBetween(b, begin)
            hend = CountHours.hoursBetween(begin, end)
            Task.tasks[task].set_hours(hbegin, hend)
        low = Task.lowestDepended()
        for task in low:
            task.time_traversal()
        self.end = max(t.end for t in low)
        self.end = max(self.end, CountHours.hoursBetween(b, e))
        bdt = QtCore.QDateTime.fromString(b, QtCore.Qt.ISODate)

        self.start = bdt

    def dumpGantt(self):
        if len(Task.tasks) == 0:
            return ""

        f = io.StringIO()
        styles = []
        style_key = []

        max_week = ceil(self.end / 7)
        for status in ('active', 'delayed', 'finished'):
            style_key.append('<td width="30%" class="{0}">{0}</td>'.format(status))
        print('''
        <style>
        table {border-collapse: collapse; padding:0}

        tr {border: 0; padding:0}

        th {text-align: right; border: 0; padding:1; margin:0}
        th.normal {background-color: #ddd}
        th.altweek {background-color: #bbb}

        td { color: white; border-bottom: thin solid white; padding:1; margin:0}
        td.normal {background-color: #ddd}
        td.altweek {background-color: #bbb}
        td.finished {background-color: red}
        td.active {background-color: green}
        td.delayed {background-color: #f60}
        </style>
        ''', file=f)
        print('<table>', file=f)
        print('<tr><th>Task</th>', file=f)

        for week in range(0, max_week + 1):
            style = week % 2 and 'normal' or 'altweek'
            mark = self.start.addDays(week * 7)
            print('<th class="{0}" colspan="40">{1:02}/{2}</th>'.format(style, mark.date().day(),
                QtCore.QDate.shortMonthName(mark.date().month())), file=f)
        print('''</tr>''', file=f)

        l = Task.tasks.values()
        for task in sorted(l):
            print('<tr><th nowrap>{0}</th>'.format(task.title), file=f)
            begin = task.begin
            end = task.end

            span = 0
            pstyle = None
            for week in range(0, max_week + 1):
                for hour in range(0, 40):
                    if begin <= (week * 40 + hour) < end:
                        style = task.status
                    else:
                        style = week % 2 and 'normal' or 'altweek'

                    if pstyle is None:
                        pstyle = style
                        span += 1
                    elif style == pstyle:
                        span += 1

                    else:
                        print('<td class="{0}" colspan="{1}"></td>'.format(pstyle, span), file=f)
                        span = 1
                        pstyle = style
            print('<td class="{0}" colspan="{1}">&nbsp;</td>'.format(pstyle, span), file=f)
            print('</tr>', file=f)

        print('''
        </table>
        <table width="90%" align="center">
        <tr>
        {0}
        </tr>
        </table>
        '''.format('\n'.join(style_key)), file=f)
        open('gantt.html', 'w').write(f.getvalue())
        return f.getvalue()

