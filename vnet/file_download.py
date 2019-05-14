#!/usr/bin/python
# -*- coding: UTF-8 -*-
import threading
import logging
import time
import os
import re
from requests import get  # to make GET request


class VNETdownload(threading.Thread):
	def __init__(self, manager):
		threading.Thread.__init__(self)
		self._manager = manager
		self._start_download = False
		self._url = None
		self._file_name = None
		self._thread_stop = False

	def start_download(self, url, file_name):
		self._start_download = True
		self._url = url
		self._file_name = file_name

	def is_download(self):
		return self._start_download

	def run(self):
		while not self._thread_stop:
			if not self._start_download:
				time.sleep(1)
				continue
			if not os.path.exists("_update"):
				os.mkdir("_update")
			with open(self._file_name, "wb") as file:
				# get request
				response = get(self._url)
				# write to file
				file.write(response.content)
			self._start_download = False

	def stop(self):
		self._thread_stop = True
		self.join()
