import os
from mpm.model import *
import shutil

class Repo:
    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.path = config['path']

    def importPlugin(self, plugin):
        dest = "{}/{}-{}.jar".format(self.path, plugin.name, plugin.version)
        shutil.copyfile(plugin.path, dest)

    def plugins(self):
        plugins = os.listdir(self.path)
        for pluginFile in plugins:
            fullPath = os.path.join(self.path, pluginFile)
            if os.path.isfile(fullPath):
                try:
                    yield Plugin(fullPath)
                except ValueError:
                    continue

    def versionsForPlugin(self, name):
        for plugin in self.plugins():
            if plugin.name == name:
                yield plugin.version

    def badFiles(self):
        plugins = os.listdir(self.path)
        for pluginFile in plugins:
            fullPath = os.path.join(self.path, pluginFile)
            if os.path.isfile(fullPath):
                try:
                    Plugin(fullPath)
                except ValueError:
                    yield fullPath
