# -*- coding: utf-8 -*-
"""
Created on Tue Dec 29 15:09:27 2020

@author: Marco Annoni (Copyright 2020, 2021)

numpy version:  1.18.1
python version: 3.7.6
Qt version:     5.9.6
PyQt version:   5.9.2
Spyder version: 4.0.1
Pygame version: 2.0.1

This is an implementation of American checkers.
Rules for the game can be found here:
    https://www.ultraboardgames.com/checkers/game-rules.php
English, international and Italian versions of the game
also exist.

To run this script in Windows you need python, some packages and an update of the PATH system variable:
    Install python from the microsoft store. When prompted, pin it to the Start menu and/or the task
    Win+R to open a 'run' prompt
    Type 'cmd' (without quotes) and press Enter to access the command prompt
    In the command prompt, enter (without quotes) 'pip install numpy'
    In the command prompt, enter (without quotes) 'pip install pygame'
    Find the path where python stores the newly installed packages by:
        opening File Explorer
        entering %USERPROFILE%\AppData\Local\Packages in the address bar
        finding and entering the python folder (it will have a long name such as PythonSoftwareFoundation.Python.3.9_qbz5n2kfra8p0)
        entering the nested folders 'LocalCache', 'local-packages', 'Python39', 'site-packages'
    Save the path you just landed into. We will refer to it as 'the packages folder'.
    Include the packages folder in the system PATH variable by:
        opening File Explorer
        right-clicking on "This PC" or "My Computer"
        clicking on 'Properties' from the contextual menu
        Clicking on 'Advanced system settings'
        Clicking on 'Environmental Variables...'
        Clicking on 'Path' and "Edit..."
        Clicking on 'New'
        Entering the path to the packages folder. It is the path we saved earlier.
    Run python. You can find it on the task bar and on the start menu since we pinned it there earlier
    Open this file there
    Press F5 to run it
    Enjoy playing!
"""

#%% Imports, some definitions


import numpy as np
import copy
from time import sleep
import winsound #sleep(0.03);winsound.Beep(500,500)
import operator
import pygame, sys
from pygame.locals import *

debugging_mode = False #True is appropriate when difficulty_depth_ifwhite == difficulty_depth_ifblack
difficulty_depth_ifwhite = 5 #6 or more starts being slow for what a player would expect to have to wait
difficulty_depth_ifblack = 5
initial_turn = 'b' #it can be 'w' (for white) or 'b' (for black). 
human_players = 'b' #it can be 'w' (for white), 'b' (for black), 'bw' or 'wb' if both players are human, '' if the computer plays both roles
CPU_players = ''.join({'b', 'w'}-set(human_players))
turn = initial_turn
delay_before_computer_move = 0.4 #(in seconds)
pieces_initially = np.array( \
    [['bc','','bc','','','','wc',''], \
      ['','bc','','','','wc','','wc'], \
      ['bc','','bc','','','','wc',''], \
      ['','bc','','','','wc','','wc'], \
      ['bc','','bc','','','','wc',''], \
      ['','bc','','','','wc','','wc'], \
      ['bc','','bc','','','','wc',''], \
      ['','bc','','','','wc','','wc']], \
      dtype='str_')
#Array of pieces 
#(one row here represents one column on the board)
#Test for debugging:
# pieces_initially = np.array( \
#     [['','','','','','','',''], \
#       ['','','wc','','wc','','wc',''], \
#       ['','bc','','','','','',''], \
#       ['','','','','','','wc',''], \
#       ['','','','','','','',''], \
#       ['','','','','','','wc',''], \
#       ['','','','','','','',''], \
#       ['','','','','','','','']], \
#       dtype='str_')

pygame.init() #close it, eventually, with pygame.quit()

BLACK =    pygame.Color(  0,   0,   0)
WHITE =    pygame.Color(255, 255, 255)
RED =      pygame.Color(255,   0,   0)
GREEN =    pygame.Color(  0, 255,   0)
BLUE =     pygame.Color(  0,   0, 255)
YELLOW =   pygame.Color(255, 255,   0)
HIYELLOW = pygame.Color(205, 205, 100)
ORANGE =   pygame.Color(255, 130,   0)
HIORANGE = pygame.Color(205, 100,  80)
GREY   =   pygame.Color(128, 128, 128)
HIGREY   = pygame.Color(100, 100, 100)

window_side_pxl_length = 700
wspl = window_side_pxl_length
square_side_pxl_length = 400 // 8 - 1
sspl = square_side_pxl_length
board_side_pxl_length = sspl*8
bspl = board_side_pxl_length
padding_on_left = 40
pol = padding_on_left
padding_on_top = 40
pot = padding_on_top
radius = sspl // 4 #radius of each checker piece
radiuss = radius ** 2   #square of the radius
mousex, mousey = 1, 1
state = 'Standard'

#%% Board
squares = list()
for i in range(8): #fix a column
    row_of_squares = list()
    ros = row_of_squares
    for j in range(8): #loop over rows
        one_square = pygame.Rect(pol+i*sspl, pot+(7-j)*sspl,  sspl, sspl)
#                                    left,          top, width, height
        color = BLACK if (i+j)%2 == 0 else WHITE
        ros.append((one_square, color))
    squares.append(ros)

