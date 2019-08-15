from random import randint
from tqdm import tqdm
import pprint

def parseCSV(csv_file):
    header = list()
    relationships = dict()
    csv_data = list()

    data = csv_file.read().decode('utf-8-sig')
    lines = data.split('\n')
    count = 0
    maxOccurence = 1
    for line in tqdm(lines):
        fields = line.split(',')
        if count == 0:
            for field in fields:
                header.append(field)
        else:
            data_line = list()
            for i in range(0, len(fields)):
                field = dict()
                field.update({'cellValue': fields[i]})
                field.update({'dirtiness': -1})
                data_line.append(field)
                for j in range(0, len(fields)):
                    if i != j:
                        if (header[i], fields[i]) not in relationships.keys():
                            relationships[(header[i], fields[i])] = dict()
                            relationships[(header[i], fields[i])][(header[j], fields[j])] = 1
                        elif (header[j], fields[j]) not in relationships[(header[i], fields[i])].keys():
                            relationships[(header[i], fields[i])][(header[j], fields[j])] = 1
                        else:
                            relationships[(header[i], fields[i])][(header[j], fields[j])] += 1
                            if relationships[(header[i], fields[i])][(header[j], fields[j])] > maxOccurence:
                                maxOccurence = relationships[(header[i], fields[i])][(header[j], fields[j])]
            csv_data.append(data_line)
        count += 1
    pprint.pprint(relationships)
    return header, csv_data, relationships, maxOccurence

#def parseCSV(csv_file):
#    header = list()
#    csv_data = list()
#    data = csv_file.read().decode('utf-8')
#    lines = data.split('\n')
#    i = 0
#    for line in lines:
#        fields = line.split(',')
#        if i == 0:
#            for field in fields:
#
#                header.append(field)
#        else:
#            data_line = list()
#            for val in fields:
#                field = dict()
#                field.update({'cellValue': val})
#                #field.update({'dirtiness': randint(0,10)})
#                field.update({'dirtiness': -1})
#                data_line.append(field)
#            csv_data.append(data_line)
#        i += 1
#        print(i)
#    return header, csv_data
