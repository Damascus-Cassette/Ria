import os
import numpy as np

os.system('color')

ENDC      = '\033[0m'
OKBLUE    = '\033[94m'
BLINKING  = '\033[9m'
    #Doesnt work in vscode terminol

## Overlaying two arrays
# a = np.full((8, 8), '', dtype='S1')
# a = np.full((8, 8), '', dtype=np.dtypes.StringDType())
# a = np.full((8, 8), '',              dtype= np.dtypes.ObjectDType())

a =       np.full((8, 8), '',   dtype= np.dtypes.StringDType())
a_color = np.full((8, 8), ENDC, dtype= np.dtypes.StringDType())


b =       np.full((8, 8), '',   dtype= np.dtypes.StringDType())
b_color = np.full((8, 8), ENDC, dtype= np.dtypes.StringDType())
    #Could merge these two a [8,8,2] shape

a[0,0] = 'a'
b[1,1] = 'b'
b_color[1,1] = BLINKING
 
# NP roll for offsetting object position:
b       = np.roll(b       , shift = (0,0))
b_color = np.roll(b_color , shift = (0,0))

#Overlaying:
mask      = a!=''
res       = np.where(mask,a,b)
res_color = np.where(mask,a_color,b_color)

#Testing creating colors
res_color[0,0]    = OKBLUE
res_color_compare = np.roll(res_color, shift = 1,) #axis =1)
color_dif_mask    = np.where(res_color != res_color_compare, f'{ENDC}'+ res_color, '')

b = color_dif_mask + res
b = np.where(b=='',' ',b)
# out = str(np.concatenate(b,axis=0).tobytes())
# a = np.column_stack((b,np.repeat(['\n'], b.shape[0])[:,None])).tostring()
# print(b)

# for row in b:
#     print(''.join(list(row)))



#### TESTING DRAWING LINKS:

import math


def solve_curve_points(
         a_pos    : tuple[int,int] , 
         b_pos    : tuple[int,int] ,
         a_handle : tuple[int,int] = None,
         b_handle : tuple[int,int] = None,
         ) ->  list[tuple[int,int]]:
    ''' Find path a->b and place sampling points to solve, dumb-dumb default is using handles '''
    res = []
    assert a_handle is not None
    assert b_handle is not None

    return [a_pos, a_handle, b_pos, b_handle]

def solve_shader(
         points   : list[tuple[int,int]],
         np_array : np.array
         )->np.array:
    ''' Interpret points, place asci characters w/a in np_array and return. Typically for actual shader not point incriment '''
    
    ''' Yeah this whole thing is kinda stupid. Instead snap to closes points that intercept?'''

    an0 = tuple(np.subtract(points[ 0], points[ 1]))
    bn0 = tuple(np.subtract(points[-1], points[-2]))
    points.insert(0,an0)
    points.insert(-1, bn0)
    #Extrapolate handles for shader's deg solver
    
    for index,pos in enumerate(points[1:-2]):
        index = index + 1
        _t_prev = points[index-1]
        _t_next = points[index+1]
        # degr  = calculate_angle(_prev,pos,_next)

        _prev = _t_prev
        _pos  = pos
        _next = _t_next


        degr = calculate_angle(_prev,_pos,_next)
        step = angle_to_step[round(degr / 45) * 45]
        char = sample_chart(degr,index,'?')

        i = 0
        while not np.all(_pos == _t_next):
            print(_pos)
            if i > 999: raise Exception('What are you doing step-line?')
            i  += 1

            _next = np.add(_pos, step)
            np_array[_pos] = char

            degr = calculate_angle(_prev,_pos,_next)
            if degr != 0:
                print('DEGR:',degr)
                raise 
                step = angle_to_step(round(degr / 45) * 45)
            else: step = angle_to_step[45]
            char = sample_chart(degr,i,'?')
        
            _prev = _pos
            _pos  = _next

        return np_array    
            


def sample_chart(degr:float|int, index:int, fallback:str):
    for (l,h),v in chart.items():
        if (degr >= l) and (degr <= h):
            return v[index%len(v)]
    return fallback


#IK This is super fucking stupid:
angle_to_step   = {
    0   : ( 0 ,  1) ,
    45  : ( 1 ,  1) ,
    90  : ( 0 ,  1) ,
    135 : (-1 ,  1) ,
    180 : (-1 ,  0) ,
    235 : (-1 , -1) ,
    280 : ( 0 , -1) ,
    325 : ( 1 , -1) ,
    360 : ( 0 ,  1) ,
}

chart = {
    (337.5 , 360  ) : '#',
    (-22.5 , 22.5 ) : '#',
    (22.5  , 67.5 ) : '#',
    (67.5  , 112.5) : '#',
    (112.5 , 157.5) : '#',
    (157.5 , 202.5) : '#',
    (202.5 , 247.5) : '#',
    (247.5 , 292.5) : '#',
    (292.5 , 337.5) : '#',
}


def calculate_angle(_prev,pos,_next):
    v1  = np.subtract(pos   , _prev)
    v2  = np.subtract(_next , pos  )


    if np.all(v1 == (0,0)) or np.all(v2 == (0,0)): 
        return (0,0)

    nv1 = normalize_2vec(v1)

    nv2 = normalize_2vec(v2)
    
    dot = np.dot(v1,v2)
    cos = np.divide(dot , (np.dot(nv1,nv2)))
    rad = np.arccos(cos)
    deg = np.deg2rad(rad)

    return np.nan_to_num(deg)
    # if deg == np.nan:
    #     return 0
    # cos_angle  = (min(max(x,+1),-1) for x in cos_angle)
    # acos_angle = (math.acos(x)      for x in cos_angle)
    # degr_angle = (math.degrees(x)   for x in acos_angle)
    return deg


def normalize_2vec(vec):
    sum_sq = sum(x**2 for x in vec)
    mag    = math.sqrt(sum_sq)
    if mag == 0: 
        return [0]*len(vec)
    normalized = [x / mag for x in vec]
    return normalized

#TEST:
# board = np.full((8, 8), '',   dtype= np.dtypes.StringDType())
# res = solve_shader([(1,3),(5,5)],a)
# print(res)


def bresenham(x0, y0, x1, y1):
    '''https://github.com/encukou/bresenham/blob/master/bresenham.py'''
    dx = x1 - x0
    dy = y1 - y0

    xsign = 1 if dx > 0 else -1
    ysign = 1 if dy > 0 else -1

    dx = abs(dx)
    dy = abs(dy)

    if dx > dy:
        xx, xy, yx, yy = xsign, 0, 0, ysign
    else:
        dx, dy = dy, dx
        xx, xy, yx, yy = 0, ysign, xsign, 0

    D = 2*dy - dx
    y = 0

    for x in range(dx + 1):
        yield x0 + x*xx + y*yx, y0 + x*xy + y*yy
        if D >= 0:
            y += 1
            D -= 2*dx
        D += 2*dy