def draw_board():
    pygame.draw.polygon(DISPLAYSURF, BLUE, ((pol-2, pot-2), (pol+2+bspl, pot-2), (2+pol+bspl, pot+2+bspl), (pol-2, pot+2+bspl)))
    for i in range(8): #fix a column
        for j in range(8): #loop over rows
            one_square = squares[i][j][0]
            color = squares[i][j][1]
            pygame.draw.rect(DISPLAYSURF, color, one_square)

def print_text(text, font, fontsize, center, color, bck_color):
    """Example:
    print_text("A", 'freesansbold.ttf', 32, (64, 40), WHITE, BLUE)
    ...where WHITE=(255,255,255) and BLUE=(0,0,255)
    """
    fontObj = pygame.font.Font(font, fontsize)
    textSurfaceObj = fontObj.render(text, True, color, bck_color)
    textRectObj = textSurfaceObj.get_rect()
    textRectObj.center = center
    DISPLAYSURF.blit(textSurfaceObj, textRectObj)

def text_rowcol(text, font, fontsize, rowcol, color, bck_color):
    """<rowcol> is in the format (5,7).
    Row 5    corresponds to row 6 on the board.
    Column 7 corresponds to 8th column ('H') on the board.
    Negative integers are allowed.
    E.g. 
    text_rowcol(chr(asc), 'freesansbold.ttf', 32, (-3, 0), WHITE, BLUE)
    """
    j, i = rowcol
    center = (pol+i*sspl, pot+(7-j)*sspl)
    print_text(text, font, fontsize, center, color, bck_color)

def draw_labels():
    for i in range(8):
        asc = 65+i
        x = squares[i][0][0].centerx
        y = squares[i][0][0].centery + sspl
        print_text(chr(asc), 'freesansbold.ttf', 32, (x, y), WHITE, BLUE)
        x = squares[i][7][0].centerx
        y = squares[i][7][0].centery - sspl
        print_text(chr(asc), 'freesansbold.ttf', 32, (x, y), WHITE, BLUE)
        x = squares[0][i][0].centerx - sspl
        y = squares[0][i][0].centery
        print_text(str(i+1), 'freesansbold.ttf', 32, (x, y), WHITE, BLUE)
        x = squares[7][i][0].centerx + sspl
        y = squares[7][i][0].centery
        print_text(str(i+1), 'freesansbold.ttf', 32, (x, y), WHITE, BLUE)

#%% Pieces
        
def is_point(ttuple): #to be debugged
    if not isinstance(ttuple, tuple):
        return False
    if len(ttuple)!=2:
        return False
    if not isinstance(ttuple[0], int):
        return False
    if not isinstance(ttuple[1], int):
        return False
    return True

def is_colrow(pair):
    if not isinstance(pair, tuple):
        return False
    if len(pair)!=2:
        return False
    if not isinstance(pair[0],int):
        return False
    if not isinstance(pair[1],int):
        return False
    return True
    
def draw_piece(position, piece, high=False): 
    #E.g. draw_piece(position = (1,3), piece = "wK")
    assert is_colrow(position)
    piece = str(piece)
    if piece not in ('wc','bc','wK','bK',''):
        raise ValueError("For position %s, the 'piece' argument\n \
of the 'draw_piece' function should be\n \
one of the following: wc,bc,wK,bK.\n \
Instead, it was \
'%s'." % (str(position),piece))
    if piece != '':
        temp_square = squares[position[0]][position[1]][0]
        center_x = temp_square.centerx
        center_y = temp_square.centery
        center = (center_x,center_y)
        #radius = sspl // 4
        if   piece[0]=='w' and high:
            color_in = HIYELLOW
        elif piece[0]=='w' and not high:
            color_in = YELLOW
        elif piece[0]=='b' and not high:
            color_in = ORANGE
        elif piece[0]=='b' and high:
            color_in = HIORANGE
        if piece[1]=='K':
            radius2 = int(radius*1.5)
            color_out = (156,156,156)
        else:
            radius2 = int(radius*1.2)
            color_out = (156,156,156)
        pygame.draw.circle(DISPLAYSURF, color_out, center, radius2, 0)
        pygame.draw.circle(DISPLAYSURF, color_in, center, radius, 0)

pieces = copy.deepcopy(pieces_initially)

def draw_pieces(pieces_array = pieces):
    for i in range(8):
        for j in range(8):
            draw_piece(position = (i,j), piece = pieces[i,j])

def redraw_movable_pieces(mov_pieces_colrows):
    for colrow in mov_pieces_colrows:
        draw_piece(colrow, pieces[colrow], high=True)

# pygame.display.update()
# pygame.event.get()
# pygame.quit()

def draw_destination(position, high=False):
    #E.g. draw_destination(position = (1,3))
    assert is_colrow(position)
    i, j = position
    temp_square = squares[i][j][0]
    center_x = temp_square.centerx
    center_y = temp_square.centery
    center = (center_x,center_y)
    #radius = sspl // 4
    if high:
        color_in = HIGREY
    else: 
        color_in = GREY
    radius2 = int(radius*1.2)
    color_out = (156,156,156)
    pygame.draw.circle(DISPLAYSURF, color_out, center, radius2, 0)
    pygame.draw.circle(DISPLAYSURF, color_in, center, radius, 0)

