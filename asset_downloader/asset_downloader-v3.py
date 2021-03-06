import argparse
import json
import logging
import os
import urllib.request, urllib.error
import zlib
import threading

g_asset_number = ''
g_access_token = ''
g_tileset = None

threadLock = threading.Lock()
download_started_tiles = []
retry_started_tiles = []

failed_tiles = []

failed_tiles_in_retry = []

parser = argparse.ArgumentParser()
parser.add_argument("worker_count")
parser.add_argument("asset_number")
parser.add_argument("token")
args = vars(parser.parse_args())

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def get_access_token_url(asset_number, token):
    return "https://api.cesium.com/v1/assets/{}/endpoint?access_token={}".format(asset_number, token)


def get_tileset_url(asset_number, access_token):
    return "https://assets.cesium.com/{}/tileset.json?access_token={}".format(asset_number, access_token)


def get_content_url(asset_number, access_token, uri):
    return "https://assets.cesium.com/{}/{}?access_token={}".format(asset_number, uri, access_token)


def get_access_token(asset_number, token):
    try:
        access_token_response = urllib.request.urlopen(get_access_token_url(asset_number, token))
        return json.loads(access_token_response.read().decode('utf8').replace("'", '"'))["accessToken"]
    except urllib.error.HTTPError as error:
        if error.code == 401:
            logger.error("Invalid asset number, token pair")
        elif error.code == 404:
            logger.error("can not find asset!" + asset_number)
        else:
            raise


def get_root_tileset_json(asset_number, access_token):
    json_url = get_tileset_url(asset_number, access_token)
    return get_json(json_url)


def get_json(json_url):
    try:
        tileset_response = urllib.request.urlopen(json_url)
        tileset = zlib.decompress(tileset_response.read(), 16 + zlib.MAX_WBITS).decode('utf8').replace("'", '"')

    except urllib.error.HTTPError as e:
        logger.info("Http error")
        return None
    except Exception as e:
        logger.info(type(e))
        return None

    return json.loads(tileset)


def save_tileset(asset_number, tileset):
    os.makedirs(asset_number, exist_ok=True)
    with open(os.path.join(asset_number, 'tileset.json'), 'w') as outfile:
        json.dump(tileset, outfile)


def extract_value(input, key):
    if hasattr(input, 'items'):
        for item_key, item_value in input.items():
            if item_key == key:
                yield item_value
            if isinstance(item_value, dict):
                for result in extract_value(item_value, key):
                    yield result
            elif isinstance(item_value, list):
                for list_item in item_value:
                    for result in extract_value(list_item, key):
                        yield result

class DownloadWorker(threading.Thread):
    def __init__(self, _id):
        threading.Thread.__init__(self)
        self.id = _id

    def run(self):
        logger.info("Download Worker {} started".format(self.id))

        self.download_tileset_contents(g_asset_number, g_access_token, g_tileset, None)

    def download_tileset_contents(self, asset_number, access_token, tileset_json, parent_json_uri):
        for uri in extract_value(tileset_json, "uri"):
            # download_started_tiles

            threadLock.acquire()

            if uri in download_started_tiles:
                threadLock.release()
                continue
            else:
                download_started_tiles.append(uri)

            threadLock.release()

            logger.info("Downloading {} in download worker {}".format(uri, self.id))

            tile_content_url = get_content_url(asset_number, access_token, uri)
            tile_path = os.path.join(os.getcwd(), asset_number, uri)

            os.makedirs(os.path.dirname(tile_path), exist_ok = True)

            # found nest json file
            if uri.rfind(".json") != -1 :
                parent = "root"

                if parent_json_uri is not None:
                    parent = parent_json_uri

                logger.info("Start downloading nested tileset {} of {}".format(uri, parent))
                nested_json = get_json(tile_content_url)

                if nested_json is None:
                    logger.info("Failed to download json of nested tileset {} of {}".format(uri, parent))
                else:
                    # recursive
                    self.download_tileset_contents(asset_number, access_token, nested_json, uri)
                    logger.info("Finished downloading nested tileset {} of {}".format(uri, parent))

            if os.path.exists(tile_path) and os.path.getsize(tile_path) > 0:
                logger.info("Skip downloading {} because already exist".format(uri))
                continue

            try:
                content_file_request = urllib.request.urlopen(tile_content_url, timeout = 3)

                if content_file_request.code != 200:
                    self.add_failed_tile(uri, tile_content_url)

                    continue

                file_zip_stream = zlib.decompress(content_file_request.read(), 16+zlib.MAX_WBITS)

                local_file = open(tile_path, 'wb')
                local_file.write(file_zip_stream)
                local_file.close()
            except TimeoutError:
                self.add_failed_tile(uri, tile_content_url)
            except ConnectionResetError:
                self.add_failed_tile(uri, tile_content_url)
            except Exception as e:
                logger.info(type(e))
                self.add_failed_tile(uri, tile_content_url)

    def add_failed_tile(self, uri, tile_content_url):
        logger.info("Failed to download {} in download worker {}".format(tile_content_url, self.id))

        threadLock.acquire()
        failed_tiles.append(uri)
        threadLock.release()

def retry_failed_to_download_tiles(asset_number, access_token):
    global failed_tiles

    if len(failed_tiles) == 0:
        return

    new_failed_tiles = []

    for tile in failed_tiles:
        logger.info("Retrying downloading {}".format(tile))

        file_url = get_content_url(asset_number, access_token, tile)
        file_path = os.path.join(os.getcwd(), asset_number, tile)

        try:
            content_file_request = urllib.request.urlopen(file_url, timeout = 3)

            if content_file_request.code != 200:
                logger.info("Failed to download {}".format(file_url))
                new_failed_tiles.append(tile)
                continue

            file_zip_stream = zlib.decompress(content_file_request.read(), 16+zlib.MAX_WBITS)

            local_file = open(file_path, 'wb')
            local_file.write(file_zip_stream)
            local_file.close()
        except TimeoutError:
            logger.info("Failed to download {}".format(file_url))
            new_failed_tiles.append(tile)
        except ConnectionResetError:
            logger.info("Failed to download {}".format(file_url))
            new_failed_tiles.append(tile)
        except:
            logger.info("Failed to download {}".format(file_url))
            new_failed_tiles.append(tile)

    if len(new_failed_tiles) > 0:
        failed_tiles = new_failed_tiles
        retry_failed_to_download_tiles(asset_number, access_token)


def main():
    global g_asset_number, g_access_token, g_tileset

    g_asset_number = args["asset_number"]
    token = args["token"]
    thread_count = args["worker_count"]

    thread_count = int(thread_count)

    logger.info("Processing asset {}".format(g_asset_number))
    g_access_token = get_access_token(g_asset_number, token)
    if g_access_token is None:
        return

    logger.info("Downloading tileset")
    g_tileset = get_root_tileset_json(g_asset_number, g_access_token)

    logger.info("Saving tileset")
    save_tileset(g_asset_number, g_tileset)

    logger.info("Initializing download workers")

    threads = []
    thread_id = 1

    for x in range(thread_count):
        worker = DownloadWorker(thread_id)

        worker.start()
        threads.append(worker)
        thread_id += 1

    # Wait for all threads to complete
    for t in threads:
        t.join()

    retry_failed_to_download_tiles(g_asset_number, g_access_token)

    logger.info("All done")

if __name__ == "__main__":
    main()
