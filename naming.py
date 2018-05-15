import random

nouns = []
with open('nouns.txt', 'r') as fp:
    for line in fp:
        nouns.append(line.strip().title())

adjectives = []
with open('adjectives.txt', 'r') as fp:
    for line in fp:
        adjectives.append(line.strip().title())

def get_random_name():
    number = random.randrange(1, 100)
    noun = random.choice(nouns)
    return noun + str(number)

def get_random_ship_name():
    adjective = random.choice(adjectives).title()
    noun = random.choice(nouns).title()
    return "SS {}{}".format(adjective, noun)

