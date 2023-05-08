# Generating random Load profil.
import random


def Load(r, P_max):

    Profile = {}
    for i in range(0, r-1):
        Profile[i] = random.randrange(0.2*P_max, 0.9*P_max)
    return Profile
