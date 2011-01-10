import time, sys

def cssSafe(s):
    # names might have a space in them, so replace spaces with '-'
    return s.replace(' ', '-')

class GanttGenertor(object):
    def __init__(self):
        pass

    def dumpGantt(self, start=time.time(), f=sys.stdout):
        styles = []
        style_key = []
        i = 0
        for person in self.people:
            if person.weeks:
                max_week = max(person.weeks.keys())
            else:
                max_week = 0
            safe = cssSafe(person.name)
            colour = person.colour
            styles.append('td.%s {background-color: %s}'%(safe, colour))
            style_key.append('<td width="30%%" class="%s">%s</td>'%(safe,
                person.name))
            i += 1

        print >>f, '''
        <style>
        table {border-collapse: collapse; padding:0}

        tr {border: 0; padding:0}

        th {text-align: right; border: 0; padding:1; margin:0}
        th.normal {background-color: #ddd}
        th.altweek {background-color: #bbb}

        td {color: white; border-bottom: thin solid white; padding:1; margin:0}
        td.normal {background-color: #ddd}
        td.altweek {background-color: #bbb}
        %s
        </style>
        '''%'\n'.join(styles)
        print >>f, '<table>'
        print >>f, '<tr><th>Task</th>'

        ONE_WEEK = 7*24*60*60
        for week in range(0,max_week + 1):
            style = week%2 and 'normal' or 'altweek'
            print >>f, '<th class="%s" colspan="5">%s</th>'%(style,
                time.strftime("%d/%b",time.localtime(start + week*ONE_WEEK))
                )
        print >>f, '''</tr>'''

        l = self.tasks.values()
        l.sort(lambda a,b:cmp(a.days, b.days))
        for task in l:
            print >>f, '<tr><th nowrap>%s : %s</th>'%(task['group'],
                task['task'])
            days = task.days
            days.sort()
            day_dict = {}
            for day in days:
                day_dict[day] =1

            span = 0
            pstyle = None
            for week in range(0, max_week+1):
                for day in range(0,5):
                    if day_dict.has_key((week,day)):
                        style = cssSafe(task.person.name)
                    else:
                        style = week%2 and 'normal' or 'altweek'

                    if pstyle is None:
                        pstyle = style
                        span += 1
                    elif style == pstyle:
                        span += 1

                    else:
                        print >>f, '<td class="%s" colspan="%d">%s</td>'%(
                            pstyle, span, '')
                        span = 1
                        pstyle = style
            print >>f, '<td class="%s" colspan="%d">&nbsp;</td>'%(pstyle, span)
            print >>f, '</tr>'

        print >>f, '''
        </table>
        <table width="90%%" align="center">
        <tr>
        %s
        </tr>
        </table>
        '''%'\n'.join(style_key)

