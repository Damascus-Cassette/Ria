''' Module for simple nested asci rendering of objects '''

from typing import Self
from __future__ import annotations
from types import FunctionType

class text_statics():
    Passthrough = None
        #zero opacity address value 
        #Background value, if none use this.
    Fallback = ' '
        #Fallback value when not resolved (ie is None after all sampling)


    class ANSI:
        #noted from blender builds interestingly: https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
        HEADER    = '\033[95m'
        OKBLUE    = '\033[94m'
        OKCYAN    = '\033[96m'
        OKGREEN   = '\033[92m'
        WARNING   = '\033[93m'
        FAIL      = '\033[91m'
        ENDC      = '\033[0m'
        BOLD      = '\033[1m'
        UNDERLINE = '\033[4m'

class sprite_object():
    Background : str|FunctionType = ' '
        #
    
    effects    : list[str]
        #Text Color effects towards entire sprite
        #Sprite should resolve children colors

    children   : list[sprite_view_instance]
        #Children sprites are drawn backwards


    def sprite()->list[list[str|None]]:
        ...
    def sprite_bounding()->tuple[int,int]:
        #Bounding of self sprite.
        #Can be simplified if scalable item, via target scale
        ...
    def sprite_set_bounding()->tuple[int,int]:
        ...
    def sprite_set():
        #This and all children drawn on top in reverse order w/ text ordering
        #Items in negative space are normalized
        ...

class sprite_view_instance():
        #in, out, title, ect
    sprite_group : str
    sprite       : sprite_object
    pos_x        : int|str
    pos_y        : int|str
        #Pos can be str for variable expresson: 
        # IE: '[|]-3'     meaning center - 3
        # IE: '[|]/2+[|]' 3/4ths of the way over via 
        # IE: 'i+3' index 


    def __init__(self,
                 sprite:sprite_object, 
                 sprite_group:str = '', 
                 pos_x:str|int    = 0 , 
                 pos_y:str|int    = 0 ,
                 ):
        self.sprite = sprite
        self.sprite_group = sprite_group
        self.pos_x = pos_x
        self.pos_y = pos_y

    def interpret_pos(self,
                      self_bounding   : tuple[int,int], 
                      parent_bounding : tuple[int,int],
                      index           : int = 0,
                      )->tuple[int,int]:
        s_bw  , s_bh  = self_bounding
        p_bw  , p_bh  = parent_bounding

        pos_x = pos_utils.interpret_pos_axis(s_bw, self.pos_x, p_bw, vars = {'x':s_bw,'w':s_bw,'h':s_bh})
        pos_y = pos_utils.interpret_pos_axis(s_bh, self.pos_y, p_bh, vars = {'x':s_bh,'w':s_bw,'h':s_bh})

        return pos_x, pos_y

class pos_utils():

    @classmethod
    def interpret_pos_axis(self ,
            x         : int     ,          # variable keys
            expr      : str|int ,          # Axis in current bounding
            p_x_bound : int     ,          # Determines axis offset
            variables : dict|None = None , # parent object's bounding box in axis 
            )->int: 
        '''return Integer, pos or neg, on axis specified axis resolving possible expressions, 0 is left-top'''
        
        if isinstance(expr,int): return expr

        if variables is None: variables = {}
        variables = variables | self.generate_vars(x,p_x_bound)
        
        expr_res  : list[int] = []
        res  = 0

        for indv_expr in self.yield_expr_sets(expr):
            if isinstance(indv_expr,str): 
                indv_expr = self.replace_variables(indv_expr,variables)
            
            a,b,func = self.split_expression(indv_expr)

            if not a: a = res

            res = func(int(a),int(b))
            expr_res.append(res)

        return int(sum(expr_res))
    
    @classmethod
    def split_expression(self,expr:str)->tuple[int,int,FunctionType]:
        for k,v in self.expressions.items():
            if k in expr:
                a = expr.split(k)[0]
                b = expr.split(k)[1]
                func = v
                return a,b,func
        raise Exception(f'COULD NOT RESOLVE EXPRESSION: {expr}')

    @classmethod
    def generate_vars(self,
                       s_bound, #self   len bounding
                       p_bound, #parent len bounding
                      )->dict[str,FunctionType]:
        return {
            # ALIGN LEFT 
            '|<<'  : 0                         , # p_left meets self_left
            '<|<'  : 0 - (s_bound/2)           , # p_left meets self_center 
            '<<|'  : 0 - s_bound               , # p_left meets self_right

            # ALIGN RIGHT 
            '|>>'  : p_bound + s_bound         , # p_right meets self.left
            '>|>'  : p_bound + (s_bound/2)     , # p_right meets self.center
            '>>|'  : p_bound - s_bound         , # p_right meets self.right

            # ALIGN CENTER 
            '[>|]' : (p_bound/2) - s_bound     , # p_center meets self.left
            '[|]'  : (p_bound/2) - (s_bound/2) , # p_center meets self.center
            '[|<]' : (p_bound/2) + s_bound     , # p_center meets self.left
        }
        
    @classmethod
    def replace_variables(expr:str,variables:dict):
        for x in expr:
            if x in variables.keys():
                res =+ variables[x]
            else:
                res =+ x
        return res

    @classmethod
    def yield_expr_sets(self,expr):
        expr_sets : list[str|int] = []
        _set = []
        _last_set : tuple = None
        for x in expr:
            _delim_set = self.get_delim(x)
            
            if _delim_set is None:
                yield str(_set)
                _set = []
                continue
            elif _delim_set != _last_set:
                yield str(_set)
                _set = []
                continue
            _set =+ x
        yield _set

    @classmethod    
    def get_delim(self,v)->tuple[str]|None:
        for x in self.statement_delim_sets:
            if v in x:
                return x
        if v in self.statement_split_on:
            return None
        raise Exception(v, 'IS NOT IN ACCEPTED VALUES:', self.statement_delim_sets, self.statement_split_on)

    statement_split_on   = ','
    statement_delim_sets = [ #Contents of each string are utilized as a delimiter of statement
        '|<>[]+',
        '1234567890/wh',
    ]
    expressions = {
        '//' : lambda a,b : a // b , 
        '/'  : lambda a,b : a /  b , 
        '+'  : lambda a,b : a +  b , 
        '-'  : lambda a,b : a -  b , 
        }