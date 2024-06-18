import cv2
import numpy as np
import win32gui
from desktopmagic.screengrab_win32 import getRectAsImage
from PIL import Image

import _G
import Input
from _G import log_debug, log_error, log_info, log_warning, resume, uwait, wait, flush
from _G import (CVLocalDistance, CVMatchHardRate, CVMatchMinCount, CVMatchStdRate)

_G.DesktopDC = win32gui.GetDC(0)

def is_color_ok(cur, target, bias=None):
  if bias == None:
    bias = _G.ColorBiasRange
  log_debug("=== Pixel Color Comparing ===")
  for c1,c2 in zip(cur,target):
    if _G.VerboseLevel >= 4:
      print('-'*10)
      print(c1, c2)
    if abs(c1 - c2) > bias:
      return False
  return True

def is_pixel_match(pix, col):
  for i, j in zip(pix, col):
    tx, ty = i
    if not is_color_ok(get_pixel(tx, ty), j):
      return False
  return True

def get_pixel(x,y,sync=False):
  # use win32api to get pixel in real time, slower
  if sync:
    rect = get_full_rect()
    x += rect[0]
    y += rect[1]
    rgb = win32gui.GetPixel(_G.DesktopDC, x, y)
    b = (rgb & 0xff0000) >> 16
    g = (rgb & 0x00ff00) >> 8
    r = (rgb & 0x0000ff)
    return (r,g,b)
  # take DC snapshot first, faster
  dc = take_snapshot()
  return dc.getpixel((x,y))

def get_mouse_pixel(mx=None, my=None):
  if not mx and not my:
    mx, my = Input.get_cursor_pos()
  r,g,b = get_pixel(mx, my, True)
  return ["({}, {}),".format(mx, my), "({}, {}, {}),".format(r,g,b)]

def get_full_rect():
  return (
    _G.AppRect[0] + _G.WinTitleBarSize[0] + _G.WinDesktopBorderOffset[0],
    _G.AppRect[1] + _G.WinTitleBarSize[1] + _G.WinDesktopBorderOffset[1],
    _G.AppRect[2],
    _G.AppRect[3]
  )

def get_content_rect():
  rect = list(win32gui.GetClientRect(_G.AppHwnd))
  rect[0] += _G.WinTitleBarSize[0] + _G.WinDesktopBorderOffset[0] + _G.AppRect[0]
  rect[1] += _G.WinTitleBarSize[1] + _G.WinDesktopBorderOffset[1] + _G.AppRect[1]
  rect[2] += _G.WinTitleBarSize[0] - _G.WinTitleBarSize[0]
  rect[3] += _G.WinTitleBarSize[1] - _G.WinTitleBarSize[1]
  return tuple(rect)

def take_snapshot(rect=None,filename=None):
  if not filename:
    filename = _G.DCSnapshotFile
  offset = list(get_content_rect())
  if not rect:
    rect = offset
    rect[2] += rect[0]
    rect[3] += rect[1]
  else:
    rect = list(rect)
    rect[0] += offset[0]
    rect[1] += offset[1]
    rect[2] += offset[0]
    rect[3] += offset[1]
  # note: cache will be flushed every frame during main_loop
  if _G.LastFrameCount == _G.FrameCount and filename in _G.SnapshotCache:
    return _G.SnapshotCache[filename]
  else:
    _G.LastFrameCount = _G.FrameCount
  depth = 0
  while True:
    try:
      return _take_snapshot(rect, filename)
    except Exception as err:
      if depth > 5:
        raise err
      log_error("Error while taking snapshot, waiting for 5 seconds")
      wait(5)

def _take_snapshot(rect,filename):
  path = filename if filename.startswith(_G.DCTmpFolder) else f"{_G.DCTmpFolder}/{filename}"
  getRectAsImage(tuple(rect)).save(path, format='png')
  img = Image.open(path)
  _G.SnapshotCache[filename] = img 
  return img 

def resize_image(size, src_fname, dst_fname):
  img = Image.open(src_fname)
  ret = img.resize(size)
  ret.save(dst_fname)
  return ret 

def filter_local_templates(mat, threshold):
  '''
  Used in cv2.matchTemplate in order to find most likely point of bitmap
  '''
  global CVLocalDistance
  matched = []
  for y,ar in enumerate(mat):
    x = np.where(ar == np.max(ar))[0][0]
    if ar[x] > threshold:
      matched.append((x,y,ar[x]))
  filtered = []
  last_y = -CVLocalDistance
  last_r = 0
  cur_xy = (-1,-1)
  log_debug("Matched template points:")
  for x,y,rate in matched:
    log_debug(f"{(x,y)} rate")
    if abs(y - last_y) > CVLocalDistance:
      last_r = 0
      last_y = y
      if cur_xy[0] >= 0:
        filtered.append(cur_xy)
      cur_xy = (-1,-1)

    if abs(y - last_y) <= CVLocalDistance and rate > last_r:
      cur_xy = (x,y)
      last_y = y
      last_r = rate
  
  if cur_xy[0] >= 0:
    filtered.append(cur_xy)
  return filtered

def find_object(objimg_path, threshold=CVMatchHardRate):
  take_snapshot()
  src = cv2.imread(f"{_G.DCTmpFolder}/{_G.DCSnapshotFile}")
  tmp = cv2.imread(objimg_path)
  res = cv2.matchTemplate(src, tmp, cv2.TM_CCOEFF_NORMED)
  ret = filter_local_templates(res, threshold)
  return [(int(p[0]),int(p[1])) for p in ret]

def find_object_with_rates(objimg_path, threshold=CVMatchHardRate):
  take_snapshot()
  src = cv2.imread(f"{_G.DCTmpFolder}/{_G.DCSnapshotFile}")
  tmp = cv2.imread(objimg_path)
  res = cv2.matchTemplate(src, tmp, cv2.TM_CCOEFF_NORMED)
  objects = filter_local_templates(res, threshold)
  rates = [res[y][x] for x,y in objects]
  return (objects, rates)

def get_difficulty():
  diffculty = [
    [(314, 507), (42, 84, 170)],
    [(314, 507), (215, 76, 0)],
    [(314, 507), (137, 88, 161)],
  ]
  for i,o in enumerate(diffculty):
    p,c = o
    if is_color_ok(get_pixel(*p, True), c):
      return i
  return -1
