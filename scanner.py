from json import    loads
from util import    get_active_spread_groups


SCANS = loads(open("./scans.json", "r").read())


def perform_scan(title, definition):

    spread_groups = get_active_spread_groups(**definition)

    for spread_group in spread_groups:

        for spread_id in spread_group.active_ids:
        
            rows = spread_group.get_spread_rows(spread_id)

            pass

    

if __name__ == "__main__":

    for title, definition in SCANS.items():

        perform_scan(title, definition)