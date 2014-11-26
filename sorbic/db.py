'''
Interface to interact on a database level
'''
# Import python libs
import os
import io
# Import sorbic libs
import sorbic.ind.hdht
import sorbic.stor
# Import third party libs
import msgpack

DB_OPTS = (
        'key_delim',
        'hash_limit',
        'key_hash',
        'fmt',
        'fmt_map',
        'header_len',
        'serial')


class DB(object):
    '''
    Databaseing
    '''
    def __init__(
            self,
            root,
            key_delim='/',
            hash_limit=0xfffff,
            key_hash='blake',
            fmt='>KsQ',
            fmt_map=None,
            header_len=1024,
            serial='msgpack'):
        self.root = root
        self.key_delim = key_delim
        self.hash_limit = hash_limit
        self.key_hash = key_hash
        self.fmt = fmt
        self.fmt_map = fmt_map
        self.header_len = header_len
        self.serial = serial
        self._get_db_meta()
        self.storage = sorbic.stor.Stor(self.root, serial)
        self.index = sorbic.ind.hdht.HDHT(
                self.root,
                self.key_delim,
                self.hash_limit,
                self.key_hash,
                self.fmt,
                self.fmt_map,
                self.header_len)

    def _get_db_meta(self):
        '''
        Read in the database metadata to preserve the original behavior
        as to when the database are created
        '''
        db_meta = os.path.join(self.root, 'sorbic_db_meta.mp')
        meta = {}
        if os.path.isfile(db_meta):
            with io.open(db_meta, 'rb') as fp_:
                meta = msgpack.loads(fp_.read())
        for entry in DB_OPTS:
            meta[entry] = meta.get(entry, getattr(self, entry))
            setattr(self, entry, meta[entry])
        if not os.path.isdir(self.root):
            os.makedirs(self.root)
        with io.open(db_meta, 'w+b') as fp_:
            fp_.write(msgpack.dumps(meta))

    def insert(self, key, data, id_=None, type_='doc', serial=None, **kwargs):
        '''
        Insert a key into the database
        '''
        c_key = self.index.raw_crypt_key(key)
        table_entry = self.index.get_table_entry(key, c_key)
        start, size = self.storage.write(
                table_entry,
                data,
                serial)
        return self.index.commit(
                table_entry,
                key,
                c_key,
                id_,
                start,
                size,
                type_,
                **kwargs)

    def get(self, key, id_=None):
        '''
        Retrive an entry
        '''
        entries = self.index.get_data_entry(key, id_)
        return self.storage.read(
                entries['table'],
                entries['data']['st'],
                entries['data']['sz'],
                self.serial)
