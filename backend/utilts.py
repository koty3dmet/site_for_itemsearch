import random
num = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]
sym = ['a', 'b', 's', 'd', 'e', 'f', 'h', 'y', 'z', 'w', 'r', 'k', 'l']
def gen_UID():
    s = ''
    for _ in range(8):
        s+=str(random.choice(random.choice([num, sym])))
        
    return s

for _ in range(10):
    a = gen_UID()
    print(a)