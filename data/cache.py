#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据缓存模块"""

import os
import pickle
from datetime import datetime


class DataCache:
    """数据缓存类"""
    
    def __init__(self, cache_dir="./cache", expire_hours=24):
        self.cache_dir = cache_dir
        self.expire_hours = expire_hours
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_path(self, key):
        safe_key = key.replace("/", "_").replace(":", "_")
        return os.path.join(self.cache_dir, f"{safe_key}.pkl")
    
    def get(self, key):
        cache_path = self._get_cache_path(key)
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            
            cache_time = data.get('_cache_time', 0)
            if datetime.now().timestamp() - cache_time > self.expire_hours * 3600:
                os.remove(cache_path)
                return None
            
            return data.get('value')
        except:
            return None
    
    def set(self, key, value):
        cache_path = self._get_cache_path(key)
        data = {
            'value': value,
            '_cache_time': datetime.now().timestamp()
        }
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
    
    def clear(self):
        for filename in os.listdir(self.cache_dir):
            os.remove(os.path.join(self.cache_dir, filename))
