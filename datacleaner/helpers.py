from random import randint

def parseCSV(csv_file):
    header = list()
    csv_data = list()
    data = csv_file.read().decode('utf-8')
    lines = data.split('\n')
    i = 0
    for line in lines:
        fields = line.split(',')
        if i == 0:
            for field in fields:

                header.append(field)
        else:
            data_line = list()
            for val in fields:
                field = dict()
                field.update({'cellValue': val})
                field.update({'dirtiness': randint(0,10)})
                data_line.append(field)
            csv_data.append(data_line)
        i += 1
        print(i)
    return header, csv_data
