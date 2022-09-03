import os
from model import *
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

class Server:
    def __init__(self, path, pluginSet):
        self.path = path
        self.pluginSet = pluginSet

    def updateSymlinkForPlugin(self, plugin, version):
        pluginFilename = os.path.join(self.path, 'plugins/versions/{}-{}.jar'.format(plugin.name, version))
        pluginSymlink = os.path.join(self.path, plugin.name + '.jar')
        linkDst = os.path.relpath(pluginFilename, self.path)

        if os.path.lexists(pluginSymlink):
            os.unlink(pluginSymlink)
        os.symlink(linkDst, pluginSymlink)

    def pluginStates(self):
        managedPluginFilenames = []
        for plugin in self.pluginSet:
            compatibleVersions = []
            pluginLinkName = '{}.jar'.format(plugin.name)
            managedPluginFilenames.append(pluginLinkName)

            if os.path.exists(os.path.join(self.path, pluginLinkName)) and not os.path.islink(os.path.join(self.path, pluginLinkName)):
                yield SymlinkConflict(plugin)
                continue

            for installedVersion in self.versionsForPlugin(plugin.name):
                if installedVersion in plugin.versionSpec:
                    compatibleVersions.append(installedVersion)

            if len(compatibleVersions) == 0:
                yield MissingVersions(plugin)
            else:
                preferredVersion = list(reversed(sorted(compatibleVersions)))[0]
                currentVersion = self.currentVersionForPlugin(plugin.name)

                if currentVersion == preferredVersion:
                    yield Installed(plugin, currentVersion)
                else:
                    yield OutdatedSymlink(plugin, currentVersion, preferredVersion)

        otherPlugins = os.listdir(self.path)
        for pluginFile in otherPlugins:
            if os.path.isfile(os.path.join(self.path, pluginFile)) and pluginFile not in managedPluginFilenames:
                yield UnmanagedFile(pluginFile)

    def currentVersionForPlugin(self, pluginName):
        pluginSymlink = os.path.join(self.path, pluginName + '.jar')
        if not os.path.lexists(pluginSymlink):
            return None
        suffix = '.jar'
        pluginJar = os.path.basename(os.readlink(pluginSymlink))
        jarVersion = pluginJar[len(pluginName)+1:len(pluginJar)-len(suffix)]
        try:
            pluginSemver = Version.coerce(jarVersion)
        except ValueError:
            pluginSemver = jarVersion
        return pluginSemver

    def versionsForPlugin(self, pluginName):
        plugins = os.listdir(os.path.join(self.path, 'plugins', 'versions'))
        for pluginJar in plugins:
            if pluginJar.startswith(pluginName):
                prefix = pluginName + '-'
                suffix = '.jar'
                jarVersion = pluginJar[len(prefix):len(pluginJar)-len(suffix)]
                try:
                    pluginSemver = Version.coerce(jarVersion)
                except ValueError:
                    pluginSemver = jarVersion
                yield pluginSemver

