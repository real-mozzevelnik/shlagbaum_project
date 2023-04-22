from random import randint, shuffle
from string import ascii_letters

def generate_password():
    password = ''
    for i in range(7):
        password = password + str(randint(0, 9))
        password = password + ascii_letters[randint(0, len(ascii_letters)-1)]
    password = list(password)
    shuffle(password)
    
    return ''.join(password)

print(generate_password())