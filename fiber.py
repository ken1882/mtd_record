import _G
from _G import wait
import stage, utils, graphics, Input, position
import os
from glob import glob
import logging
import re
from datetime import datetime,timedelta
from obswebsocket import obsws
from obswebsocket import requests as obsreq

logging.basicConfig(level=logging.INFO)

VIEDO_OUTPUT_DIR = 'G:/cache'
VIDEO_DEST_DIR   = 'G:/cache/mtd'
DEFAULT_OBS_FILENAME = '%CCYY-%MM-%DD %hh-%mm-%ss'
VIDEO_FORMAT = 'mkv'
MAX_RECORDING_TIME = timedelta(minutes=30)

FlagRecordingStarted = False
ObsWs = obsws('localhost', 4455)
RecordStartTime = None

def stop_recording(filename=None, rm=False):
  global FlagRecordingStarted,RecordStartTime
  if not FlagRecordingStarted:
    return
  RecordStartTime = None
  FlagRecordingStarted = False
  res = ObsWs.call(obsreq.StopRecord())
  fpath = res.datain['outputPath']
  if rm:
    while True:
      try:
        wait(0.03)
        os.remove(fpath)
        break
      except PermissionError:
        pass
    return
  if not filename:
    return
  filename = re.sub(r'[\\/:*?"<>|]', '-', filename)
  while True:
    try:
      wait(0.03)
      os.rename(fpath, f"{VIDEO_DEST_DIR}/{filename}.{VIDEO_FORMAT}")
      break
    except PermissionError:
      pass

def start_recording():
  global FlagRecordingStarted,RecordStartTime
  FlagRecordingStarted = True
  RecordStartTime = datetime.now()
  ObsWs.call(obsreq.StartRecord())

def safe_click(x, y, dur=1, **kwargs):
  times = int(dur // 0.05)
  for _ in range(times):
    wait(0.05)
    yield
  Input.click(x, y, **kwargs)
  for _ in range(times):
    wait(0.05)
    yield

def get_character_name():
  yield from safe_click(*position.CharProfile2)
  yield from safe_click(*position.CharProfile)
  yield from safe_click(*position.DefaultSkin)
  ret  = utils.ocr_rect(position.CharacterNameRect, fname='chname.png')
  ret2 = utils.ocr_rect(position.CharacterRaceRect, fname='chrace.png')
  yield from safe_click(*position.GeneralBack)
  return f"{ret2}_{ret}"

def wait_until_transition(st=0, ed=3):
  depth = st
  while True:
    yield
    if stage.is_stage('StoryAuto'):
      break
    if stage.is_stage('StoryTransition') or stage.is_stage('Scene') or stage.is_stage('Gallery'):
      depth += 1
      _G.log_info("Transition depth:", depth)
      if depth > ed:
        break
    else:
      depth = 0
  while stage.is_stage('StoryTransition'):
    yield

def process_recording(video_name):
  STEP_INIT = 0
  STEP_A  = 1
  STEP_B  = 2
  chord   = 'B'
  step = 0
  _G.log_info("Start recording")
  _G.flush()
  flag_pass = False
  depth = 0
  flag_end = False
  dep_threashold = 3
  while not flag_end:
    yield
    if FlagRecordingStarted and RecordStartTime and datetime.now() > RecordStartTime+MAX_RECORDING_TIME:
      _G.log_warning("Max recording time excessed, something probably went wrong, exiting")
      stop_recording('__'+video_name)
      _G.FlagRunning = False
      return

    if stage.is_stage('NextScene'):
      flag_pass = True
    if stage.is_stage('StoryTransition'):
      depth += 1
      _G.log_info("Scene depth:", depth)
      if depth >= dep_threashold:
        flag_pass = True
    else:
      depth = 0
    if not flag_pass:
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
      for _ in range(10):
        wait(0.3)
        yield
      dep_threashold = 10
    elif step == STEP_A:
      try:
        utils.pause_process()
        stop_recording(f"{video_name}_A")
      finally:
        utils.resume_process()
      yield from wait_until_transition()
      start_recording()
      for _ in range(5):
        wait(0.3)
        yield
    elif step >= STEP_B:
      try:
        utils.pause_process()
        stop_recording(f"{video_name}_{chord}")
      finally:
        utils.resume_process()
      yield from wait_until_transition(depth, dep_threashold)
      for _ in range(1):
        wait(0.1)
        yield
      while True:
        yield
        if stage.is_stage('NextScene') or stage.is_stage('Gallery'):
          _G.log_info("Scene ended")
          flag_end = True
          break
        elif stage.is_stage('SceneChoices_3'):
          spos = stage.Enum['SceneChoices_3']['pos']
          # third option
          mx   = spos[2][0] + spos[5][0]
          my   = spos[2][1] + spos[5][1]
          yield from safe_click(mx, my)
        else:
          _G.log_info("Start step recording")
          start_recording()
          chord = chr(ord(chord)+1)
          for _ in range(10):
            wait(0.5)
            yield
          if stage.is_stage('StoryAuto') or stage.is_stage('StoryMain'):
            _G.log_info('Scene continue')
            break
          else:
            _G.log_info('Scene ended, discard empty recording')
            stop_recording(rm=True)
    flag_pass = False
    depth = 0
    step += 1
  dep_threashold = 3

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
  cnt_chr = 0
  _G.log_info("Starting index:", idx)
  if not _G.ARGV.all:
    while not stage.is_stage('SceneSelect'):
      yield
    yield from start_scene(datetime.now().strftime("%Y-%m-%d-%H-%M-%S_"))
    return
  while True:
    yield
    if stage.is_stage('Gallery'):
      if not _G.ARGV.all:
        break
      cnt_chr += 1
      if _G.ARGV.number > 0 and cnt_chr > _G.ARGV.number:
        break
      _G.log_info(f"Recording character {cnt_chr}/{_G.ARGV.number}")
      if idx >= 5:
        _G.log_info("Next row")
        idx = 0
        mx, my, mx2, my2 = position.NextCharacterRowScroll
        while True:
          yield
          color = graphics.get_pixel(mx, my, True)
          if graphics.is_color_ok(color, (228, 206, 173), bias=5):
            break
          else:
            mx  += 1
            mx2 += 1
        yield
        mx  -= 15
        mx2 -= 15
        Input.click(mx, my)
        wait(0.1)
        Input.scroll_to(mx, my, mx2, my2, slow=True)
        yield
      mx, my = position.FirstCharacterAvartar
      mx = mx + position.NextCharacterDeltaX * idx
      _G.log_info(mx, my)
      yield from safe_click(mx, my)
      chname = datetime.now().strftime("%Y-%m-%d-%H-%M-%S_")
      if not _G.ARGV.skip_name:
        chname = yield from get_character_name()
      chname = re.sub(r'[\\/:*?"<>|]', '-', chname)
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


def start_test_fiber():
  mx, my, mx2, my2 = position.NextCharacterRowScroll
  while True:
    yield
    color = graphics.get_pixel(mx, my, True)
    if graphics.is_color_ok(color, (187, 160, 121), bias=2):
      break
    else:
      mx  += 1
      mx2 += 1
  yield
  mx  -= 15
  mx2 -= 15
  Input.click(mx, my)
  wait(0.1)
  Input.scroll_to(mx, my, mx2, my2, slow=True)
  yield