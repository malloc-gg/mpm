#!/bin/env python
import yaml
from semantic_version import Spec, Version
import os
import sys
from functools import total_ordering

try:
        from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
        from yaml import Loader, Dumper

conf = yaml.load(open('plugins.yml', 'r'), Loader=Loader)

class PluginSpec:
    def __init__(self, name, versionSpec):
        self.name = name
        try:
            self.versionSpec = Spec(versionSpec)
        except ValueError:
            raise ValueError("Invalid version spec for plugin {}: {}".format(name, versionSpec))

@total_ordering
class PluginState:
    def __init__(self, plugin):
        self.plugin = plugin

    def __eq__(self, other):
        return self.plugin == other.plugin

    def __ne__(self, other):
        return self.plugin != other.plugin

    def __lt__(self, other):
        return self.plugin.name < other.plugin.name

class UnmanagedFile(PluginState):
    def __init__(self, filename):
        self.filename = filename

    def __lt__(self, other):
        return self.filename < other.filename

class OutdatedSymlink(PluginState):
    def __init__(self, plugin, currentVersion, wantedVersion):
        super().__init__(plugin)
        self.currentVersion = currentVersion
        self.wantedVersion = wantedVersion

class SymlinkConflict(PluginState):
    pass

class MissingVersions(PluginState):
    pass

class Installed(PluginState):
    def __init__(self, plugin, currentVersion):
        super().__init__(plugin)
        self.currentVersion = currentVersion

class Repo:
    def __init__(self, path, pluginSet):
        self.path = path
        self.pluginSet = pluginSet

    def updateSymlinkForPlugin(self, plugin, version):
        pluginFilename = os.path.join(self.path, 'versions/{}-{}.jar'.format(plugin.name, version))
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
        plugins = os.listdir(os.path.join(self.path, 'versions'))
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

for (serverName,server) in conf['servers'].items():
    changeset = []
    if len(sys.argv) > 1 and serverName not in sys.argv[1:]:
        continue
    if 'pluginPath' not in server:
        continue
    if not os.path.exists(server['pluginPath']):
        print("Missing plugin path for {}: {}".format(serverName, server['pluginPath']))
    else:
        print("=== Updating server {}".format(serverName))
        pluginSpecs = {}
        for inherited in server.get('inherit', ()):
            for inheritedPlugin in conf['servers'][inherited]['plugins']:
                pluginSpecs[inheritedPlugin['name']] = PluginSpec(inheritedPlugin['name'], str(inheritedPlugin.get('version', '*')))

        for pluginConf in server.get('plugins', ()):
            pluginSpecs[pluginConf['name']] = PluginSpec(pluginConf['name'], str(pluginConf.get('version', '*')))

        repo = Repo(server['pluginPath'], pluginSpecs.values())
        outdatedLinks = []
        missing = []
        installed = []
        unmanaged = []
        conflicts = []
        for state in repo.pluginStates():
            if isinstance(state, OutdatedSymlink):
                outdatedLinks.append(state)
            elif isinstance(state, Installed):
                installed.append(state)
            elif isinstance(state, MissingVersions):
                missing.append(state)
            elif isinstance(state, UnmanagedFile):
                unmanaged.append(state)
            elif isinstance(state, SymlinkConflict):
                conflicts.append(state)

        print("Installed plugins:")
        for state in sorted(installed):
            print("\t{} {}: {}".format(state.plugin.name, state.plugin.versionSpec, state.currentVersion))
        print("Oudated symlinks:")
        for state in sorted(outdatedLinks):
            print("\t{} {}: Current: {} Wanted: {}".format(state.plugin.name, state.plugin.versionSpec, state.currentVersion, state.wantedVersion))
        print("Missing plugins:")
        for state in sorted(missing):
            print("\t{}: {}".format(state.plugin.name, state.plugin.versionSpec))
        print("Unmanaged files:")
        for state in sorted(unmanaged):
            print("\t{}".format(state.filename))
        print("Symlink Conflicts:")
        for state in sorted(conflicts):
            print("\t{}.jar".format(state.plugin.name))

        if len(outdatedLinks) > 0:
            print("Apply changes? [y/N]")
            answer = input().lower()
            if answer == "y":
                for state in outdatedLinks:
                    repo.updateSymlinkForPlugin(state.plugin, state.wantedVersion)
            else:
                print("Not applying changes.")
