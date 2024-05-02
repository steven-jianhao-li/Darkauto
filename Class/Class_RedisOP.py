# 提供RedisOP类，用于与Redis数据库交互

import redis
import json
import time
import random
import os

main_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
defautl_config_path = main_path + '/Config/RedisConfig.json'

class RedisOP:
    def __init__(self, config_path=defautl_config_path):
        self.config_path = config_path
        self.config = self.load_config()
        self.pool = redis.ConnectionPool(host=self.config['host'], port=self.config['port'], db=self.config['db'])
        self.r = redis.Redis(connection_pool=self.pool)

    def load_config(self):
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        return config

    def set(self, key, value):
        self.r.set(key, value)

    def get(self, key):
        return self.r.get(key)

    def delete(self, key):
        self.r.delete(key)

    def set_expire(self, key, value, expire):
        self.r.setex(key, value, expire)

    def get_expire(self, key):
        return self.r.ttl(key)

    def set_list(self, key, value):
        self.r.rpush(key, value)

    def get_list(self, key):
        return self.r.lrange(key, 0, -1)

    def delete_list(self, key):
        self.r.delete(key)

    def set_hash(self, key, field, value):
        self.r.hset(key, field, value)

    def get_hash(self, key, field):
        return self.r.hget(key, field)

    def delete_hash(self, key, field):
        self.r.hdel(key, field)

    def set_expire_hash(self, key, field, value, expire):
        self.r.hset(key, field, value)
        self.r.expire(key, expire)

    def get_expire_hash(self, key):
        return self.r.ttl(key)

    def set_set(self, key, value):
        self.r.sadd(key, value)

    def get_set(self, key):
        return self.r.smembers(key)

    def delete_set(self, key):
        self.r.delete(key)

    def set_expire_set(self, key, value, expire):
        self.r.sadd(key, value)
        self.r.expire(key, expire)

    def get_expire_set(self, key):
        return self.r.ttl(key)

    def set_zset(self, key, value, score):
        self.r.zadd(key, {value: score})

    def get_zset(self, key):
        return self.r.zrange(key, 0, -1, withscores=True)