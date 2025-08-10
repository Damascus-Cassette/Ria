import os
import numpy as np

os.system('color')

ENDC      = '\033[0m'
OKBLUE    = '\033[94m'
BLINKING  = '\033[9m'
    #Doesnt work in vscode terminol

from typing import TypeAlias
import copy

## Overlaying two arrays
# a = np.full((8, 8), '', dtype='S1')
# a = np.full((8, 8), '', dtype=np.dtypes.StringDType())
# a = np.full((8, 8), '',              dtype= np.dtypes.ObjectDType())

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
 
# def offset(np_arrays:tuple[np.array],shift=(0,0)):
#     assert isinstance(np_arrays,(tuple,list))
#     res = []
#     for x in np_arrays:
#         if isinstance(x,tuple):
#             res.append(tuple((v+shift[i] for i,v in enumerate(x))))
#         else:
#             res.append( np.roll(x , shift = shift))
#     return res

# def set_effect(
#             effect_arrays:np.array  , 
#             effect       : str      , 
#             mask_src     : np.array = None, 
#             mask_value   : str      = ''  , ):
#     if not isinstance(effect_arrays,(list,tuple,set)):
#         effect_arrays = [effect_arrays]
#     for x in effect_arrays:
#         if   mask_src: mask = mask_src != mask_value
#         else         : mask = x        != mask_value
#         yield np.where(mask,b,b+=mask_value)


# def overlay(bases:tuple[np.array],overlays:tuple[np.array],mask_value = '',mask_from_first = True):
#     ''' Assumption of mask from first in iterable of bases and overlays for multi-datatype overlays '''
#     assert isinstance(bases,(tuple,list))
#     assert isinstance(overlays,(tuple,list))
#     res = []
    
#     if mask_from_first:
#         b,o  = zip(bases,overlays)[0]
#         mask = b!=mask_value

#     for b,o in zip(bases,overlays):
#         if not mask_from_first:
#             mask = b!=mask_value
#         res.append(np.where(mask,b,o))
    
#     return res

# def print_collapse(text_array    :np.array        ,
#                    color_array   :np.array        ,
#                    default_color :str       = ENDC)->list[str]:
#     color_compare  = np.roll (color_array, shift = 1,) #axis =1)
#     color_dif_mask = np.where(color_array != color_compare, f'{default_color}'+ color_array, '')

#     color_dif_mask + text_array
#     res = []
#     for row in np.where(text_array=='',' ',text_array):
#         res.append(''.join(list(row)))
#     return res

###

class point():
    x:float
    y:float

    def __init__(self,x,y):
        self.x = float(x)
        self.y = float(y) 
    
    def __iter__(self):
        yield self.x
        yield self.y
    
    def __add__(self,other):
        assert isinstance(other,(self.__class__,int,float))
        return self.__class__(*[v+other[i] for i,v in self])
    def __sub__(self,other):
        assert isinstance(other,(self.__class__,int,float))
        return self.__class__(*[v-other[i] for i,v in self])

class line():
    Fonts = {
        'regular' : 'a',
        'bold'    : 'A',
    }

    p1    : point
    p2    : point
    font  : str   = 'regular'   
    color : str   = ENDC 
        #string of character types, default is color-reset (white)
        #May want to make some palettes?


    def __init__(self,
                 p1    : point,
                 p2    : point,
                 color : str  = ENDC,
                 font  : str  = 'regular',):
        self.p1    = p1
        self.p2    = p2
        self.color = color
        self.font  = font

    def determine_line(self,np_array)->list[point]:
        return[point(x) for x in bresenham(*self.p1,*self.p2)]
    
    def shader(self,text,color,coords:list[point])->tuple[np.array,np.array]:
        ### Apply shader to coordinates
        _neg  = coords[0] - (coords[1] - coords[0]) 
        _post = coords[-1] + (coords[-1] - coords[-2])

        coords = copy.copy(coords)
        coords.insert( 0,_neg )
        coords.insert(-1,_post)

        color = color
        text  = text

        for i,pos in enumerate(coords[1:-2]):
            i=+1
            _prev =  coords[i-1] 
            _pos  =  pos
            _next =  coords[i+1]
            
            char  = self.determine_character(_prev,_pos,_next)
            col   = self.determine_color(_prev,_pos,_next)

            color[pos] = char
            text[pos ] = col
        return text, color

    def determine_character(self,_prev:point,_pos:point,_next:point):
        return self.Font[self.font]
    def determine_color    (self,_prev:point,_pos:point,_next:point):
        return self.color

from typing import Self

