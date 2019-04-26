#!/usr/bin/python
# -*- coding: UTF-8 -*-
import threading
import logging
import time
import os
import re


class VNETRouterFix(threading.Thread):
	def __init__(self, manager):
		threading.Thread.__init__(self)
		self._manager = manager
		self._start_fix = False
		self._tap_ip = None
		self._tag_netmask = None
		self._dest_ip = None
		self._thread_stop = False

	def start_fix(self, tap_ip, tag_netmask, dest_ip):
		self._start_fix = True
		self._tap_ip = tap_ip
		self._tag_netmask = tag_netmask
		self._dest_ip = dest_ip

	def is_fixing(self):
		return self._start_fix

	def run(self):
		while not self._thread_stop:
			if not self._start_fix:
				time.sleep(1)
				continue

			cmd4_ret = None
			for i in range(2):
				cmd1 = 'sc query tinc.tofreeioerouter|find /I "STATE"'
				cmd1_ret = os.popen(cmd1).read().strip()
				cmd1_ret = re.split('\s+', cmd1_ret)
				if cmd1_ret[3] == "RUNNING":
					cmd0 = 'route DELETE ' + self._tap_ip
					cmd0_ret = os.popen(cmd0).read().strip()
					cmd2 = 'route ADD ' + self._tap_ip + ' MASK ' + self._tag_netmask + ' 10.222.0.1'
					cmd2_ret = os.popen(cmd2).read().strip()
					cmd3 = 'route CHANGE ' + self._tap_ip + ' MASK ' + self._tag_netmask + ' 10.222.0.1'
					cmd3_ret = os.popen(cmd3).read().strip()
					cmd4 = 'FOR /F "tokens=1 delims=:" %A IN ' + "('ping " + self._dest_ip + " -n 1 ^| " + 'findstr /N "TTL"' + "') DO @echo %A"
					cmd4_ret = os.popen(cmd4).read().strip()
					if cmd4_ret:
						if int(cmd4_ret) > 0:
							break
				time.sleep(i + 1)
			if cmd4_ret and int(cmd4_ret) > 0:
				self._start_fix = False

	def stop(self):
		self._thread_stop = True
		self.join()
