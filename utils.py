import _G
from _G import log_error,log_debug,log_info,log_warning,resume,wait,uwait
import numpy as np
import os
import win32gui, win32process, win32console, win32con
from time import sleep
from random import random
import traceback
import os.path
import psutil
from PIL import Image
from difflib import SequenceMatcher
import graphics

try:
  import pytesseract
except Exception:
  log_warning("Pytesseract not available, OCRs won't be available")

AppCandidates = []

def EnumWindowCallback(hwnd, lparam):
  global AppCandidates
  if win32gui.IsWindowVisible(hwnd):
    title = win32gui.GetWindowText(hwnd)
    if title == _G.AppWindowName:
      AppCandidates.append(hwnd)
      print(f"App found with HWND {hwnd} ({_G.AppWindowName}), pid={_G.AppPid}")

def EnumChildWindowCB(hwnd, lparam):
  clsname = win32gui.GetClassName(hwnd)
  title   = win32gui.GetWindowText(hwnd)
  print(hwnd, clsname, title)
  if title == _G.AppChildWindowName:
    _G.AppChildHwnd = hwnd
    print("Target child found")
    return False

def update_app_rect():
  _G.AppRect = list(win32gui.GetWindowRect(_G.AppHwnd))
  _G.AppRect[2] -= _G.AppRect[0]
  _G.AppRect[3] -= _G.AppRect[1]
  _G.AppRect = tuple(_G.AppRect)
  print(f"Rect updated: {_G.AppRect}")

def find_app_window():
  global AppCandidates
  AppCandidates = []
  win32gui.EnumWindows(EnumWindowCallback, None)
  if not AppCandidates:
    return
  hwnd = AppCandidates[0]
  if len(AppCandidates) > 1:
    print("Multiple app found:")
    for i,hw in enumerate(AppCandidates):
      print(f"[{i}] hwnd={hw} {win32process.GetWindowThreadProcessId(hw)}")
    sn = input("please select one: ")
    hwnd = AppCandidates[sn]
  _G.AppHwnd = hwnd
  _G.AppTid,_G.AppPid = win32process.GetWindowThreadProcessId(hwnd)
  _G.AppProcess = psutil.Process(_G.AppPid)
  print(f"App found with HWND {hwnd} ({_G.AppWindowName}), pid={_G.AppPid}")
  update_app_rect()

def find_child_window():
  log_info("Child windows:")
  win32gui.EnumChildWindows(_G.AppHwnd, EnumChildWindowCB, None)
  print("\n\n")

def move_window(x=None,y=None,w=None,h=None,boardless=False):
  x = x if x != None else _G.AppRect[0]
  y = y if y != None else _G.AppRect[1]
  w = w if w != None else _G.AppRect[2]
  h = h if h != None else _G.AppRect[3]
  if boardless: # warning: irreversible
    _G.WinTitleBarSize = (0, 0)
    _G.WinDesktopBorderOffset = (0, 0)
    ws = win32gui.GetWindowLong(_G.AppHwnd, win32con.GWL_STYLE)
    ws = ws & ~(win32con.WS_CAPTION | win32con.WS_DLGFRAME | win32con.WS_SYSMENU)
    ws = ws & ~(win32con.WS_MINIMIZEBOX | win32con.WS_MAXIMIZEBOX | win32con.WS_THICKFRAME)
    ws = ws & ~(win32con.WS_EX_DLGMODALFRAME  | win32con.WS_EX_CLIENTEDGE | win32con.WS_EX_STATICEDGE)
    win32gui.SetWindowLong(_G.AppHwnd, win32con.GWL_STYLE, ws)
    win32gui.SetWindowPos(
      _G.AppHwnd, win32con.HWND_TOP,
      0, 0, 0, 0,
      win32con.SWP_FRAMECHANGED | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_NOOWNERZORDER
    )
  
  win32gui.MoveWindow(_G.AppHwnd, x, y, w, h, False)
  sleep(0.1)
  update_app_rect()

def resize_app_window(x=None, y=None, w=None, h=None, boardless=False):
  update_app_rect()
  if x == None:
    x = _G.AppRect[0]
  if y == None:
    y = 0
  if w == None:
    w = _G.WindowWidth
  if h == None:
    h = _G.WindowHeight
  move_window(x, y, w, h, boardless)
  sleep(0.1)
  update_app_rect()

def safe_execute_func(func, args=[], kwargs={}):
  try:
    return func(*args, **kwargs)
  except Exception as err:
    err_info = traceback.format_exc()
    handle_exception(err, err_info)
  return _G.MsgPipeError

def handle_exception(err, errinfo):
  _G.log_error(f"An error occured during runtime!\n{str(err)}\n{errinfo}")

def img2str(image_file, lang='jpn', config='--psm 12 --psm 13'):
  if not os.path.exists(image_file) and not image_file.startswith(_G.DCTmpFolder):
    image_file = f"{_G.DCTmpFolder}/{image_file}"
  return pytesseract.image_to_string(image_file, lang=lang, config=config) or ''

def ocr_rect(rect, fname, zoom=1.0, lang='jpn', config='--psm 12 --psm 13', **kwargs):
  log_info(f"Processing OCR for {fname}")
  if kwargs.get('num_only'):
    lang = 'eng'
    config += ' -c tessedit_char_whitelist=1234567890'
  if not os.path.exists(fname):
    fname = f"{_G.DCTmpFolder}/{fname}"
  img = graphics.take_snapshot(rect, fname)
  if zoom != 1.0:
    size = (int(img.size[0]*zoom), int(img.size[1]*zoom))
    graphics.resize_image(size, fname, fname)
  sleep(0.3)
  img.close()
  return img2str(fname, lang, config).translate(str.maketrans('。',' ')).strip()

def diff_string(a,b):
  return SequenceMatcher(None,a,b).ratio()

def isdigit(n):
  try:
    _ = int(n)
    return True
  except Exception:
    return False

def str2int(ss):
  try:
    return int("".join([n for n in ss if isdigit(n)]))
  except ValueError:
    return None

def ensure_dir_exist(path):
  path = path.split('/')
  path.pop()
  if len(path) == 0:
    return
  pwd = ""
  for dir in path:
    pwd += f"{dir}/"
    if not os.path.exists(pwd):
      os.mkdir(pwd)

def EnumWindowSelfCB(hwnd, lparam):
  _G.SelfPid = win32process.GetCurrentProcessId()
  if win32process.GetWindowThreadProcessId(hwnd) == _G.SelfPid:
    _G.SelfHwnd = hwnd
    return False
  return True

def get_self_hwnd():
  if _G.IS_WIN32:
    _G.SelfHwnd = win32console.GetConsoleWindow()
    if _G.SelfHwnd == 0:
      win32gui.EnumWindows(EnumWindowSelfCB, None)
    return _G.SelfHwnd

def is_focused():
  if _G.IS_WIN32:
    hwnd = win32gui.GetForegroundWindow()
    return hwnd == _G.SelfHwnd or hwnd == _G.AppHwnd
  return True

def pause_process(proc=None):
  if not proc:
    proc = _G.AppProcess
  _G.log_info("Pausing process", proc.name())
  proc.suspend()

def resume_process(proc=None):
  if not proc:
    proc = _G.AppProcess
  _G.log_info("Resume process", proc.name())
  proc.resume()