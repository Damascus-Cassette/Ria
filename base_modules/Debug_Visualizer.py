from .utils.statics         import get_data_uuid, get_file_uid, INVALID_UUID
from .Execution_Types       import _mixin, item
from ..statics              import _unset
from ..models.struct_module import module
from .Execution_Types       import socket_shapes as st

from typing import Self

from typing import TypeAlias
import copy

class ANSI:
    #from blender builds interestingly: https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
    HEADER    = '\033[95m'
    OKBLUE    = '\033[94m'
    OKCYAN    = '\033[96m'
    OKGREEN   = '\033[92m'
    WARNING   = '\033[93m'
    FAIL      = '\033[91m'
    ENDC      = '\033[0m'
    BOLD      = '\033[1m'
    UNDERLINE = '\033[4m'


from contextvars import ContextVar
from contextlib  import contextmanager

def color_print(str,orig_len):
    ...

class text_line:
    align_index : int
    colors      : list[str] = (ANSI.ENDC,)
    fill        : str       = ' ' #Empty space filler
    text        : str       = ''

    def __len__(self):
        return len(self.text)
    
    def __init__(self,text, fill=' ', align_index:int=0, colors:str|list[str]=ANSI.ENDC):
        if not isinstance(colors, (list,tuple,set)):
            colors = [colors]
        else: colors = copy.copy(colors)

        self.align_index = align_index
        self.colors = colors
        self.fill   = fill
        self.text   = text

    def formatted_text(self,max_len:int=None)->tuple[str]:
        if max_len is None:
            max_len = len(self)
        post_len = len(self)-max_len-self.align_index
        post     = self.fill * post_len
        pre      = self.fill * (max_len-post_len) 
        return (*self.colors, pre, self.text, post, ANSI.ENDC )

    def draw(self, max_len=None)->None:
        print(*self.formatted_text(max_len=max_len))
        
class text_paragraph:
    items : list[text_line]
    
    def __init__(self,lines:list[text_line],align_index:int=0):
        if not isinstance(lines, (list,tuple,set)):
            lines = [lines]
        else: lines = copy.copy(lines)
        self.items = lines
        self.align_index = align_index

    def append(self,item:text_line):
        assert isinstance(item,text_line)

    def extend(self,items:text_line):
        assert isinstance(items, (list,tuple,set))
        for x in items:
            self.append(x)

    def max_height(self):
        return len(self.items)

    def max_width(self):
        return max([len(x) for x in self.items])

    def __iter__(self):
        for x in self.items:
            yield x
    
    def y_offset_yield(self,y_max):#->text_line:
        for y_i in enumerate(y_max):
            #Yield with self offset_index
            if y_i<self.align_index:
                yield text_line('',),self
                #Draws nothing for deired length
            yield self.items[self.align_index - y_i],self

def link_line():
    def __init__(colors,start_index:int,end_index:int):
        ...
    ...

def yield_rows(paragraphs):
    lst = []
    for x in paragraphs: 
        if isinstance(x,ellipsis): 
            yield lst
            lst = []
            last_ellipsis = True
        else:
            lst.append(x)
            last_ellipsis = False
    if not last_ellipsis:
        yield lst    


def draw(paragraphs):

    for paragraph_set in yield_rows(paragraphs):
        max_len    = max(x.max_width  for x in paragraph_set)
        max_height = max(x.max_height for x in paragraph_set)

        row : list[str] = [''] * max_height
        for i,x in enumerate(paragraph_set):
            max_len=paragraph_set.max_width
            lines   : list[text_line] = list(x.y_offset_yield(max_height))
            f_lines : list[str]       = [x.formatted_text(max_len) for x in lines]
            new_row = []
            for r,l in zip(row,f_lines):
                new_row.append(r+l)
            row = new_row

    # for lines in zip(*iterators):
    #     for line, paragraph in lines:
    #         line      : text_line
    #         paragraph : text_paragraph
    #         line.formatted_text(paragraph.max_len)

def line_paragraph():
    ...

class main(module):
    ''' Quick n dirty way to debug node & graph shapes via text.  '''
    UID     = 'Debug_Interface'
    Version = '0.1a'

    

