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

DEFAULT_OBS_FILENAME = '%CCYY-%MM-%DD %hh-%mm-%ss'
VIDEO_FORMAT = 'mkv'
ObsWs = obsws('localhost', 4455)

def stop_recording(filename):
  res = ObsWs.call(obsreq.StopRecord())
  fpath = res.datain['outputPath']
  os.rename(fpath, f"{os.path.dirname(fpath)}/{filename}.{VIDEO_FORMAT}")

def start_recording():
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
  while True:
    if not stage.is_stage('StoryTransition'):
      continue
    if step == STEP_INIT:
      yield from wait_until_transition()
      start_recording()
    elif step == STEP_A:
      stop_recording(f"{video_name}_A.mp4")
      yield from wait_until_transition()
      start_recording()
    elif step == STEP_B:
      stop_recording(f"{video_name}_B.mp4")
      yield from wait_until_transition()
    step += 1

def start_scene(filename):
  yield from safe_click(*position.SceneStart)
  yield from process_recording(filename)
  for _ in range(10):
    wait(0.3)
    yield

def start_recording_fiber():
  idx = -1
  vid = 0
  depth = 0
  while True:
    yield
    if stage.is_stage('Gallery'):
      idx += 1
      if idx >= 7:
        idx = 0
        Input.scroll_to(*position.NextCharacterRowScroll, slow=True)
        wait(0.3)
        yield
      mx, my = position.FirstCharacterAvartar
      mx = mx + position.NextCharacterDeltaX * idx
      yield from safe_click(mx, my)
      chname = yield from get_character_name()
      _G.log_info("Character:", chname)
      vid = 1
      yield from safe_click(*position.FirstScene)
      yield from start_scene(f"{chname}_{vid}")
    elif stage.is_stage('NextScene'):
      vid += 1
      yield from safe_click(*position.ToNextScene)
      yield from start_scene(f"{chname}_{vid}")
      
      