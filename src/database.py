from pymongo import MongoClient
from typing import List
import json
from src import utility

class Clan:

    def __init__(self, clan_tag, clan_symbol):
        self.clan_tag: str = clan_tag
        self.clan_symbol: str = clan_symbol
        self.clan_announcement_channel: str = None

    def set_clan_announcement_channel(self, channel_id):
        self.clan_announcement_channel = channel_id

    def has_clan_announcement_channel(self):
        return self.clan_announcement_channel is not None

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class User:

    def __init__(self, user_id, account_name):
        self.user_id: str = user_id
        self.account_name: str = account_name

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class Server:

    def __init__(self, server_id):
        self.server_id: str = server_id
        self.users: List[User] = []
        self.clans: List[Clan] = []

    def add_user(self, user):
        self.users += [user]

    def add_clan(self, clan):
        self.clans += [clan]

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class Database:

    cache: dict = dict()

    def __init__(self, atlas_uri, db_name, collection_name='prod'):
        self.cluster = MongoClient(atlas_uri)
        self.db = self.cluster[db_name]
        self.collection = self.db[collection_name]

    def server_data_to_server(self, data):
        server_data = json.loads(data['server'])
        server = Server(server_data['server_id'])
        if 'clans' in server_data:
            for clan in server_data['clans']:
                data = Clan(clan['clan_tag'], clan['clan_symbol'])
                if 'clan_announcement_channel' in clan:
                    data.set_clan_announcement_channel(clan['clan_announcement_channel'])
                server.add_clan(data)
        if 'users' in server_data:
            for user in server_data['users']:
                data = User(user['user_id'], user['account_name'])
                server.add_user(data)
        return server


    def read_servers(self):
        servers = []
        results = self.collection.find()
        for data in results:
            servers += [self.server_data_to_server(dict(data))]
        return servers

    def write_server(self, server: Server):
        try:
            query = {'_id': server.server_id}
            update = {'_id': server.server_id, 'server': server.toJSON()}
            self.collection.update_one(query, {'$set': update}, upsert=True)
        except Exception as exception:
            utility.log(type(exception).__name__)
            utility.log("An error occurred trying to save the server: %s" % server.server_id)
            return False
        if server.server_id in self.cache:
            self.cache[server.server_id] = server
        return True

    def read_server(self, server_id: str):
        if server_id in self.cache:
            return self.cache[server_id]
        data = self.collection.find_one({'_id': server_id})
        if not data:
            utility.log("A server was requested that has not been registered: %s" % server_id)
            return None
        data = dict(data)
        server = self.server_data_to_server(data)
        self.cache[server_id] = server
        return server
