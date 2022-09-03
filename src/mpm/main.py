#!/bin/env python
import argparse
import pathlib
import sys
import yaml
import os

from mpm.repo import Repo
from mpm.server import Server
from mpm.model import *
from mpm.transactions import Resolver

try:
        from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
        from yaml import Loader, Dumper

DEFAULT_CONFIG = """
repositories: {}
servers: {}
"""

class Config():

    def __init__(self, path):
        if path is None:
            path = os.path.expanduser('~/mpm.yaml')
        self.path = path
        with open(path, 'r') as fd:
            self.yaml = yaml.load(fd, Loader=Loader)
        self.config = yaml.load(DEFAULT_CONFIG, Loader=Loader)
        if isinstance(self.yaml, dict):
            self.config.update(self.yaml)

    def repository(self, name):
        return Repo(name, self.config['repositories'][name])

    def repositories(self):
        return [Repo(name, c) for (name, c) in self.config['repositories'].items()]

    def update_repository(self, name, config):
        self.config['repositories'][name] = config

    def add_repository(self, name, path):
        if name in self.config['repositories']:
            raise ValueError('Repository already exists')

        self.update_repository(name, {
            'path': path
        })

    def servers(self):
        return [Server(name, c) for (name, c) in self.config['servers'].items()]

    def server(self, name):
        return Server(name, self.config['servers'][name])

    def update_server(self, server, config):
        self.config['servers'][server] = config

    def add_server(self, name, path):
        if name in self.config['servers']:
            raise ValueError("Server already exists")

        self.update_server(name, {
            'path': path,
            'plugins': [],
            'inherit': []
        })

    def save(self):
        stream = open(self.path, 'w')
        yaml.dump(self.config, stream, Dumper=Dumper)
        stream.close()

def do_repo_add(args, config):
    if not os.path.exists(args.path):
        os.makedirs(args.path)
    config.add_repository(args.name, args.path)
    config.save()
    print("Added repository {}".format(args.path))

def do_repo_list(args, config):
    for repo in config.repositories():
        print("{} ({})".format(repo.name, repo.path))
        for plugin in sorted(repo.plugins()):
            print('\t', plugin.name, '\t', plugin.version)
        for badFile in sorted(repo.badFiles()):
            print('\tWARNING: Unknown file', badFile)

def do_repo_import(args, config):
    repo = config.repository(args.name)
    plugins = []
    for path in args.path:
        try:
            plugins.append(Plugin(path))
        except:
            print("Bad plugin filename {}".format(path))

    if len(plugins) == 0:
        print("No plugins found.")

    print('Found the following plugins:')
    for plugin in plugins:
        print("\t{} {}".format(plugin.name, plugin.version))
    print("Import plugins into {}? [y/N]".format(repo.name))
    answer = input().lower()
    if answer == "y":
        for plugin in plugins:
            repo.importPlugin(plugin)
        print("Imported!")
    else:
        print("Cancelled.")

def do_server_add(args, config):
    config.add_server(args.name, args.path)
    server = config.server(args.name)
    for plugin in server.installedPlugins():
        try:
            server.add_plugin(PluginSpec(plugin.name, plugin.version))
        except:
            pass
    config.update_server(server.name, server.config)
    config.save()
    print("Added server {} in {}".format(args.name, args.path))

def do_server_list(args, config):
    for server in config.servers():
        print('{} ({})'.format(server.name, server.path))
        foundPlugins = []
        installedPlugins = list(server.installedPlugins())
        for wanted in server.wantedPlugins():
            for installed in installedPlugins:
                if installed.name == wanted.name:
                    foundPlugins.append(wanted.name)
                    print('\t{} {} (wanted: {})'.format(installed.name, installed.version, wanted.versionSpec))
        for installed in installedPlugins:
            if installed.name not in foundPlugins:
                print('\t{} {}'.format(installed.name, installed.version))

def do_server_add_plugin(args, config):
    server = config.server(args.server)
    plugins = []
    for pluginSpec in args.plugin:

        if os.path.exists(pluginSpec):
            plugin = Plugin(pluginSpec)
            pluginSpec = PluginSpec(plugin.name, str(plugin.version))
        else:
            allVersions = []
            for repo in config.repositories():
                allVersions += repo.versionsForPlugin(pluginSpec)
            bestVersions = list(reversed(sorted(allVersions)))
            if len(bestVersions) > 0:
                pluginSpec = PluginSpec(pluginSpec, bestVersions[0])
            else:
                print("Cannot find plugin {} in any repository".format(pluginSpec))
                sys.exit(1)

        plugins.append(pluginSpec)

    print("Added {} to {}".format(pluginSpec, server.name))
    for pluginSpec in plugins:
        print("\t{} {}".format(pluginSpec.name, pluginSpec.versionSpec))
    print("Add these plugins to server {}? [y/N]".format(server.name))
    answer = input().lower()
    if answer == "y":
        for pluginSpec in plugins:
            server.add_plugin(pluginSpec)
        config.update_server(server.name, server.config)
        config.save()
        print("Added!")
    else:
        print("Cancelled.")

def do_server_sync(args, config):
    resolver = Resolver(config.servers(), config.repositories())
    isEmpty = True
    for trans in resolver.transactions():
        isEmpty = False
        print("\t{}".format(trans))
    if isEmpty:
        print("No changes to process.")
        return
    print("Apply changes? [y/N]")
    answer = input().lower()
    if answer == "y":
        print("Testing transaction...") 
        for trans in resolver.transactions():
            trans.test()
        print("Running transaction...")
        for trans in resolver.transactions():
            trans.run()

def main():
    parser = argparse.ArgumentParser(description='Paper Plugin Sync')
    parser.add_argument('--config', dest='config_path', type=Config)
    subparsers = parser.add_subparsers()
    repos = subparsers.add_parser('repo')
    repo_sub = repos.add_subparsers()

    repo_add = repo_sub.add_parser('add')
    repo_add.add_argument('name', help='Name of the repository')
    repo_add.add_argument('path', help='Where to add a repository or create a new one')
    repo_add.set_defaults(func=do_repo_add)

    repo_list = repo_sub.add_parser('list')
    repo_list.set_defaults(func=do_repo_list)

    repo_import = repo_sub.add_parser('import')
    repo_import.add_argument('name', help='Name of the repository')
    repo_import.add_argument('path', nargs="+", help='Path of the plugin to import')
    repo_import.set_defaults(func=do_repo_import)

    servers = subparsers.add_parser('server')
    server_sub = servers.add_subparsers()
    server_add = server_sub.add_parser('add')
    server_add.add_argument('name', help='Name for the server')
    server_add.add_argument('path', help='Path to your server\'s root directory')
    server_add.set_defaults(func=do_server_add)

    server_list = server_sub.add_parser('list')
    server_list.set_defaults(func=do_server_list)

    server_add_plugin = server_sub.add_parser('add-plugin')
    server_add_plugin.add_argument('server', help='Name of server to modify')
    server_add_plugin.add_argument('plugin', nargs='+', help='Plugin file or spec to install')
    server_add_plugin.set_defaults(func=do_server_add_plugin)

    server_sync = server_sub.add_parser('sync')
    server_sync.set_defaults(func=do_server_sync)

    args = parser.parse_args()

    config = Config(args.config_path)

    if 'func' not in args:
        parser.print_usage()
    else:
        args.func(args, config)

if __name__ == "__main__":
    main()
