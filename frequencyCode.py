import numpy as np

def frequency(r1,theta,r2)  :
    #surface fit for frequency on radial disk with 2 supports
    #r1 refers to the distance from center of the first support (0-.9)
    #theta is the angle between the supports (from center) (0 - pi)
    #r2 is the distance from center to the second support (0-.9)

    frequency = (140.93-r1*25)+(-7.458*r1+9.1185)*theta+(-170)*r2+\
                (5.783*r1-10.367)*theta**2+(-8.1)*theta*r2+(117)*r2**2+\
                (4.2)*theta**3+(-28.075*r1+31.5125)*theta**2*r2+(15.63*r1-2.26)*theta*r2**2+\
                (-.7)*theta**4+(-.35)*theta**3*r2+(21.77*r1-27.862)*theta**2*r2**2

    return frequency
