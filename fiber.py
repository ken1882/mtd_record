import _G
from _G import wait
import stage, utils, graphics, Input
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
  yield from safe_click(229, 597)
  yield from safe_click(221, 888)
  ret = utils.ocr_rect((1096, 182, 1375, 226), fname='chname.png')
  yield from safe_click(52, 47)
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


def start_recording_fiber():
  # Input.scroll_to(1820, 477, 1820, 301, slow=True)
  while True:
    yield
    vid = 1
    chname = yield from get_character_name()
    _G.log_info("Character:", chname)
    yield from safe_click(467, 651)
    yield from safe_click(961, 635)
    yield from process_recording(f"{chname}_{vid}")
    break