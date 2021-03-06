import os
import json

VERSION = "1"

VERSION_KEY = "version"
SERVERS_KEY = "servers"

NAME_KEY = "name"
USER_KEY = "user"
ADDRESS_KEY = "address"

home = os.environ['HOME']
default_config_dir = "%s/.ssh-menu" % home
default_servers_config = '%s/servers' % default_config_dir


class InvalidConfigException(Exception):
    pass


def get_default_servers_config_path():
    """Return the default path of the servers config file"""
    return default_servers_config


def init_config():
    """Initialize the config. If a config file already exists, it does nothing."""

    if not os.path.exists(default_config_dir):
        os.mkdir(default_config_dir)

    if os.path.exists(default_servers_config):
        # the servers config already exists
        return

    config_template = { VERSION_KEY: VERSION, SERVERS_KEY: {} }

    with open(default_servers_config, mode='w') as f:
        f.writelines(json.dumps(config_template, indent=2))


def get_servers_config(path):
    """Parse the file into a ServersConfig object. Throws InvalidConfigException if the config is not valid"""

    with open(path, 'r') as f:
        config = json.loads(f.read())

        if not VERSION_KEY in config or config[VERSION_KEY] != VERSION:
            raise InvalidConfigException("unsupported config version")

        if not SERVERS_KEY in config or not isinstance(config[SERVERS_KEY], dict):
            raise InvalidConfigException("malformed or missing %s from config" % SERVERS_KEY)

        servers = {}

        for name, server in config[SERVERS_KEY].items():
            # validate the server
            required_keys = [ USER_KEY, ADDRESS_KEY ]
            for k in required_keys:
                if k not in server:
                    raise InvalidConfigException("server missing required key: %s" % k)

            servers[name] = Server(name=name,
                                   user=server[USER_KEY],
                                   address=server[ADDRESS_KEY])

        return ServersConfig(path, servers)


class Server():
    """A class for an individual server that a user can connect to"""
    def __init__(self, name, user, address):
        # TODO: last time it connected for sorting
        self.name = name
        self.user = user
        self.address= address

    def connection_string(self):
        """The connection string suitable for `ssh {connection_string()}`"""
        return "%s@%s" % (self.user, self.address)

    def to_map(self):
        """Turn it into a map suitable for json serialization"""
        return {
            USER_KEY: self.user,
            ADDRESS_KEY: self.address,
        }


class ServersConfig():
    """A class for accessing the server config and persistence"""
    def __init__(self, path, servers):
        self.path = path
        self.servers = servers

    def to_map(self):
        """Turn it into a map suitable for json serialization"""
        config_map = {
            VERSION_KEY: VERSION,
            SERVERS_KEY: {},
        }

        for name, server in self.servers.items():
            config_map[SERVERS_KEY][name] = server.to_map()

        return config_map

    def get_server(self, name):
        """Get the server by this name. If the server is not present, returns None"""
        for server in self.servers.values():
            if server.name == name:
                return server

        return None

    def get_servers(self):
        """Get a list of the servers"""
        return self.servers.values()

    def add_server(self, name, user, address):
        """Adds a server to this config, or updates an existing server by that name"""
        server = self.get_server(name)
        if server:
            server.user = user
            server.address = address
        else:
            self.servers[name] = Server(name, user, address)

    def remove_server(self, name):
        server = self.get_server(name)
        if server:
            del self.servers[name]

    def save(self):
        """Save it to the disk at the given path"""
        config_json = json.dumps(self.to_map(), indent=2) + "\n"
        with open(self.path, 'w') as f:
            f.write(config_json)