def draw_pointer_circle(xyposition):
    #E.g. draw_pointer_circle(xyposition = (213,320))
    assert is_point(xyposition)
    x, y = xyposition
    temp_square = squares[i][j][0]
    center_x = temp_square.centerx
    center_y = temp_square.centery
    center = (center_x,center_y)
    #radius = sspl // 4
    pygame.draw.circle(DISPLAYSURF, HIGREY, xyposition, radius, 3)


#%% Operations (biggest cell)
    
def depth_by_turn(turn):
    assert turn in ('w','b')
    if turn == 'b':
        return difficulty_depth_ifblack
    else:
        return difficulty_depth_ifwhite

def turn_to_colorname(turn):
    assert turn in ('w','b')
    if turn == 'b':
        return "Black"
    else:
        return "White"
    
def display():
    global mousex
    global mousey
    short_list = pygame.event.get()
    for event in short_list:
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == MOUSEMOTION:
            mousex, mousey = event.pos
    pygame.display.update()    

def count_pieces(pieces_array = pieces, \
                 color='w'): #color can be 'w' or 'b'
    if not color in ('w','b'):
        raise ValueError("The 'color' argument\n \
of the 'count_pieces' function should be\n \
one of the following: 'b', 'w'.\n \
Instead, it was \
'%s'." % (color,))
    counter = 0
    for i in range(8):
        for j in range(8):
            if pieces_array[i,j] != '':
                if pieces_array[i,j][0] == color:
                    counter += 1
    return counter
#count_pieces(color='b')

def scoring_f(pieces_array = pieces):
    wscore = 0
    bscore = 0
    for i in range(8):
        for j in range(8):
            if pieces_array[i,j] != '':
                if pieces_array[i,j][0] == 'w' and pieces_array[i,j][1] == 'K':
                    wscore += 5
                elif pieces_array[i,j][0] == 'w' and pieces_array[i,j][1] == 'c':
                    wscore += 3+(2*(7-j)/8)
                if pieces_array[i,j][0] == 'b' and pieces_array[i,j][1] == 'K':
                    bscore += 5
                elif pieces_array[i,j][0] == 'b' and pieces_array[i,j][1] == 'c':
                    bscore += 3+(2*j/8)
    if wscore != 0:
        score = bscore/wscore
    else:
        score = 21
    return score
scoring_f_bwin = 21 #this score means that black wins
scoring_f_wwin = -1 #this score means that white wins


def turn_toggle(color): #color can be 'w' or 'b'
    """e.g. turn = turn_color('w')"""
    if not isinstance(color, str):
        raise ValueError("<color> in function\n \
<turn_toggle> was supposed to be a character.\n \
Instead its type is %s" % (str(type(color)),))
    if color=='w':
        return 'b'
    elif color=='b':
        return 'w'
    else:
        raise ValueError("<color> in function\n \
<turn_toggle> was supposed to be 'w' or 'b'.\n \
Instead it was:\n \
'%s'" % (color,))

def turn_color(turn): #turn can be 'w' or 'b'
    """e.g. color_tuple = turn_color('b') """
    assert turn in ('w','b')
    if turn == 'w':
        return YELLOW
    if turn == 'b':
        return ORANGE

def add_tuples(tup1, tup2):
    """add 2 tuples with same length"""
    return tuple(map(operator.add, tup1, tup2))

def midtuple(tup1, tup2):
    """averages 2 tuples with same length.
    It returns a tuple with integer coefficients.
    This function should only be used within 
    the <eating_moves> function"""
    return tuple(map(lambda i, j: int((i+j)/2), tup1, tup2))

def simple_moves(position, pieces):
    """Given a placement of pieces and a position,
    it finds the non-capturing moves that the checker 
    at such position can make.
    <pieces>: an array containing the placement of pieces
    <position>: a pair with the position of the checker
        whose moves we are finding. E.g. (i,j), where
        i in range(8) and j in range(8).
    <simple_moves>: returns a list of moves 
        (a move is a pair of pairs, one matching the 
        'position' or starting point, the other matching 
        the destination)
    """
    assert is_colrow(position), "Position is: "+str(position)
    if pieces[position] == '':
        return tuple()
    color   = pieces[position][0] #'w' or 'b'
    quality = pieces[position][1] #'c' or 'K'
    candidate_dest = []
    if quality == "K" or color == 'b':
        candidate_dest.append(add_tuples(position, (-1,1)))
        candidate_dest.append(add_tuples(position, ( 1,1)))
    if quality == "K" or color == 'w':
        candidate_dest.append(add_tuples(position, ( 1,-1)))
        candidate_dest.append(add_tuples(position, (-1,-1)))
    args_to_remove=[]
    for arg in candidate_dest:
        if min(arg)<0 or max(arg)>7 or pieces[arg] != '':
            args_to_remove.append(arg)
    destinations = list(set(candidate_dest)-set(args_to_remove))
    simple_moves_l = [(position,dest) for dest in destinations]
    simple_moves_l = tuple(simple_moves_l)
    return simple_moves_l

