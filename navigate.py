import math

# Return a list of coordinates for the path between these src and dst
# src and dst are tuples of (x,y)

# TODO: Fix the diagonal hop for make_path_2d((0,0), (10,2))
def make_path_2d(src, dst):
    dx = dst[0] - src[0]
    dy = dst[1] - src[1]
    path = []

    if dx != 0:
        vertical = False
        slope = dy/dx
        b = src[1] - slope*src[0]
    else:
        vertical = True

    if math.fabs(dx) > math.fabs(dy):

        # xstep shows whether we are moving foward or backwards on the x-axis
        xstep = 1
        if src[0] > dst[0]:
            xstep = -1

        path = [src]
        # good old y = mx + b
        while path[-1][0] != dst[0]:
            nextx = path[-1][0] + xstep
            nexty = math.floor(slope * nextx + b)
            path.append((nextx, nexty))

    else:
        # ystep shows whether we are moving foward or backwards on the y-axis
        ystep = 1
        if src[1] > dst[1]:
            ystep = -1

        path = [src]
        # good old x = (y-b)/m
        while path[-1][1] != dst[1]:
            x,y = path[-1][0], path[-1][1]
            nexty = y + ystep
            if vertical:
                nextx = x
            else:
                nextx = math.ceil((y-b)/slope)
            path.append((nextx, nexty))

    if path[-1][0] != dst[0] or path[-1][1] != dst[-1]:
        path.append(dst)

    return path

def distance_formula(p1, p2):
    return int(math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2))
