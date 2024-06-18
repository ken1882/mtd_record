from copy import copy
import enum
from time import sleep

import cv2
import numpy as np
from desktopmagic.screengrab_win32 import getRectAsImage

import _G
import graphics
import position
import utils
from _G import log_debug, log_error, log_info, log_warning, resume, uwait, wait
from _G import CVMatchHardRate,CVMatchMinCount,CVMatchStdRate,CVLocalDistance
from utils import img2str, isdigit, ocr_rect
import re

Enum = {
  'Gallery': {
    'pos': ((14, 30),(127, 35),(290, 35),(653, 1026),(1826, 945),),
    'color': ((249, 239, 227),(79, 70, 71),(79, 70, 71),(134, 91, 82),(95, 150, 87),)
  },
  'StoryMain': {
    'pos': ((1125, 839),(1220, 841),(1275, 839),(1364, 842),(1427, 840),(1594, 841),),
    'color': ((84, 75, 74),(84, 75, 74),(84, 75, 74),(84, 75, 74),(84, 75, 74),(220, 196, 178),)
  },
  'StoryAuto': {
    'pos': ((1124, 836),(1216, 841),(1275, 842),(1364, 843),(1503, 822),(1593, 840),),
    'color': ((84, 75, 74),(84, 75, 74),(104, 244, 208),(84, 75, 74),(82, 72, 71),(220, 196, 178),)
  },
  'StoryTransition': {
    'pos': ((38, 172),(40, 276),(57, 407),(127, 529),(129, 733),(257, 926),(630, 774),(529, 442),(1127, 494),(910, 771),(1527, 932),(1703, 773),(1738, 388),(1476, 242),(1288, 515),(1165, 726),(1674, 970),(1730, 712),(1091, 289),(1011, 554),(522, 628),(1123, 450),(25, 26),(1870, 45),(812, 49),),
    'color': ((0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),)
  }
}

def get_current_stage():
  global Enum
  if _G.LastFrameCount != _G.FrameCount:
    _G.CurrentStage = None
    _G.LastFrameCount = _G.FrameCount
  else:
    return _G.CurrentStage
  
  for key in Enum:
    stg = Enum[key]
    if graphics.is_pixel_match(stg['pos'], stg['color']):
      _G.CurrentStage = key
      return key

  return None

def check_pixels(pixstruct):
  return graphics.is_pixel_match(pixstruct['pos'], pixstruct['color'])

StageDepth = 0
LastStage = '_'
def is_stage(stg):
  global LastStage,StageDepth
  s = get_current_stage()
  if s != LastStage:
    _G.log_info("Current stage:", s)
    LastStage = s
    StageDepth = 0
  else:
    StageDepth += 1
  return s and stg in s