def eating_moves(position, pieces):
    """Given a placement of pieces and a position,
    it finds the capturing moves that the checker 
    at such position can make.
    <pieces>: an array containing the placement of pieces
    <position>: a pair with the position of the checker
        whose moves we are finding.
    <eating_moves>: returns a list of capturing moves 
        (a move is a pair of pairs, one matching the 
        'position' or starting point, the other matching 
        the destination)
    """
    assert is_colrow(position), "Position is: "+str(position)
    if pieces[position] == '':
        return tuple()
    color   = pieces[position][0] #'w' or 'b'
    quality = pieces[position][1] #'c' or 'K'
    candidate_dest = []
    if quality == "K" or color == 'b':
        candidate_dest.append(add_tuples(position, (-2,2)))
        candidate_dest.append(add_tuples(position, ( 2,2)))
    if quality == "K" or color == 'w':
        candidate_dest.append(add_tuples(position, ( 2,-2)))
        candidate_dest.append(add_tuples(position, (-2,-2)))
    args_to_remove=[]
    for arg in candidate_dest:
        if min(arg)<0 or max(arg)>7 or pieces[arg] != '':
            args_to_remove.append(arg)
        else:
            middle_pos = midtuple(position,arg) #(1,5)
            middle_piece = pieces[middle_pos] #'bc'
            if turn_toggle(color) not in middle_piece:
                args_to_remove.append(arg)
    destinations = list(set(candidate_dest)-set(args_to_remove))
    eating_moves_l = [(position,dest) for dest in destinations]
    eating_moves_l = tuple(eating_moves_l)
    return eating_moves_l

def single_moves(position, pieces):
    assert is_colrow(position)
    em = eating_moves(position, pieces)
    #In American checkers, capturing moves must be chosen
    # over simple ones.
    if len(em)>0:
        return em
    else:
        return simple_moves(position, pieces)

def board_moves(turn, pieces):
    """E.g.: board_moves('w', pieces)
    It returns a tuple with all moves the given player
        could make.
    <turn> must be 'w' or 'b'
    <pieces> must be the ndarray woth the pieces"""
    em = tuple() #em = eating moves
    sm = tuple() #sm = simple moves
    for i in range(8):
        for j in range(8):
            if turn not in pieces[i,j]: #e.g. 'b' not in 'bK'
                continue
            em += eating_moves((i, j), pieces)
            sm += simple_moves((i, j), pieces)
    if len(em)>0:
        return em
    else:
        return sm

def game_is_over(turn, pieces):
    assert turn in ('w','b')
    return (board_moves(turn, pieces) == tuple())

def board_simple_moves(turn, pieces):
    """E.g.: board_simple_moves('w', pieces)
    It returns a tuple with all moves *simple* moves the given player
        could make.
    <turn> must be 'w' or 'b'
    <pieces> must be the ndarray woth the pieces"""
    sm = tuple() #sm = simple moves
    for i in range(8):
        for j in range(8):
            if turn in pieces[i,j]: #e.g. 'b' in 'bK'
                sm += simple_moves((i, j), pieces)
    return sm

def board_composite_moves(turn, pieces):
    """E.g.: board_composite_moves('w', pieces)
    It returns a tuple with all moves *composite* moves the given player
        could make.
    <turn> must be 'w' or 'b'
    <pieces> must be the ndarray woth the pieces"""
    cm = tuple() #sm = simple moves
    for i in range(8):
        for j in range(8):
            if turn in pieces[i,j]: #e.g. 'b' in 'bK'
                cm += composite_moves((i, j), pieces)
    return cm

def movable_pieces_colrows(board_possible_moves):
    """E.g.: movable_pieces_colrows(board_moves('w', pieces))
    It returns a tuple with the colrow(s) of the pieces 
        that can be moved based on the tuple of possible 
        moves <board_possible_moves>
    <board_possible_moves> must be a tuple of possible 
        moves, like the one returned by 
        board_moves(turn, pieces)"""
    assert is_moves(board_possible_moves)
    if len(board_possible_moves)>0:
        return tuple(zip(*board_possible_moves))[0]
    else:
        return tuple()

def is_move(pair_of_pairs):
    if not isinstance(pair_of_pairs, tuple):
        return False
    if not len(pair_of_pairs)==2:
        return False
    if not isinstance(pair_of_pairs[0], tuple):
        return False
    if not isinstance(pair_of_pairs[1], tuple):
        return False
    if not len(pair_of_pairs[0])==2:
        return False
    if not len(pair_of_pairs[1])==2:
        return False
    if not isinstance(pair_of_pairs[0][0], int):
        return False
    if not isinstance(pair_of_pairs[0][1], int):
        return False
    if not isinstance(pair_of_pairs[1][0], int):
        return False
    if not isinstance(pair_of_pairs[1][1], int):
        return False
    pair1, pair2 = pair_of_pairs
    pair1x, pair1y = pair1
    pair2x, pair2y = pair2
    if abs(pair1x-pair2x) != abs(pair1y-pair2y):
        return False
    if abs(pair1x-pair2x) not in (1,2):
        return False
    return True

