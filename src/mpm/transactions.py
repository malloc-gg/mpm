from mpm.model import *
import shutil

class Resolver:
    def __init__(self, servers, repos):
        self.servers = servers
        self.repos = repos

    def transactions(self):
        availablePlugins = []

        for repo in self.repos:
            for plugin in repo.plugins():
                availablePlugins += list(repo.plugins())

        for server in self.servers:
            installedPlugins = list(server.installedPlugins())
            foundNames = []
            for wanted in server.wantedPlugins():

                repoVersions = []
                installedVersions = []
                foundNames.append(wanted.name)

                for plugin in availablePlugins:
                    if plugin.name == wanted.name and plugin.version in wanted.versionSpec:
                        repoVersions.append(plugin)


                if len(repoVersions) == 0:
                    # Nothing in the repos, nothing to do
                    continue

                for plugin in installedPlugins:
                    if plugin.name == wanted.name:
                        installedVersions.append(plugin)

                bestVersion = list(reversed(sorted(installedVersions + repoVersions)))[0]
                if bestVersion not in installedVersions:
                    yield InstallPlugin(server, bestVersion)

                for plugin in installedVersions:
                    if plugin != bestVersion:
                        yield RemovePlugin(server, plugin)

            for installed in installedPlugins:
                if installed.name not in foundNames:
                    yield RemovePlugin(server, installed)

class Transaction:
    def test(self):
        raise NotImplemented

    def run(self):
        raise NotImplemented

class InstallPlugin(Transaction):
    def __init__(self, server, plugin):
        self.server = server
        self.plugin = plugin

    def __str__(self):
        return "Install {} to {}".format(self.plugin, self.server)

    def test(self):
        dest = os.path.join(self.server.pluginPath, '{}-{}.jar'.format(self.plugin.name, self.plugin.version))
        if os.path.exists(dest):
            raise Exception("{} already exists!".format(dest))

    def run(self):
        dest = os.path.join(self.server.pluginPath, '{}-{}.jar'.format(self.plugin.name, self.plugin.version))
        shutil.copyfile(self.plugin.path, dest)

class RemovePlugin(Transaction):
    def __init__(self, server, plugin):
        self.server = server
        self.plugin = plugin

    def __str__(self):
        return "Remove {} from {}".format(self.plugin, self.server)

    def test(self):
        os.path.exists(self.plugin.path)

    def run(self):
        os.remove(self.plugin.path)
