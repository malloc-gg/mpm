# Minecraft Plugin Manager

mpm is a tool used to maintain the various servers and their plugins on
play.malloc.gg.

Malloc runs a heterogenous environment of server versions, depending on what
gamemodes folks are playing and how recently the latest major Minecraft update
was published. Many of these servers need to share common infrastructure, such
as universal network-wide chat, discord interfaces, player statistics, voice
chat, and more. Managing them got to be such a pain in the ass that I wrote this
tool to help out the workload.

## Use cases

mpm is highly specialized for the purposes of malloc.gg, but it should
be able to work in other systems where:

- You have multiple servers in a network
- They each need to share common plugin versions
- Some sub-groups of servers share plugins amongst themselves, but not with
  every other server on the network
- You're trying to upgrade a network to a new minecraft release but can't bring
  all the servers and their plugins along at the same time

## Installation

    # pip install .

## Usage

- Create a new plugin repository: `mpm repo add`
- List repositories: `mpm repo list`
- Import a package to a repository: `mpm repo import`

- Add a server to mpm: `mpm server add`
- List your servers: `mpm server list`
- Add a plugin to a server: `mpm server add-plugin`
- Commit your changes: `mpm server sync`

Documentation is scarce. Sorry about that. Pull requests and wiki editors appreciated.

Versions are managed using simple symlinks,
and they require that the actual .jar files use Semver naming. Any deviation
from Semver can result in some really goofy behavior, but for the most part, the
majority of plugins available on spigot.org include a compatible string in the
downloaded filename.

Compatible version ranges are specified in plugins.yml for each plugin and
follow Python semantics. If a version field isn't listed, it defaults to `*` aka
`=>0.0.0`. Be careful when specifying incomplete or unusual version numbers, as
sometimes YAML might interpret your 1.0 as a numeric 1. Throw some quotes around
for good measure if you run into this.

## Known Bugs

- Bad documentation
- 'mpm' is not an uncommon name

Maybe you'll find this useful too. Batteries not included.
