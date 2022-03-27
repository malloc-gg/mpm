# A tool to manage plugins on play.malloc.gg

plugin-sync is a tool used to maintain the various servers and their plugins on
play.malloc.gg.

Malloc runs a heterogenous environment of server versions, depending on what
gamemodes folks are playing and how recently the latest major Minecraft update
was published. Many of these servers need to share common infrastructure, such
as universal network-wide chat, discord interfaces, player statistics, voice
chat, and more. Managing them got to be such a pain in the ass that I wrote this
tool to help out the workload.

## Use cases

plugin-sync is highly specialized for the purposes of malloc.gg, but it should
be able to work in other systems where:

- You have multiple servers in a network
- They each need to share common plugin versions
- Some sub-groups of servers share plugins amongst themselves, but not with
  every other server on the network
- You're trying to upgrade a network to a new minecraft release but can't bring
  all the servers and their plugins along at the same time


## Usage

To use, you'll need to create a `plugins.yml` file, using the same structure as
the one in this repository. Then, create a versions/ directory Inside each
server's plugins/ directory. For example, if your server.jar lives at
`/srv/minecraft/server/`, you'll create
`/srv/minecraft/server/plugins/versions/`. Plugin files are not automatically
synchronized between each server's versions directory, though this would be the
next direction for this tool to go. Versions are managed using simple symlinks,
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

- Sometimes you'll end up with a mismatch between where the symlink goes and the
  version'd filename, usually when you've got a version that goes beyond the
  traditional $MAJOR.$MINOR.$PATCH tuple. Just rename your files, I guess.

Maybe you'll find this useful too. Batteries not included.