class sprite():
    ''' Viewed inside of instance, pipeline should be obj->sprite->sprite_view->obj-> '''
    text   : np.array
    color  : np.array
    lines  : list[line]

    def __init__(self, color_default = ENDC, size =(100,100),):
        self.text  = np.full(size, ''           , dtype= np.dtypes.StringDType())
        self.color = np.full(size, color_default, dtype= np.dtypes.StringDType())
        self.lines = []
    
    def offset   (self, shift : tuple|point):
        new_lines = []
        for x in self.lines:
            new_lines.append(x+shift)
        self.lines = new_lines

        self.text  = np.roll(self.text ,shift = tuple(*shift)) 
        self.color = np.roll(self.color,shift = tuple(*shift))

    def overlay  (self, 
                  other : Self         , 
                  mask_color    = ''   , 
                  mask_text     = ''   ,
                  overlay_color = True ,
                  overlay_text  = True , 
                  merge_lines   = True ):
        
        if overlay_text:
            text_mask  = self.text !=mask_text
            self.text  = np.where(text_mask,self.text,other.text)
        
        if overlay_color:
            color_mask = self.color!=mask_color
            self.color = np.where(color_mask,self.color,other.color)

        if merge_lines:
            self.lines.extend(other.lines)
    
    def __add__(self,other):
        new = copy.deepcopy(self)
        new.overlay(other)
        return new
    def __or__(self,other):
        new = copy.deepcopy(self)
        new.overlay(other)
        return new

    def set_color (self, ps:list[point]|point, text, append = False):
        if not isinstance(ps,list):ps=[ps]
        for p in ps: 
            if append: self.color[p]=+text 
            else     : self.color[p]= text  
    
    def set_text  (self, ps:list[point]|point, text):
        if not isinstance(ps,list):ps=[ps]
        for p in ps: 
            self.text[p]= text 
        
    def add_line  (self,
                   p1:point|tuple,
                   p2:point|tuple,
                   **kwargs):
        self.lines.append(line(p1,p2,**kwargs))

    def __getitem__(self,k:point|tuple)->tuple[str,str,list[line]]:
        if not isinstance(k,point):
            k = point(*k)

        lines = []
        for x in self.lines:
            if x.p1 == k or x.p2 == k:
                lines.append(x)

        return self.text[*k], self.color[*k], lines

    def __setitem__(self,key:tuple,value):
        ''' Set item, len 1 sets as pixel, color does otherwise '''
        if len(value) == 1:
            self.text[key]  = value
        else:
            self.color[key] = value

    def draw_lines(self)->tuple[np.array,np.array]:
        text  = self.text
        color = self.color

        for line in self.lines:
            coords = line.determine_line()
            text,color = line.shader(text,color,coords)
        
        return text,color
        

    def print_collapse(self, 
                       default_text  = ' ',
                       default_color = ENDC,
                       draw_lines    = True):
        color = self.color
        text  = self.text

        if draw_lines:
            text,color = self.draw_lines(text,color)

        color_compare  = np.roll (color, shift = 1,) #axis =1)
        color_dif_mask = np.where(color != color_compare, f'{default_color}'+ color, '')
        color_dif_mask + self.text
        res = []
        for row in np.where(text=='', default_text, text):
            res.append(''.join(list(row)))
        return res

    def centered(self)->Self:
        new = copy.deepcopy(self)
        new.offset(new.color.shape/2)
        return new

    def bounds(self)->tuple[tuple[int],tuple[int]]:
        array = self.text.astype(bool)
        col_sum = np.sum(array,axis=0).as_type(bool)
        row_sum = np.sum(array,axis=1).as_type(bool)

        col_min = col_sum.index(True)
        col_max = len(col_sum)-1-col_sum[::-1].index(True)

        row_min = row_sum.index(True)
        row_max = len(row_sum)-1-row_sum[::-1].index(True)

        return ((row_min,row_max),(col_min,col_max))

# a =       np.full((8, 8), '',   dtype= np.dtypes.StringDType())
# a_color = np.full((8, 8), ENDC, dtype= np.dtypes.StringDType())

# b =       np.full((8, 8), '',   dtype= np.dtypes.StringDType())
# b_color = np.full((8, 8), ENDC, dtype= np.dtypes.StringDType())

a = sprite(color_default=OKBLUE)
a[0,0] = 'a'
a.offset((2,3))

b = sprite()
b[2,2] = 'b'

c = a|b
lines = c.print_collapse()
for x in lines: 
    print(x)



#### TESTING DRAWING LINKS:

# import math

