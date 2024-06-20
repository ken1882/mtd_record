import _G, graphics
import win32api, win32con 
import random, math
from time import sleep
from _G import (resume,wait,uwait,log_debug,log_error,log_info,log_warning,make_lparam)

ScrollTime  = 0.03
ScrollDelta = [1,5]

keystate = [0 for _ in range(0xff)]

def update():
  global keystate
  for i in range(0xff):
    if win32api.GetAsyncKeyState(i):
      keystate[i] += 1
    else:
      keystate[i] = 0

def is_trigger(vk):
  return keystate[vk] == 1

def is_pressed(vk):
  return keystate[vk] > 0

def repeat(vk):
  return keystate[vk]

# app_offset: use DC pos instead of global pos
def get_cursor_pos(app_offset=True):
  mx, my = win32api.GetCursorPos()
  if app_offset:
    mx = mx - _G.AppRect[0] - _G.WinTitleBarSize[0] - _G.WinDesktopBorderOffset[0]
    my = my - _G.AppRect[1] - _G.WinTitleBarSize[1] - _G.WinDesktopBorderOffset[1]
  return (mx, my)

def key_down(*args):
  for kid in args:
    win32api.keybd_event(kid, 0, 0, 0)

def key_up(*args):
  for kid in args:
    win32api.keybd_event(kid, 0, win32con.KEYEVENTF_KEYUP, 0)

def trigger_key(*args):
  for kid in args:
    key_down(kid)
  sleep(0.03)
  for kid in args:
    key_up(kid)

def mouse_down(x=None, y=None, app_offset=True, use_msg=_G.AppInputUseMsg, hwnd=None):
  if not hwnd:
    hwnd = _G.AppInputHwnd
  if use_msg:
    hwnd = hwnd if hwnd else _G.AppHwnd
    win32api.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, make_lparam(x,y))
    return
  rect = None
  if x is None:
    x = 0
  if y is None:
    y = 0
  if app_offset:
    rect = graphics.get_content_rect()
    x += rect[0]
    y += rect[1]
  if x or y:
    win32api.SetCursorPos((x,y))
  win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,x,y,0,0)

def mouse_up(x=None, y=None, app_offset=True, use_msg=_G.AppInputUseMsg, hwnd=None):
  if not hwnd:
    hwnd = _G.AppInputHwnd
  if use_msg:
    hwnd = hwnd if hwnd else _G.AppHwnd
    win32api.SendMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, make_lparam(x,y))
    return
  rect = None
  if app_offset:
    rect = graphics.get_content_rect()
  if x is None:
    x = 0
  elif app_offset:
    x += rect[0]
  if y is None:
    y = 0
  elif app_offset:
    y += rect[1]
  if x or y :
    win32api.SetCursorPos((x,y))
  win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,x,y,0,0)

def set_cursor_pos(x, y, app_offset=True, use_msg=_G.AppInputUseMsg, hwnd=None, wparam=None):
  if not hwnd:
    hwnd = _G.AppInputHwnd
  if use_msg:
    hwnd = hwnd if hwnd else _G.AppHwnd
    win32api.SendMessage(hwnd, win32con.WM_MOUSEMOVE, wparam, make_lparam(x,y))
    return
  if app_offset:
    rect = graphics.get_content_rect()
    x += rect[0]
    y += rect[1]
  win32api.SetCursorPos((int(x),int(y)))

def click(x=None, y=None, app_offset=True, use_msg=_G.AppInputUseMsg, hwnd=None, dur=0.05):
  if not hwnd:
    hwnd = _G.AppInputHwnd
  x = int(x)
  y = int(y)
  if not use_msg and x and y:
    set_cursor_pos(x, y, app_offset)
  mouse_down(x, y, app_offset, use_msg, hwnd)
  sleep(dur)
  mouse_up(x, y, app_offset, use_msg, hwnd)

def rclick(x, y, app_offset=True, use_msg=_G.AppInputUseMsg, hwnd=None, rrange=_G.PosRandomRange):
  mx = int(x) + random.randint(-rrange[0], rrange[0])
  my = int(y) + random.randint(-rrange[1], rrange[1])
  click(mx, my, app_offset, use_msg, hwnd)

def dclick(x=None, y=None, app_offset=True, use_msg=_G.AppInputUseMsg, hwnd=None):
  if not hwnd:
    hwnd = _G.AppInputHwnd
  click(x,y,app_offset, use_msg, hwnd)
  sleep(0.1)
  click(x,y,app_offset, use_msg, hwnd)

