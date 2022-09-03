#!/bin/env python
import yaml
import os
import sys
from model import *

try:
        from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
        from yaml import Loader, Dumper

conf = yaml.load(open('plugins.yml', 'r'), Loader=Loader)

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
