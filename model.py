from semantic_version import Spec, Version
from functools import total_ordering
import os
import re

#version_pattern = re.compile('^(?P<name>.*)-(?P<version>[^-]+)(?P<extra>-[^-]+)?\.jar$')
version_pattern = re.compile('^(?P<name>.*)-(?P<version>[^-]+(?:-[^-]+)?)\.jar$')
version_pattern = re.compile('^(?P<name>.+)-(?P<version>(?:\.?\d+)+).+jar$')

@total_ordering
class Plugin:
    def __init__(self, path):
        self.path = path
        pluginName = os.path.basename(path)
        pluginMatches = version_pattern.match(pluginName)

        if pluginMatches is None:
            raise ValueError("Cannot derive plugin name from '{}'".format(path))

        self.name = pluginMatches['name']

        try:
            self.version = Version.coerce(pluginMatches['version'])
        except ValueError:
            raise ValueError("Cannot derive semver from '{}'".format(path))

    def __eq__(self, other):
        return self.name == other.name and self.version == other.version

    def __ne__(self, other):
        return self.name != other.name or self.version != other.version

    def __lt__(self, other):
        if self.name == other.name:
            return self.version < other.version
        return self.name < other.name

@total_ordering
class PluginSpec:
    def __init__(self, name, versionSpec):
        self.name = name
        try:
            self.versionSpec = Spec(str(versionSpec))
        except ValueError:
            raise ValueError("Invalid version spec for plugin {}: {}".format(name, versionSpec))

    def __str__(self):
        return "{} {}".format(self.name, self.versionSpec)

    def __eq__(self, other):
        return self.name == other.name and self.versionSpec == other.versionSpec

    def __ne__(self, other):
        return self.name != other.name or self.versionSpec != other.versionSpec

    def __lt__(self, other):
        return self.name < other.name

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

class Available(PluginState):
    def __init__(self, repoPlugin):
        super().__init__(repoPlugin)

class Installed(PluginState):
    def __init__(self, plugin, currentVersion):
        super().__init__(plugin)
        self.currentVersion = currentVersion