def scroll_up(x, y, delta = 100, app_offset=True, haste=False):
  mouse_down(x, y, app_offset)
  ty = y + delta
  sleep(0.01 if haste else 0.5)
  while y <= ty:
    y += (random.randint(*ScrollDelta) + haste * 2)
    set_cursor_pos(x, min([y,ty]), app_offset)
    wait(0.01 if haste else ScrollTime)
  mouse_up(x, y, app_offset)

def scroll_down(x, y, delta = 100, app_offset=True, haste=False):
  mouse_down(x, y, app_offset)
  ty = y - delta
  sleep(0.01 if haste else 0.5)
  while y >= ty:
    y -= (random.randint(*ScrollDelta) + haste * 2)
    set_cursor_pos(x, max([y,ty]), app_offset)
    wait(0.01 if haste else ScrollTime)
  mouse_up(x, y, app_offset)

def scroll_left(x, y, delta = 100, app_offset=True, haste=False):
  mouse_down(x, y, app_offset)
  tx = x + delta
  sleep(0.01 if haste else 0.5)
  while x <= tx:
    x += (random.randint(*ScrollDelta) + haste * 2)
    set_cursor_pos(min([x,tx]), y, app_offset)
    wait(0.01 if haste else ScrollTime)
  mouse_up(x, y, app_offset)

def scroll_right(x, y, delta = 100, app_offset=True, haste=False):
  mouse_down(x, y, app_offset)
  tx = x - delta
  sleep(0.01 if haste else 0.5)
  while x >= tx:
    x -= (random.randint(*ScrollDelta) + haste * 2)
    set_cursor_pos(max([x,tx]), y, app_offset)
    wait(0.01 if haste else ScrollTime)
  mouse_up(x, y, app_offset)

def scroll_to(x, y, x2, y2, app_offset=True, haste=False, hold=True, slow=False, use_msg=False):
  mouse_down(x, y, app_offset, use_msg=use_msg)
  sleep(0.01 if haste else ScrollTime)
  tdx, tdy = abs(x2 - x), abs(y2 - y)
  try:
    pcx, pcy = tdx // tdy, tdy // tdx
    pcx, pcy = min([max([pcx, 0.4]), 2]), min([max([pcy, 0.4]), 2])
  except Exception:
    pcx, pcy = 1, 1
  
  while x != x2 or y != y2:
    dx = int((random.randint(*ScrollDelta) + haste * 2) * pcx)
    dy = int((random.randint(*ScrollDelta) + haste * 2) * pcy)
    dx = 1 if dx > 0 and slow else dx
    dy = 1 if dy > 0 and slow else dy
    dx = 1 if dx == 0 and x != x2 else dx
    dy = 1 if dy == 0 and y != y2 else dy
    x = min([x2, x+dx]) if x2 > x else max([x2, x-dx])
    y = min([y2, y+dy]) if y2 > y else max([y2, y-dy])
    set_cursor_pos(x, y, app_offset, use_msg=use_msg)
    wait(0.01 if haste else ScrollTime)
  if hold:
    sleep(1)
  mouse_up(x, y, app_offset, use_msg=use_msg)


MaxMoveTimes = 42
def moveto(x,y,speed=10,max_steps=MaxMoveTimes,app_offset=True,aync=True,rand=True):
  global MaxMoveTimes
  if max_steps <= 0:
    max_steps = 0x7fffffff
  if app_offset:
    rect = graphics.get_content_rect()
    x += rect[0]
    y += rect[1]
  cx,cy = get_cursor_pos(False)
  dx = x - cx
  dy = y - cy
  times = int(math.hypot(dx,dy) // speed)
  if times > max_steps:
    times = max_steps
    speed = math.hypot(dx,dy) // max_steps
  angle = math.atan2(dy,dx)
  dx = speed * math.cos(angle)
  dy = speed * math.sin(angle)
  for _ in range(times):
    cx += dx
    cy += dy
    rx,ry = 0,0
    if rand:
      rx = random.randint(-_G.PosRandomRange[0],_G.PosRandomRange[0]) // 2
      ry = random.randint(-_G.PosRandomRange[1],_G.PosRandomRange[1]) // 2
      rx = rx // 2 if dx > dy else rx
      ry = ry // 2 if dy > dx else ry
    set_cursor_pos(cx+rx, cy+ry, False)
    wait(0.01)
  set_cursor_pos(x, y, False)

def rmoveto(x,y,rrange=10,**kwargs):
  moveto(x+random.randint(-rrange, rrange), y+random.randint(-rrange, rrange), **kwargs)