# def solve_curve_points(
#          a_pos    : tuple[int,int] , 
#          b_pos    : tuple[int,int] ,
#          a_handle : tuple[int,int] = None,
#          b_handle : tuple[int,int] = None,
#          ) ->  list[tuple[int,int]]:
#     ''' Find path a->b and place sampling points to solve, dumb-dumb default is using handles '''
#     res = []
#     assert a_handle is not None
#     assert b_handle is not None

#     return [a_pos, a_handle, b_pos, b_handle]

# def solve_shader(
#          points   : list[tuple[int,int]],
#          np_array : np.array
#          )->np.array:
#     ''' Interpret points, place asci characters w/a in np_array and return. Typically for actual shader not point incriment '''
    
#     ''' Yeah this whole thing is kinda stupid. Instead snap to closes points that intercept?'''

#     an0 = tuple(np.subtract(points[ 0], points[ 1]))
#     bn0 = tuple(np.subtract(points[-1], points[-2]))
#     points.insert(0,an0)
#     points.insert(-1, bn0)
#     #Extrapolate handles for shader's deg solver
    
#     for index,pos in enumerate(points[1:-2]):
#         index = index + 1
#         _t_prev = points[index-1]
#         _t_next = points[index+1]
#         # degr  = calculate_angle(_prev,pos,_next)

#         _prev = _t_prev
#         _pos  = pos
#         _next = _t_next


#         degr = calculate_angle(_prev,_pos,_next)
#         step = angle_to_step[round(degr / 45) * 45]
#         char = sample_chart(degr,index,'?')

#         i = 0
#         while not np.all(_pos == _t_next):
#             print(_pos)
#             if i > 999: raise Exception('What are you doing step-line?')
#             i  += 1

#             _next = np.add(_pos, step)
#             np_array[_pos] = char

#             degr = calculate_angle(_prev,_pos,_next)
#             if degr != 0:
#                 print('DEGR:',degr)
#                 raise 
#                 step = angle_to_step(round(degr / 45) * 45)
#             else: step = angle_to_step[45]
#             char = sample_chart(degr,i,'?')
        
#             _prev = _pos
#             _pos  = _next

#         return np_array    
            


# def sample_chart(degr:float|int, index:int, fallback:str):
#     for (l,h),v in chart.items():
#         if (degr >= l) and (degr <= h):
#             return v[index%len(v)]
#     return fallback


# #IK This is super fucking stupid:
# angle_to_step   = {
#     0   : ( 0 ,  1) ,
#     45  : ( 1 ,  1) ,
#     90  : ( 0 ,  1) ,
#     135 : (-1 ,  1) ,
#     180 : (-1 ,  0) ,
#     235 : (-1 , -1) ,
#     280 : ( 0 , -1) ,
#     325 : ( 1 , -1) ,
#     360 : ( 0 ,  1) ,
# }

# chart = {
#     (337.5 , 360  ) : '#',
#     (-22.5 , 22.5 ) : '#',
#     (22.5  , 67.5 ) : '#',
#     (67.5  , 112.5) : '#',
#     (112.5 , 157.5) : '#',
#     (157.5 , 202.5) : '#',
#     (202.5 , 247.5) : '#',
#     (247.5 , 292.5) : '#',
#     (292.5 , 337.5) : '#',
# }


# def calculate_angle(_prev,pos,_next):
#     v1  = np.subtract(pos   , _prev)
#     v2  = np.subtract(_next , pos  )


#     if np.all(v1 == (0,0)) or np.all(v2 == (0,0)): 
#         return (0,0)

#     nv1 = normalize_2vec(v1)

#     nv2 = normalize_2vec(v2)
    
#     dot = np.dot(v1,v2)
#     cos = np.divide(dot , (np.dot(nv1,nv2)))
#     rad = np.arccos(cos)
#     deg = np.deg2rad(rad)

#     return np.nan_to_num(deg)
#     # if deg == np.nan:
#     #     return 0
#     # cos_angle  = (min(max(x,+1),-1) for x in cos_angle)
#     # acos_angle = (math.acos(x)      for x in cos_angle)
#     # degr_angle = (math.degrees(x)   for x in acos_angle)
#     return deg


# def normalize_2vec(vec):
#     sum_sq = sum(x**2 for x in vec)
#     mag    = math.sqrt(sum_sq)
#     if mag == 0: 
#         return [0]*len(vec)
#     normalized = [x / mag for x in vec]
#     return normalized

#TEST:
# board = np.full((8, 8), '',   dtype= np.dtypes.StringDType())
# res = solve_shader([(1,3),(5,5)],a)
# print(res)


#TODO PLAN:
#Utilize above as a way to slice for mask creation
# value of index, angle
# Then fullfill angle with corisponding character