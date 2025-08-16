#Sourced from https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
import random

#TODO: Re-write to have a proper print w/ formatting generator. now that I understand ANSI codes more

ESC = '\033'
class modes:
    BOLD   = (f'{ESC}[1m',f'{ESC}[22m')	#bold mode.
    DIM    = (f'{ESC}[2m',f'{ESC}[22m')	#dim/faint mode.
    ITAL   = (f'{ESC}[3m',f'{ESC}[23m')	#italic mode.
    ULINE  = (f'{ESC}[4m',f'{ESC}[24m')	#underline mode.
    BLINK  = (f'{ESC}[5m',f'{ESC}[25m')	#blinking mode
    INVER  = (f'{ESC}[7m',f'{ESC}[27m')	#inverse/reverse mode
    INVS   = (f'{ESC}[8m',f'{ESC}[28m')	#hidden/invisible mode
    STRIKE = (f'{ESC}[9m',f'{ESC}[29m')	#strikethrough mode.

class colors:
    @staticmethod
    def Generate256(key:str|int,background = False):
        if isinstance(key,str):
            r = random.Random()
            r.seed(key)
            # key = r.randint(1,256)
            key = r.randint(1,231)
            del r
        if background: return f'{ESC}[48;5;{key}m'
        return f'{ESC}[38;5;{key}m'
    
    # Could also generate rgb 

    Black = f'{ESC}[30m' 
    
    B_Black = f'{ESC}[40m' 

    Red = f'{ESC}[31m' 
    B_Red = f'{ESC}[41m' 
    
    Green = f'{ESC}[32m' 
    B_Green = f'{ESC}[42m' 
    
    Yellow = f'{ESC}[33m' 
    B_Yellow = f'{ESC}[43m' 
    
    Blue = f'{ESC}[34m' 
    B_Blue = f'{ESC}[44m' 

    Magenta = f'{ESC}[35m' 
    B_Magenta = f'{ESC}[45m' 

    Cyan = f'{ESC}[36m' 
    B_Cyan = f'{ESC}[46m' 

    White = f'{ESC}[37m' 
    B_White = f'{ESC}[47m' 

    Default = f'{ESC}[39m' 
    B_Default = f'{ESC}[49m' 

    @classmethod
    def ColorKey_Fallback(cls,key:int|str,background =False):
        if isinstance(key,str):
            if background:
                if (res:=getattr(cls,'B_'+key.capitalize(),None)) is not None: return res
            if (res:=getattr(cls,key.capitalize(),None)) is not None: return res
        else: return cls.Generate256(key,background=background)


    