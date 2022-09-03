from mpm.model import *
import shutil

class Server:
    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.path = config['path']
        self.pluginPath = self.path+'/plugins'

    def plugins(self):
        return [PluginSpec(p['name'], p['version']) for p in self.config['plugins']]

    def add_plugin(self, pluginSpec):
        for plugin in self.config['plugins']:
            if plugin['name'] == pluginSpec.name:
                raise KeyError("Cannot add plugin multiple times.")
        self.config['plugins'].append({'name': pluginSpec.name, 'version': str(pluginSpec.versionSpec)})

    def pluginStates(self, repos):
        managedPluginFilenames = []
        for plugin in self.plugins():
            compatibleVersions = []
            pluginLinkName = '{}.jar'.format(plugin.name)
            managedPluginFilenames.append(pluginLinkName)

            if os.path.exists(os.path.join(self.pluginPath, pluginLinkName)) and not os.path.islink(os.path.join(self.pluginPath, pluginLinkName)):
                yield SymlinkConflict(plugin)
                continue

            for installedVersion in self.versionsForPlugin(plugin.name, repos):
                if installedVersion in plugin.versionSpec:
                    compatibleVersions.append(installedVersion)

            if len(compatibleVersions) == 0:
                for repo in repos:
                    for repoPlugin in repo.plugins():
                        if repoPlugin.name == plugin.name and repoPlugin.version in plugin.versionSpec:
                            compatibleVersions.append(repoPlugin)
                if len(compatibleVersions) == 0:
                    yield MissingVersions(plugin)
                else:
                    preferredVersion = list(reversed(sorted(compatibleVersions)))[0]
                    yield Available(preferredVersion)
            else:
                preferredVersion = list(reversed(sorted(compatibleVersions)))[0]
                currentVersion = self.currentVersionForPlugin(plugin.name)

                if currentVersion == preferredVersion:
                    yield Installed(plugin, currentVersion)
                else:
                    yield OutdatedSymlink(plugin, currentVersion, preferredVersion)

        otherPlugins = os.listdir(self.pluginPath)
        for pluginFile in otherPlugins:
            if os.path.isfile(os.path.join(self.pluginPath, pluginFile)) and pluginFile not in managedPluginFilenames:
                yield UnmanagedFile(pluginFile)

    def currentVersionForPlugin(self, pluginName):
        pluginSymlink = os.path.join(self.pluginPath, pluginName + '.jar')
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

    def versionsForPlugin(self, pluginName, repos):
        plugins = os.listdir(os.path.join(self.pluginPath, 'versions'))
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

    def updateSymlinkForPlugin(self, plugin, version):
        pluginFilename = os.path.join(self.pluginPath, 'versions/{}-{}.jar'.format(plugin.name, version))
        pluginSymlink = os.path.join(self.pluginPath, plugin.name + '.jar')
        linkDst = os.path.relpath(pluginFilename, self.pluginPath)

        if os.path.lexists(pluginSymlink):
            os.unlink(pluginSymlink)
        os.symlink(linkDst, pluginSymlink)

    def installVersion(self, plugin):
        dest = os.path.join(self.pluginPath, 'versions/{}-{}.jar'.format(plugin.name, plugin.version))
        shutil.copyfile(plugin.path, dest)
