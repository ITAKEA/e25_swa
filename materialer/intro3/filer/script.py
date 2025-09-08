

f = open('info.txt', 'r')

with open('info2', 'w') as f:
    f.write('hello from context manager')


print('filen er  lukket')