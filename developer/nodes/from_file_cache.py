import json
import os
import hashlib

def get_file_nodes_cache(file_path, file_hash=None, cache_directory='pilot.cache'):
    # TODO: use path.join
    current_cache_directory = os.path.dirname(
        file_path) + "/" + cache_directory
    current_cache_file = current_cache_directory + \
        "/"+os.path.basename(file_path)+".json"

    if not os.path.exists(current_cache_file):
        return None

    try:
        with open(current_cache_file, 'r') as f:
            cache = json.load(f)

        if not file_hash:
            with open(file_path, 'r') as f:
                file_content = f.read()
                file_hash = hashlib.sha256(file_content.encode()).hexdigest()
        if cache.get('file_hash') != file_hash:
            return None

        return cache.get('nodes')
    except Exception as e:
        print("CACHE ERROR", e)
        return None

def save_file_nodes_cache(file_path, nodes, file_hash=None, cache_directory='pilot.cache'):
    # TODO: use path.join
    current_cache_directory = os.path.dirname(
        file_path) + "/" + cache_directory
    current_cache_file = current_cache_directory + \
        "/"+os.path.basename(file_path) + ".json"

    if not os.path.exists(current_cache_directory):
        os.makedirs(current_cache_directory, exist_ok=True)

    if not file_hash:
        with open(file_path, 'r') as f:
            file_content = f.read()
            file_hash = hashlib.sha256(file_content.encode()).hexdigest()

    with open(current_cache_file, 'w') as f:
        json.dump(dict(nodes=nodes, file_hash=file_hash), f, indent=4)