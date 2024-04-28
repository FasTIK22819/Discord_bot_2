import csv
line = 0
ctx_p = ''
ctx_f = ''
with open('musics.csv', mode='r', encoding='utf-8') as m_file:
    file_reader = csv.reader(m_file)
    len_sp = sum(1 for rows in file_reader)
