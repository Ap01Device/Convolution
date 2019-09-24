ages = {'Aurio': 10, 'Bill': 30, 'David': 100}

name = input('Who are you look up?')

try:
    print(f'{name} is {ages[name]} years old')
except KeyError:
    print(f'Sorry, {name} is not in the dictionary')