def is_eating_move(pair_of_pairs):
    if not is_move(pair_of_pairs):
        return False
    pair1, pair2 = pair_of_pairs
    pair1x = pair1[0]
    pair2x = pair2[0]
    if abs(pair1x-pair2x) != 2:
        return False
    return True

def is_moves(tuple_of_moves):
    if not isinstance(tuple_of_moves, tuple):
        return False
    for move in tuple_of_moves:
        if not is_move(move):
            return False
    return True

def is_composite_move(moves_list):
    if not is_moves(moves_list):
        return False
    if len(moves_list) == 0:
        return True
    if len(moves_list) == 1 and is_eating_move(moves_list[0]):
        return True
    for i in range(len(moves_list) - 1):
        if moves_list[i][1] != moves_list[i+1][0]:
            return False
        if not is_eating_move(moves_list[i]):
            return False
    if not is_eating_move(moves_list[-1]):
        return False
    return True

def apply_move(move, pieces):
    """
    <move> is a pair of pairs, representing start and
        destination respectively 
        #e.g. ((1,2),(0,3)) or ((3,2),(1,4))
    <pieces> is an ndarray representing positions on the board.
    <apply_move> returns another ndarray like <pieces>,
        with the updated positions.
    """
    local_pieces = copy.deepcopy(pieces)
    assert is_move(move)
    local_pieces[move[1]] = local_pieces[move[0]].copy()
    local_pieces[move[0]] = ''
    """if the color on destination is white and the row number 
    is 0 (*,0), or the color on destination is black and the row 
    number is 7 (*,7), ...
    ... then the second character should be 'K' """
    cod = local_pieces[move[1]][0] #cod = color_on_destination
    rnod = move[1][1] #rnod = row_num_on_dest
    if (cod == 'w' and rnod == 0) or (cod == 'b' and rnod == 7):#PROMOTION to King!
        local_pieces[move[1]] = local_pieces[move[1]][0]+'K'
    if abs(move[0][0]-move[1][0]) == 2:
        piece_to_be_eaten = local_pieces[midtuple(move[0], move[1])]
        color_of_piece_to_be_eaten = piece_to_be_eaten[0]
        local_pieces[midtuple(move[0], move[1])] = ''
    return local_pieces

def is_promoting_move(move, pieces):
    """
    E.g. is_promoting_move(((1,2),(3,4)), pieces)
    """
    assert is_move(move)
    start_colrow = move[0] #e.g. (1,2)
    piece = pieces[start_colrow] #e.g. 'bc'
    if piece == "": #in this case piece must be in ('bc', 'bK', 'wc', 'wK')
        raise ValueError()
    piece_color = piece[0] #e.g. 'b'
    dest_colrow = move[1] #e.g. (3,4)
    dest_row = dest_colrow[1] #e.g. 4
    if (piece_color == 'w' and dest_row == 0) \
        or (piece_color == 'b' and dest_row == 7):
            return True
    else:
        return False #that's what would happen in the example
    
def move_is_continuable(move, pieces):
    """
    the move is a capture
        and it is not a promotion
        and its destination with resulting configuration has eating moves
    """
    assert is_move(move)
    if is_eating_move(move) and not is_promoting_move(move, pieces):
        dest_colrow = move[1]
        resulting_pieces_conf = apply_move(move, pieces)
        if len(eating_moves(dest_colrow, resulting_pieces_conf))>0:
            return True
    return False

def composite_moves(colrow_position, pieces): #needed by computer player only
    assert is_colrow(colrow_position)
    pieces_local = copy.deepcopy(pieces)
    em = eating_moves(colrow_position, pieces_local)
    if em == tuple():
        return tuple()
    output = tuple()
    for m in em:
        if not move_is_continuable(m, pieces_local):#move is continuable if it is not a promotion and one more eating move can be done afterwards
            output += ((m,),)
        else:
            next_state = apply_move(m, pieces_local)
            next_colrow = m[1]
            next_CMs = composite_moves(next_colrow, next_state)
            for next_cm in next_CMs:
                cm = (m,) + next_cm
                output += (cm,)
    return output

def apply_comp_move(comp_move, pieces): #to be debugged. #comp stands for composite
    """
    <comp_move> is a tuple of moves, each of which is a pair of pairs
    <pieces> is an ndarray representing positions on the board.
    <apply_comp_move> returns another ndarray like <pieces>,
        with the positions updated with the given moves.
    """
    local_pieces = copy.deepcopy(pieces)
    assert is_composite_move(comp_move), "comp_move = " + str(comp_move)
    for move in comp_move:
        local_pieces = apply_move(move, local_pieces)
    return local_pieces

