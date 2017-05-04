import sublime
import sublime_plugin
import time
import json
import os
import urllib
import datetime
from collections import namedtuple
from os.path import relpath

history_filename = 'SyncoPath.sublime-settings'
history = sublime.load_settings(history_filename)
USER = history.get("user_name") or os.environ['USER']
FIREBASE = history.get("firebase_url")

class PsynchopathListener(sublime_plugin.EventListener):

  def on_pre_save_async(self, view):
    if FIREBASE:
      folders = sublime.active_window().folders()
      file_path = relpath(view.file_name(), (folders and folders[0]) or '')
      files_in_firebase = get_data()
      conflicts = [x for x in files_in_firebase if x["file"] == file_path]
      # Remove any old saves
      for item in conflicts:
        remove_data(item)
      # This is the latest save
      post_data(file_path)

  def on_load_async(self, view):
    if FIREBASE:
      folders = sublime.active_window().folders()
      file_path = relpath(view.file_name(), (folders and folders[0]) or '')
      files_in_firebase = get_data()
      # conflicts = [x for x in files_in_firebase if (x["file"] == file_path)] # testing against myself
      conflicts = [x for x in files_in_firebase if (x["file"] == file_path) and (x["user"] != USER)]
      if len(conflicts):
        conflict = conflicts[0]
        sublime.message_dialog("This file was last saved by " + conflict["user"] + " " + datetime.datetime.utcfromtimestamp(conflict["date"]).strftime("%x"))

def get_data():
  url = FIREBASE + '/files.json'
  req = urllib.request.Request(url)
  response = urllib.request.urlopen(req)
  body = response.read().decode('utf-8')
  if body != 'null':
    return parse_json(body)
  else:
    return {}

def post_data(file):
  url = FIREBASE + '/files.json'
  req = urllib.request.Request(url)
  req.add_header('Content-Type', 'application/json; charset=utf-8')
  values = json.dumps(dict(file=file, date=time.time(), user=USER))
  jsondata = json.dumps(values)
  jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
  req.add_header('Content-Length', len(jsondataasbytes))
  response = urllib.request.urlopen(req, jsondataasbytes) 

def remove_data(file):
  url = FIREBASE + '/files/' + file["key"] + '.json'
  req = urllib.request.Request(url)
  req.add_header('Content-Type', 'application/json; charset=utf-8')
  req.add_header('X-HTTP-Method-Override', 'DELETE')
  response = urllib.request.urlopen(req)

def parse_json(data):
  data = json.loads(data)
  arr = []
  for key in data.keys():
    ds = json.loads(data[key])
    arr.append({"key": key, "user": ds["user"], "file": ds["file"], "date": ds["date"]})
  return arr
  