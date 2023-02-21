from json import    loads
from util import    by_season, by_sequence, get_db, get_legs, \
                    get_spread_ids, get_term_days, spread_wrapper


DB          = get_db()
SCANS       = loads(open("./scans.json", "r").read())
BEGIN       = "1900-01-01"
END         = "2050-01-01"
TERM_DAYS   = {}


def get_seasons(ids):

    return {
        tuple(
            t[0] 
            for t in spread_id
        )
        for spread_id in ids
    }


def get_sequences(today, total_width):

    return {
                i for i in range(len(today) - total_width)
            }


def perform_scan(title, scan):

    symbol      = scan["symbol"]
    max_months  = scan["max_months"]

    if symbol not in TERM_DAYS:

        TERM_DAYS[symbol] = get_term_days(DB, symbol, BEGIN, END)

    term_days = TERM_DAYS[symbol]

    mode            = scan["mode"]
    aggregate_by    = scan["aggregate_by"]
    width           = scan["width"]
    today           = term_days[-1][:max_months]

    legs        = get_legs(mode, width)
    total_width = legs[-1][0]
    todays_ids  = get_spread_ids(today, legs, total_width)

    spread_group_data = None

    if aggregate_by == "sea":

        spread_group_data = by_season(term_days, legs, total_width, get_seasons(todays_ids))
    
    else:

        spread_group_data = by_sequence(term_days, legs, total_width, get_sequences(todays_ids))

    spreads = {}

    for group_id, group_data in spread_group_data.items():

        for spread_id, spread_data in group_data.items():

            if spread_id in todays_ids:

                spreads[spread_id] = spread_wrapper(group_id, spread_id, spread_data)

    pass

    

if __name__ == "__main__":

    for title, scan in SCANS.items():

        perform_scan(title, scan)