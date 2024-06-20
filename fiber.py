import _G
from _G import wait
import stage, utils, graphics, Input, position
import os
from glob import glob
import logging
from datetime import datetime
from obswebsocket import obsws
from obswebsocket import requests as obsreq

logging.basicConfig(level=logging.INFO)

VIEDO_OUTPUT_DIR = 'G:/cache'
VIDEO_DEST_DIR   = 'G:/cache/mtd'
DEFAULT_OBS_FILENAME = '%CCYY-%MM-%DD %hh-%mm-%ss'
VIDEO_FORMAT = 'mkv'
FlagRecordingStarted = False
ObsWs = obsws('localhost', 4455)

def stop_recording(filename):
  global FlagRecordingStarted
  if not FlagRecordingStarted:
    return
  FlagRecordingStarted = False
  res = ObsWs.call(obsreq.StopRecord())
  fpath = res.datain['outputPath']
  while True:
    try:
      wait(0.03)
      os.rename(fpath, f"{VIDEO_DEST_DIR}/{filename}.{VIDEO_FORMAT}")
      break
    except PermissionError:
      pass

def start_recording():
  global FlagRecordingStarted
  FlagRecordingStarted = True
  ObsWs.call(obsreq.StartRecord())

def safe_click(x, y, dur=1, **kwargs):
  times = int(dur // 0.05)
  for _ in range(times):
    wait(0.05)
    yield
  Input.rclick(x, y, **kwargs)
  for _ in range(times):
    wait(0.05)
    yield

def get_character_name():
  yield from safe_click(*position.CharProfile)
  yield from safe_click(*position.DefaultSkin)
  ret = utils.ocr_rect(position.CharacterNameRect, fname='chname.png')
  yield from safe_click(*position.GeneralBack)
  return ret

def wait_until_transition():
  while stage.is_stage('StoryTransition'):
    yield
  wait(0.5)

def process_recording(video_name):
  STEP_INIT = 0
  STEP_A  = 1
  STEP_B  = 2
  step = 0
  _G.log_info("Start recording")
  _G.flush()
  while True:
    yield
    if not stage.is_stage('StoryTransition') and not stage.is_stage('NextScene'):
      continue
    if stage.is_stage('NextScene'):
      _G.log_warning("Scene probably has undetected trasition!")
    _G.log_info("Scene step:", step)
    if step == STEP_INIT:
      yield from wait_until_transition()
      start_recording()
      while not stage.is_stage('StoryMain'):
        wait(0.3)
        yield
      Input.click(*position.AutoAdvance, dur=0.2)
      for _ in range(60):
        wait(0.98)
        yield
    elif step == STEP_A:
      stop_recording(f"{video_name}_A.mp4")
      yield from wait_until_transition()
      start_recording()
      for _ in range(180):
        wait(0.98)
        yield
    elif step == STEP_B:
      stop_recording(f"{video_name}_B.mp4")
      yield from wait_until_transition()
      break
    step += 1

def start_scene(filename):
  Input.rclick(*position.SceneStart)
  yield from process_recording(filename)
  for _ in range(10):
    wait(0.3)
    yield

def is_last_page():
  pass

def start_recording_fiber():
  global ObsWs
  ObsWs.connect()
  idx = _G.ARGV.index
  vid = 0
  depth = 0
  _G.log_info("Starting index:", idx)
  while True:
    yield
    if stage.is_stage('Gallery'):
      if not _G.ARGV.all and idx:
        break
      if idx >= 5:
        _G.log_info("Next row")
        idx = 0
        Input.scroll_to(*position.NextCharacterRowScroll, slow=True)
        wait(0.3)
        yield
      mx, my = position.FirstCharacterAvartar
      mx = mx + position.NextCharacterDeltaX * idx
      _G.log_info(mx, my)
      yield from safe_click(mx, my)
      chname = yield from get_character_name()
      _G.log_info("Character:", chname)
      vid = 1
      exists = glob(f"{VIDEO_DEST_DIR}/{chname}*.{VIDEO_FORMAT}")
      if exists:
        _G.log_info("Character scene already exists:\n", '\n'.join(exists))
        vid += len(exists) // 2
      yield from safe_click(*position.FirstScene)
      yield from start_scene(f"{chname}_{vid}")
      idx += 1
    elif stage.is_stage('NextScene'):
      if not _G.ARGV.all and idx:
        break
      vid += 1
      yield from safe_click(*position.ToNextScene)
      yield from start_scene(f"{chname}_{vid}")
      
      