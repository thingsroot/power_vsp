from configparser import ConfigParser
import os


class _dict(dict):
	"""dict like object that exposes keys as attributes"""

	def __getattr__(self, key):
		ret = self.get(key)
		if not ret and key.startswith("__"):
			raise AttributeError()
		return ret

	def __setattr__(self, key, value):
		self[key] = value

	def __getstate__(self):
		return self

	def __setstate__(self, d):
		self.update(d)

	def update(self, d):
		"""update and return self -- the missing dict feature in python"""
		super(_dict, self).update(d)
		return self

	def copy(self):
		return _dict(dict(self).copy())


class APPCtrl:

	def get_heartbeat(self):
		config = ConfigParser()
		if os.access(os.getcwd() + '\\config.ini', os.F_OK):
			config.read('config.ini')
			if config.has_option('system', 'enable_heartbeat'):
				if config.getint('system', 'enable_heartbeat') == 0:
					return False
				else:
					return True
			else:
				return True

	def get_packetheader(self):
		config = ConfigParser()
		if os.access(os.getcwd() + '\\config.ini', os.F_OK):
			config.read('config.ini')
			if config.has_option('system', 'enable_packetheader'):
				if config.getint('system', 'enable_packetheader') == 0:
					return False
				else:
					return True
			else:
				return True
