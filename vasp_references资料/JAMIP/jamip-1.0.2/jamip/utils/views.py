from collections import OrderedDict

def shellform(data):
    Info = OrderedDict()

    for item in data:
        for key,value in item.items():
            if key not in Info:
                Info[key] = []
            Info[key].append(len(str(value)))

    for key in Info:
        Info[key] = max(max(Info[key]), len(key))
    if 'prior' in Info:
        Info.move_to_end('path')

    def printGroup(group):
        for item in group:
            for i,key in enumerate(Info):
                icon = '|'
                itemLen = Info[key] + 2
                if key not in item:
                    s = '--'.center(itemLen,' ')
                elif item[key] == '-':
                    s = str(item[key]).center(itemLen, '-')
                    icon = '+'
                else:
                    s = str(item[key]).center(itemLen, ' ')
    
    
                s = (icon if i == 0 else '') + s + icon
                print(s,end='')
            print('')
    
    print('\033[0;32;40mJump2 Tasks Check Mode\033[0m')

    tag = {}
    for key in Info:
        tag[key] = '-'
    data.insert(0, tag)
    data.append(tag)

    printGroup([tag])

    for i,key in enumerate(Info):
        if i == 0:
            s = '|' + key.center(Info[key]+3)[1:] + '|'
        else:
            s = key.center(Info[key]+2) + '|'
        print(s,end='')

    print('')
    printGroup(data)
