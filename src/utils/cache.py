from collections import OrderedDict

class InteractionLRUCache:
    def __init__(self, capacity=10):
        self.cache = OrderedDict()
        self.capacity = capacity

    def put(self, key, value):
        # If exists → move to end
        if key in self.cache:
            self.cache.move_to_end(key)

        self.cache[key] = value

        # Remove oldest
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def get_all(self):
        return list(self.cache.values())

    def clear(self):
        self.cache.clear()