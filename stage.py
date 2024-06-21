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
  'Gallery2': {
    'pos': ((40, 18),(143, 31),(660, 1020),(1792, 945),),
    'color': ((243, 232, 218),(79, 70, 71),(134, 91, 82),(95, 150, 87),)
  },
  'StoryMain': {
    'pos': ((1125, 839),(1220, 841),(1275, 839),(1364, 842),(1427, 840),(1594, 841),),
    'color': ((84, 75, 74),(84, 75, 74),(84, 75, 74),(84, 75, 74),(84, 75, 74),(220, 196, 178),)
  },
  'StoryMain2': {
    'pos': ((1267, 839),(1126, 835),(1355, 825),(1457, 823),(1579, 839),(1122, 839),),
    'color': ((84, 75, 74),(84, 75, 74),(82, 73, 71),(82, 72, 71),(220, 196, 178),(84, 75, 74),)
  },
  'StoryAuto': {
    'pos': ((1124, 836),(1216, 841),(1275, 842),(1364, 843),(1503, 822),(1593, 840),),
    'color': ((84, 75, 74),(84, 75, 74),(104, 244, 208),(84, 75, 74),(82, 72, 71),(220, 196, 178),)
  },
  'StoryAuto2': {
    'pos': ((1122, 836),(1266, 843),(1409, 829),(1490, 824),(1579, 842),),
    'color': ((84, 75, 74),(100, 243, 206),(84, 74, 74),(82, 73, 71),(220, 196, 178),)
  },
  'StoryAuto3': {
    'pos': ((1126, 830),(1272, 842),(1341, 825),(1465, 823),(1577, 840),),
    'color': ((84, 74, 74),(101, 243, 207),(82, 73, 71),(82, 72, 71),(220, 196, 178),)
  },
  'StoryTransition': {
    'pos': (((211, 131),(799, 142),(1681, 161),(217, 467),(995, 473),(1696, 466),(224, 866),(978, 849),(1715, 829),)),
    'color': ((0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0),(0, 0, 0))
  },
  'NextScene': {
    'pos': ((151, 34),(555, 443),(1310, 457),(729, 653),(1026, 650),(1797, 947),),
    'color': ((39, 35, 35),(79, 70, 71),(79, 70, 71),(109, 218, 180),(255, 131, 159),(47, 75, 43),)
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
