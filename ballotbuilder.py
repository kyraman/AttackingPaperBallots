from reportlab.platypus import PageBreak, Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import landscape, letter as PAGESIZE, A4
from PIL import Image
from enum import Enum
from pdf2image import convert_from_path
import argparse

from reportlab.lib.colors import PCMYKColor, PCMYKColorSep, Color, black as BLACK, lightgrey as GREY, grey as DARKGREY
from reportlab.lib.units import inch

NUM_H_MARKS = 34
NUM_V_MARKS = 41

MARK_HEIGHT = 0.05*inch
MARK_WIDTH = 0.17*inch

BUBBLE_HEIGHT = 0.09*inch
BUBBLE_WIDTH = 0.18*inch

H_MARGIN = 0.08*inch
V_MARGIN_TOP = 0.25*inch
V_MARGIN_SUM = 1.14*inch
V_MARGIN_BOT = V_MARGIN_SUM - V_MARGIN_TOP
class Attacks(Enum):
    NONE = 0
    YES = 1
    NO = 2
    SHIFT = 3
    # FAKE_YES = 4
    # FAKE_NO = 5
    BAD_YES = 6
    BAD_NO = 7

def defineAttack(n):
    if n == 0:
        return {}
    if n == 1:
        return {
            '1A': Attacks.BAD_YES
        }
    if n == 2:
        return {
            '1B': Attacks.SHIFT
        }
    # ERROR - defaulting to regular ballot
    return {}

def calculate_coords(page_size, block_size, num_blocks, small_margin, big_margin):
    single_size = (page_size - small_margin - big_margin - block_size) / (num_blocks - 1)
    return [small_margin + x * single_size for x in range(num_blocks)]

def drawTimingMark(c, x, y):
    c.rect(x, y, MARK_WIDTH, MARK_HEIGHT, fill=1)

def drawTimingMarks(c):
    # h_margin = 
    vertical = calculate_coords(PAGESIZE[1], MARK_HEIGHT, NUM_V_MARKS, V_MARGIN_BOT, V_MARGIN_TOP)
    horizontal = calculate_coords(PAGESIZE[0], MARK_WIDTH, NUM_H_MARKS, H_MARGIN, H_MARGIN)

    horizontalSkips = {}
    verticalSkips = {}

    right_side = PAGESIZE[0] - H_MARGIN - MARK_WIDTH
    for n, v in enumerate(vertical):
        if n in verticalSkips:
            continue
        drawTimingMark(c, H_MARGIN, v)
        drawTimingMark(c, right_side, v)

    top_side = PAGESIZE[1] - V_MARGIN_TOP - MARK_HEIGHT
    for n, h in enumerate(horizontal):
        if n in horizontalSkips:
            continue
        drawTimingMark(c, h, top_side)
    
    for x in [1, -3, -2, NUM_H_MARKS // 2]:
        drawTimingMark(c, horizontal[x], vertical[0])

    return horizontal, vertical
    

def drawBubble(c, x, y, fill=0, text=None):
    c.ellipse(x, y, x+BUBBLE_WIDTH, y+BUBBLE_HEIGHT, fill=fill)
    if text is not None:
        c.drawString(x + BUBBLE_WIDTH + 0.05*inch, y, text)

def drawQuestion(c, indices, axes, attack=None, yes_fill=0, no_fill=0):
    x_ax, y_ax = axes

    x = x_ax[indices[0]]
    y = y_ax[indices[1]]
    y_yes = y_ax[indices[1] + 1]

    # Pre bubble
    if attack is not None:
        if attack == Attacks.YES:
            yes_fill = 1
        elif attack == Attacks.NO:
            no_fill = 1
        elif attack == Attacks.SHIFT:
            y, y_yes = y_yes, 2*y_yes - y

    c.setStrokeColor(GREY)
    drawBubble(c, x, y, fill=no_fill, text='NO')
    drawBubble(c, x, y_yes, fill=yes_fill, text='YES')

    # Post bubble
    if attack is not None:
        if attack == Attacks.BAD_YES or attack == Attacks.BAD_NO:
            c.setStrokeColor(DARKGREY)
            line_y = y_yes if attack == Attacks.BAD_YES else y
            line_y += BUBBLE_HEIGHT/2
            c.line(x-0.035*inch, line_y, x+0.01*inch, line_y)

def drawRectangle(c, indices, dimensions, axes):
    x_ax, y_ax = axes
    width, height = dimensions

    unit_width = x_ax[1] - x_ax[0]
    unit_height = y_ax[1] - y_ax[0]

    x = x_ax[indices[0]] - (unit_width - MARK_WIDTH) / 2
    y = y_ax[indices[1]] - (unit_height - MARK_HEIGHT) / 2

    c.setStrokeColor(BLACK)
    c.rect(x, y, width * unit_width, height * unit_height)

def drawQuestions(c, axes, attacks={}):
    questions = {
        '1A': ((1, 19), (11, 15)), 
        '1C': ((12, 19), (11, 15)),
        '1E': ((23, 21), (10, 13)),
        '1B': ((1, 10), (11, 9)),
        '1D': ((12, 9), (11, 10)),
        '1F': ((23, 5), (10, 16)),
    }

    # filled in bubbles
    answers = { # 0 = No answer, 1 = Yes, 2 = No, 3 = Both
        '1A': 1,
        '1C': 2,
        '1E': 1,
        '1B': 1,
        '1D': 1,
        '1F': 2,
    }

    # attacks = {
    #     '1A': Attacks.BAD_YES,
    #     '1B': Attacks.SHIFT,
    # } if attacks is None else attacks

    for q, params in questions.items():
        indices, dimensions = params
        drawRectangle(c, indices, dimensions, axes)
        a = answers.get(q, 0)
        drawQuestion(c, indices, axes, attacks.get(q, None), yes_fill=a%2, no_fill=a//2)

def saveCanvas(c, pdfName, name):
    c.save()
    convert_from_path(pdfName, dpi=153)[0].save(name, 'JPEG')

def runAttack(args):
    pdfName = 'test.pdf'
    c = canvas.Canvas(pdfName, pagesize=PAGESIZE)
    c.setStrokeColor(BLACK)
    pdfmetrics.registerFont(TTFont('answer_font', 'Raleway-Regular.ttf'))
    c.setFont('answer_font', 10)

    axes = drawTimingMarks(c)
    drawQuestions(c, axes, defineAttack(args.attack))

    saveCanvas(c, pdfName, args.output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ballot Attacker Parser")
    parser.add_argument('attack', type=int, nargs='?', help="Attack number. If blank, no attack used.", default=0)
    parser.add_argument('output', type=str, nargs='?', help="JPG file to output", default='test.jpg')
    runAttack(parser.parse_args())