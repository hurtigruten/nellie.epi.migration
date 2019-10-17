import helpers as hs
import config as cf

ctfl_env = hs.createContentfulEnvironment(cf.CTFL_SPACE_ID, cf.CTFL_ENV_ID, cf.CTFL_MGMT_API_KEY)


start_keys = ["voyageMap", "voyagePicture", "itdpic"]

while True:
    for start_key in start_keys:
        assets = ctfl_env.assets().all(query={"sys.id[match]": start_key})
        for asset in assets:
            asset.delete()
            print("Asset %s deleted" % asset.sys['id'])