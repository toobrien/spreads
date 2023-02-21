from json import    loads
from util import    get_active_spread_groups


SCANS = loads(open("./scans.json", "r").read())


def perform_scan(title, definition):

    spread_groups = get_active_spread_groups(**definition)

    pass

    

if __name__ == "__main__":

    for title, definition in SCANS.items():

        perform_scan(title, definition)