def show_move(pieces):
    winsound.Beep(700,int(delay_before_computer_move*1000//2))
    #sleep(delay_before_computer_move/2)   #slow version gives you time to see the steps made by CPU
    draw_board() #slow version displays updated board after every step
    draw_pieces(pieces_array = pieces)#slow version displays updated board after every step
    display()
    winsound.Beep(400,int(delay_before_computer_move*1000//2))
    #sleep(delay_before_computer_move)   #slow version gives you time to see the steps made by CPU

def show_turn(turn):
    text_rowcol("Turn:", 'freesansbold.ttf', 32, (7, 10), WHITE, BLUE)
    text_rowcol("     ", 'freesansbold.ttf', 32, (6, 10), turn_color(turn), turn_color(turn))

def apply_comp_move_slow(comp_move, pieces): #to be debugged. #comp stands for composite
    """
    <comp_move> is a tuple of moves, each of which is a pair of pairs
    <pieces> is an ndarray representing positions on the board.
    <apply_comp_move_slow> returns the ndarray <local_pieces>,
        with the positions updated with the given moves,
        and displays each step of the composite move.
    Eventually, <apply_comp_move_slow> also toggles the turn.
    """
    global turn
    local_pieces = copy.deepcopy(pieces)
    assert is_composite_move(comp_move), "comp_move = " + str(comp_move)
    for move in comp_move:
        local_pieces = apply_move(move, local_pieces) #slow version updates pieces *globally*
        show_move(local_pieces)
    turn = turn_toggle(turn)
    return local_pieces

def map_moves_to_destinations(moves_tuple):
    """takes a tuple of moves and returns a tuple of destinations
    E.g. map_moves_to_destinations((((1,2),(3,4)),((1,2),(5,6))))
    returns: ((3,4),(5,6))"""
    assert is_moves(moves_tuple), "moves_tuple was %s" % str(moves_tuple)
    if len(moves_tuple) == 0:
        return tuple()
    else:
        return tuple(zip(*moves_tuple))[1]

def distance2_sq(point1, point2):
    assert is_point(point1)
    assert is_point(point2)
    x1, y1 = point1
    x2, y2 = point2
    return (x1-x2)**2 + (y1-y2)**2

def distanceinf(point1, point2):
    assert is_point(point1)
    assert is_point(point2)
    x1, y1 = point1
    x2, y2 = point2
    return max(abs(x1-x2), abs(y1-y2))

def map_point_to_colrow(point): #to be debugged
    assert is_point(point), "point = "+str(point)
    i1 = (mousex-pol)//sspl
    i2 = i1 - 1
    i3 = i1 + 1
    j1 = 7-((mousey-pot)//sspl)
    j2 = j1+1
    j3 = j1-1
    i_l = [i for i in (i1, i2, i3) if i in range(8)]
    j_l = [j for j in (j1, j2, j3) if j in range(8)]
    if i_l != [] and j_l != []:
        for i in i_l:
            for j in j_l:
                center = (squares[i][j][0].centerx, squares[i][j][0].centery)
                if distanceinf(point, center) <= sspl//2:
                    return (i,j)
    return None

def is_A1(string):
    if not isinstance(string, str):
        return False
    if len(string) != 2:
        return False
    if ord(string[0]) not in tuple(range(65, 73)):
        return False
    if not int(string[1]) not in tuple(range(1,9)):
        return False
    return True

def map_colrow_to_A1(pair): #to be debugged
    assert is_colrow(pair), "Pair is: "+str(pair)
    i, j = pair
    char1 = chr(65+i)
    char2 = str(j+1)
    return char1+char2
    
def map_A1_to_colrow(A1): #to be debugged
    assert is_A1(A1)
    i = ord(A1[0])-65
    j = int(A1[1])-1
    return (i,j)

def optim_func(turn):
    """
    e.g. of = optim_func('w')
        of([1,2,3])==3
    e.g. of = optim_func('b') 
        of([1,2,3])==1
    """
    assert turn in ("b","w")
    if turn == 'b':
        return max
    return min
    
def CPU_move(turn, pieces, depth, accelerate_if_nochoice = False):
    """
    e.g. CPU_move('w', pieces, 5)
    e.g. CPU_move('b', pieces, 5)
    It returns a 2-tuple, where:
    the 1st argument is the score of
        the recommended move (based on minmax optimization over <depth>
        turns) and 
    the 2nd one is the tuple of moves (both composite 
        and simple) that would achieve such score if players played 
        according to the minmax strategy.
    The list in the 2nd argument ends with None if there is a 
    gameover situation at the end of it.
    """
    assert turn in ('b', 'w')
    assert isinstance(depth, int)
    assert depth >= 0
    local_pieces = copy.deepcopy(pieces)
    bcm = board_composite_moves(turn, local_pieces)
    bsm = board_simple_moves(turn, local_pieces)
    #If there are no moves, game is over
    if len(bcm)==0 and len(bsm)==0:
        if turn == 'b':
            score = scoring_f_wwin  #this parameter is related to the function scoring_f
            return (score, None)
        elif turn == 'w':
            score = scoring_f_bwin #this parameter is related to the function scoring_f
            return (score, None)
    #Else, if depth == 0, return the score
    if depth == 0:
        score = scoring_f(local_pieces)
        return (score, tuple())
    #Else, recursion
    opt_score = None
    if len(bcm)>0:
        if accelerate_if_nochoice and len(bcm) == 1:
            return (None, bcm)
        for cm in bcm: #if I'm here, depth>0
            next_state = apply_comp_move(cm, local_pieces)
            score_n_moves = CPU_move(turn_toggle(turn), next_state, depth-1)
            score = score_n_moves[0]
            def debugging1():
                pass
            if debugging_mode:
                #debugging starts
                if depth == depth_by_turn(turn):
                    print("turn: ", turn)
                    print("score: ", score)
                    print("moves: ", (cm,) + score_n_moves[1] if score_n_moves[1]!=None else (cm,) + (score_n_moves[1],))
                #debugging ends
            if opt_score == None \
                or (score > opt_score and turn == 'b') \
                or (score < opt_score and turn == 'w'):
                opt_score = score
                moves_in = score_n_moves[1]
                if moves_in != None:
                    moves_out = (cm,) + moves_in
                else:
                    moves_out = (cm,) + (moves_in,)
        return (opt_score, moves_out)
    if len(bsm)>0:
        if accelerate_if_nochoice and len(bsm) == 1:
            return (None, bsm)
        for sm in bsm:
            next_state = apply_move(sm, local_pieces)
            score_n_moves = CPU_move(turn_toggle(turn), next_state, depth-1)
            score = score_n_moves[0]
            if debugging_mode:
                #debugging starts
                if depth == depth_by_turn(turn):
                    print("turn: ", turn)
                    print("score: ", score)
                    print("moves: ", (sm,) + score_n_moves[1] if score_n_moves[1]!=None else (sm,) + (score_n_moves[1],))
                #debugging ends
            if opt_score == None \
                or (score > opt_score and turn == 'b') \
                or (score < opt_score and turn == 'w'):
                opt_score = score
                moves_in = score_n_moves[1]
                if moves_in != None:
                    moves_out = (sm,) + moves_in
                else:
                    moves_out = (sm,) + (moves_in,)
        return (opt_score, moves_out)


#%% Initial display (and Game Loop)
#Board and pieces
pygame.init()
DISPLAYSURF = pygame.display.set_mode((wspl, wspl)) #a Surface object is returned and stored in DISPLAYSURF
pygame.display.set_caption('Checkers Board')
draw_board()
draw_labels()
draw_pieces()
show_turn(turn)
display()

# Game Loop
if debugging_mode:
    c=0                                         #debugging code
    list_of_lists = []                          #debugging code
while True: # main game loop
    def debugging2():
        pass
    mylist = pygame.event.get() #uncomment this after removing occurrences of the same in debugging code below...
    if debugging_mode:
        exitloop = False                        #debugging block starts...
        while not exitloop:                       
            mylist = pygame.event.get()
            for event in mylist:
                if event.type == KEYDOWN:
                    exitloop = True               
                if event.type == QUIT:
                     pygame.quit()
                     sys.exit()                 #...debugging block ends
    if debugging_mode:
        c += len(mylist)                          #debugging block starts...
        if mylist != []:
            while len(list_of_lists) > 2:
                list_of_lists.pop(0)
            list_of_lists.append(mylist)
            print(c, mylist)
            if len(list_of_lists) >= 2:
                if mylist[0].type != list_of_lists[-2][0].type:
                    pass
                    # print(c, mylist)              #...debugging block ends
    if game_is_over(turn, pieces):
        print("GAME OVER: '%s' player cannot move and loses" % (turn,))
        text_rowcol("GAME OVER: '%s' player " % (turn_to_colorname(turn),),\
                    'freesansbold.ttf', 32, (-3, 4), WHITE, BLUE)
        text_rowcol("cannot move and loses",\
                    'freesansbold.ttf', 32, (-4, 4), WHITE, BLUE)
        display()
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                     pygame.quit()
                     sys.exit()
    #HANDLE EVENTS
    #HANDLE EVENTS
    def EVENTS_bookmark():
        pass
    if turn in human_players:
        if state == 'CPU':
            state = 'Standard'
        for event in mylist: #pygame.event.get() returned a list
            if state == 'Standard':
                if event.type == QUIT:
                     pygame.quit()
                     sys.exit()
                elif event.type == MOUSEMOTION:
                    mousex, mousey = event.pos
                elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                    mousex, mousey = event.pos
                    clicked_square_colrow = map_point_to_colrow(event.pos)
                    board_possible_moves = board_moves(turn, pieces)
                    mpcr = movable_pieces_colrows(board_possible_moves)
                    if clicked_square_colrow in mpcr:
                        selected_piece = pieces[clicked_square_colrow]
                        sppm = single_moves(clicked_square_colrow, pieces)
                        state = 'LButtonDown'
                        selected_piece_possible_moves = sppm
                        sppd = tuple(zip(*sppm))[1]
                        selected_piece_possible_destinations = sppd
                        selected_piece_colrow = clicked_square_colrow
                elif event.type == MOUSEBUTTONUP and event.button == 1:
                    mousex, mousey = event.pos
                    state = 'Standard'
            elif state == 'LButtonDown':
                if event.type == QUIT:
                     pygame.quit()
                     sys.exit()
                elif event.type == MOUSEMOTION:
                    mousex, mousey = event.pos
                elif event.type == MOUSEBUTTONUP and event.button == 1:
                    mousex, mousey = event.pos
                    selected_destination = map_point_to_colrow((mousex, mousey))
                    state = 'Standard' #this may be overridden in a bit...
                    if selected_destination in sppd: #sppd=selected_piece_possible_destinations
                        move = (selected_piece_colrow, selected_destination)
                        m_is_cont = move_is_continuable(move, pieces)
                        pieces = apply_move(move, pieces)
                        if m_is_cont:
                            state = 'MiddleOfMove'
                            selected_piece_colrow = selected_destination
                            sppm = eating_moves(selected_piece_colrow, pieces)#notice that only eating moves are considered in this scenario
                            sppd = map_moves_to_destinations(sppm)
                            selected_piece_possible_destinations = sppd
                            selected_piece = pieces[selected_piece_colrow]
                        else:
                            turn = turn_toggle(turn)
                            if turn not in human_players:
                                state = 'CPU' #bc we must override state='Standard'
            elif state == 'MiddleOfMove':
                if event.type == QUIT:
                     pygame.quit()
                     sys.exit()
                elif event.type == MOUSEMOTION:
                    mousex, mousey = event.pos
                elif event.type == MOUSEBUTTONUP and event.button == 1:
                    sppm = eating_moves(selected_piece_colrow, pieces) #sppm=selected_piece_possible_moves
                    sppd = tuple(zip(*sppm))[1] #sppd=selected_piece_possible_destinations
                    mousex, mousey = event.pos
                    selected_destination = map_point_to_colrow((mousex, mousey))
                    if selected_destination in sppd: #sppd=selected_piece_possible_destinations
                        move = (selected_piece_colrow, selected_destination)
                        m_is_cont = move_is_continuable(move, pieces)
                        pieces = apply_move(move, pieces)
                        turn = turn_toggle(turn)
                        if m_is_cont:
                            state = 'MiddleOfMove'
                            turn = turn_toggle(turn) #this is to undo the change of turn applied by apply_comp_move
                            selected_piece_colrow = selected_destination
                            sppm = eating_moves(selected_piece_colrow, pieces)#notice that only eating moves are considered in this scenario
                            sppd = map_moves_to_destinations(sppm)
                            selected_piece_possible_destinations = sppd
                            selected_piece = pieces[selected_piece_colrow]
                        else:
                            state = 'Standard'#notice that we switch to standard only if not m_is_cont
            elif state == 'CPU':
                pass #this can occur if the state has already changed to CPU but the events list mylist still has events to go through
            else:
                raise ValueError("'state' is %s" % (state,))
            if debugging_mode:
                text_rowcol(30*" ", \
                            'freesansbold.ttf', 32, (-5, 4), BLACK, BLACK)#debugging code
                text_rowcol("LButtonDown = "+str(state == 'LButtonDown'), \
                            'freesansbold.ttf', 32, (-5, 4), WHITE, BLUE)#debugging code
    else: #computer plays (we are here "if turn not in human_players")
        def CPU_EVENTS_bookmark():
            pass
        state = 'CPU'
        for event in mylist: #pygame.event.get() returned a list
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
        #Display is done here
        text_rowcol("CPU thinking...", 'freesansbold.ttf', 24, (5, 11), WHITE, BLUE)
        display()
        #Decide move, apply, draw, change turn
        score, moves_seq = CPU_move(turn, pieces, depth_by_turn(turn), accelerate_if_nochoice = True)
        move = moves_seq[0] #this move may be simple or composite
        def debugging3():
            pass
        if debugging_mode:
            #debugging starts
            print("chosen turn: ", turn)
            print("chosen score: ", score)
            print("chosen moves: ", moves_seq)
            #debugging ends
        if is_composite_move(move):
            pieces = apply_comp_move_slow(move, pieces)#this includes delaying and displaying
        elif is_move(move):
            pieces = apply_move(move, pieces)
            show_move(pieces)
            turn = turn_toggle(turn)
        #If we got here, it should be game over. Otherwise, error
        elif not game_is_over(turn, pieces):
            raise ValueError()
        #Display is done here
        text_rowcol("                      ", 'freesansbold.ttf', 32, (5, 11), BLACK, BLACK)
        display()


    #DISPLAY
    #DISPLAY
    def DISPLAY_bookmark():
        pass
    draw_board()
    draw_labels()
    draw_pieces()
    show_turn(turn)
    if state in ('LButtonDown', 'MiddleOfMove'):
        # highlight the selected piece
        # show its destinations
        # display a circle at the current pointer position
        # highlight a destination if the pointer is on it
        draw_piece(position = selected_piece_colrow, \
                   piece = pieces[selected_piece_colrow], \
                   high = True)
        pos = (mousex, mousey)
        current_colrow = map_point_to_colrow(pos)
        for dest in selected_piece_possible_destinations:
            draw_destination(position = dest, \
                             high = (True if dest == current_colrow else False))
        draw_pointer_circle(pos)
    elif state == 'Standard':
        board_possible_moves = board_moves(turn, pieces)
        mpcr = movable_pieces_colrows(board_possible_moves)
        redraw_movable_pieces(mpcr)
        pos = (mousex, mousey)
        current_square_colrow = map_point_to_colrow(pos)
        if current_square_colrow in mpcr:
            possible_moves = single_moves(current_square_colrow, pieces)
            possible_dests = map_moves_to_destinations(possible_moves)
            for dest in possible_dests:
                draw_destination(position = dest, high = False)
    elif state == 'CPU':
        #For the CPU state, the Display part was incorporated with the events part
        pass
    pygame.display.update()
