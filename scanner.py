from json       import loads
from statistics import stdev
from sys        import argv
from util       import get_active_spread_groups, spread


SCANS = loads(open("./scans.json", "r").read())


def moving_average(src, lag):

    res = [ None for i in range(len(src)) ]

    for i in range(lag - 1, len(src)):

        x = 0

        for j in range(0, lag):

            x += src[i - j] / lag

        res[i] = x
    
    return res


# Not implemented: no consistent high / low data
'''
def atr(spread_id, spread_group, lag):

    spread_rows = spread_group.get_spread_rows(spread_id)

    tr = [
        max(
            spread_rows[i][spread.high] - spread_rows[i][spread.low],
            spread_rows[i][spread.high] - spread_rows[i - 1][spread.settle],
            spread_rows[i][spread.low] - spread_rows[i - 1][spread.settle]
        )
        for i in range(1, len(spread_rows))
    ]

    res = moving_average(tr, int(lag))
    
    return res
'''


def dte(spread_id, spread_group, params = None):

    spread_rows = spread_group.get_spread_rows(spread_id)

    return [ row[spread.dte] for row in spread_rows]


# Not implemented: no consistent high / low data
'''
def range_score(spread_id, spread_group, lags):

    spread_rows = spread_group.get_spread_rows(spread_id)
    lags        = lags.split(",")
    long        = int(lags[0])
    short       = int(lags[1])
    ma_len      = int(lags[2])

    highs       = [ row[spread.high] for row in spread_rows]
    lows        = [ row[spread.low] for row in spread_rows]

    long_max_highs  = [ None for _ in highs ]
    long_min_lows   = [ None for _ in highs ]
    long_rngs       = [ None for _ in highs ]
    
    short_max_highs = [ None for _ in highs ]
    short_min_lows  = [ None for _ in highs ]
    short_rngs      = [ None for _ in highs ]


    for i in range(long, len(highs)):

        long_max_highs[i]   = max(highs[i - long:i])
        long_min_lows[i]    = min(lows[i - long:i]) 
        long_rngs[i]        = long_max_highs[i] - long_min_lows[i]

    for i in range(short, len(highs)):

        short_max_highs[i]  = max(highs[i - short:i])
        short_min_lows[i]   = min(lows[i - short:i])
        short_rngs[i]       = short_max_highs[i] - short_min_lows[i]
                        
    pct = [
        short_rngs[i] / long_rngs[i]
        for i in range(long, len(long_rngs))
    ]

    res = moving_average(pct, ma_len)

    return res
'''


def range_pct(spread_id, spread_group, lag):

    spread_rows = spread_group.get_spread_rows(spread_id)
    lag         = int(lag)
    settles     = [ row[spread.settle] for row in spread_rows ]
    res         = [ 0 for row in spread_rows ]

    if len(settles) >= lag:

        for i in range(lag, len(settles)):

            max_settle = max(settles[i - lag:i])
            min_settle = min(settles[i - lag:i])

            rng = max_settle - min_settle

            res[i] = (settles[i] - min_settle) / rng if rng != 0 else 0

    return res


def sigma(spread_id, spread_group, lag):

    spread_rows = spread_group.get_spread_rows(spread_id)
    lag         = int(lag)
    d_settle    = [ 0.0 for _ in spread_rows]
    res         = [ None for _ in spread_rows ]

    for i in range(1, len(d_settle)):

        d_settle[i] = spread_rows[i][spread.settle] - spread_rows[i -1][spread.settle]
                    
    for i in range(lag, len(d_settle)):

        res[i] = stdev(d_settle[i - lag:i])

    return res


def zscore(spread_id, spread_group, params = None):

    spread_rows = spread_group.get_spread_rows(spread_id)
    mu          = spread_group.mu
    sigma       = spread_group.sigma

    res = [
        (row[spread.settle] - mu) / sigma
        for row in spread_rows
    ]
    
    return res


CRITERIA_FUNCS = {
    #"atr":         atr,
    "dte":          dte,
    #"range_score": range_score,
    "range_pct":    range_pct,
    "sigma":        sigma,
    "zscore":       zscore
}


def perform_scan(title, definition, criteria):

    spread_groups = get_active_spread_groups(**definition)

    print(title.ljust(15))
    print("".ljust(15) + "".join([ crit.ljust(15) for crit in criteria ]) + "\n")

    spread_groups = sorted(spread_groups, key = lambda g: g.group_id[0])

    for spread_group in spread_groups:

        active_ids = sorted(spread_group.active_ids, key = lambda i: (i[0][1], i[0][0]))

        for spread_id in active_ids:

            printable_id = [ leg[0] for leg in spread_id ] # months
            printable_id.append(f" {spread_id[0][1][2:]}") # year

            output = "".join(printable_id).ljust(15)

            for crit in criteria:

                params  = None
                func    = crit

                if ":" in crit:

                    parts = crit.split(":")

                    func    = parts[0]
                    params  = parts[1]

                res     = CRITERIA_FUNCS[func](spread_id, spread_group, params)
                latest  = res[-1]

                if isinstance(latest, float):

                    latest = f"{latest:0.3f}"

                output += f"{latest}".ljust(15)

            print(output)

    

if __name__ == "__main__":

    criteria = SCANS["criteria"]
    symbols  = SCANS["symbols"]

    if len(argv) > 1:

        definitions = argv[1:]

        for definition in definitions:

            parts = definition.split(":")

            symbol          = parts[0]
            mode            = parts[1]
            width           = int(parts[2])
            aggregate_by    = parts[3]
            max_months      = int(parts[4])

            definition = {
                "symbol":       symbol,
                "mode":         mode,
                "width":        width,
                "aggregate_by": aggregate_by,
                "max_months":   max_months
            }

            perform_scan(f"{parts[0]} {mode}:{width}", definition, criteria)

            print("\n")
    
    else:    

        for symbol, params in symbols.items():

            for mode, widths in params["modes"].items():

                for width in widths:

                    definition = {
                        "symbol":       symbol,
                        "mode":         mode,
                        "width":        width,
                        "aggregate_by": params["aggregate_by"],
                        "max_months":   params["max_months"]
                    }

                    perform_scan(f"{symbol} {mode}:{width}", definition, criteria)

                    print("\n")