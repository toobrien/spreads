from    datetime                import  datetime
from    enum                    import  IntEnum
from    json                    import  loads
from    numpy                   import  log
import  polars                  as      pl
import  plotly.graph_objects    as      go
from    sys                     import  path
from    statistics              import  mean, stdev
from    typing                  import  List, Tuple

path.append("..")

from    data.cat_df            import  cat_df


CONFIG      = loads(open("./config.json").read())
MIN_DTE     = CONFIG["min_dte"]
MAX_DTE     = CONFIG["max_dte"]
YEAR        = datetime.now().year
MONTH       = datetime.now().month
MIN_OPACITY = 0.2
SCATTER_COL = 1
PDF_COL     = 2
HISTORY     = 20
BEGIN       = CONFIG["start_date"]
END         = CONFIG["end_date"]
TERM_DAYS   = {}
LOG         = False
MONTHS      = {
    "F": 1,
    "G": 2,
    "H": 3,
    "J": 4,
    "K": 5,
    "M": 6,
    "N": 7,
    "Q": 8,
    "U": 9,
    "V": 10,
    "X": 11,
    "Z": 12
}


# ----- classes -----

class term(IntEnum):

    date        = 0
    month       = 1
    year        = 2
    settle      = 3
    dte         = 4


class spread(IntEnum):

    date        = 0
    id          = 1
    settle      = 2
    dte         = 3


class leg(IntEnum):

    idx     = 0
    ratio   = 1


class spread_group:


    active_ids  = None
    group_id    = None
    mu          = None
    rows        = None
    sigma       = None
    spread_ids  = None


    def __init__(self, active_ids, group_id, rows, spread_ids):

        self.active_ids = active_ids
        self.group_id   = group_id
        self.spread_ids = spread_ids
        self.rows       = rows

        settles = [ row[spread.settle] for row in self.rows]

        self.mu     = mean(settles)
        self.sigma  = stdev(settles)

    
    def get_spread_rows(self, spread_id):

        return [
            row
            for row in self.rows
            if row[spread.id] == spread_id
        ]


    def get_all_rows(self):

        return self.rows


class spread_wrapper:


    group_id        = None
    id              = None
    data            = None


    def __init__(self, group_id, id, data):

        self.group_id   = group_id
        self.id         = id
        self.data       = data


# ----- db -----


def get_term_days(symbol: str, start: str = None, end: str = None):
    
    if not start:

        start = BEGIN

    if not end:

        end = END

    terms = cat_df(
                "futs",
                symbol,
                start,
                end
            ).sort(
                [ "date", "year", "month" ]
            ).select(
                [
                    "date",
                    "month",
                    "year",
                    "settle",
                    "dte"
                ]
            )
    
    if LOG:

        terms = terms.with_columns(terms["settle"].apply(log))

    terms = terms.rows()

    term_days   = []
    cur_date    = terms[0][term.date]
    cur_day     = []

    for row in terms:

        if row[term.date] != cur_date:

            term_days.append(cur_day)

            cur_date    = row[term.date]
            cur_day     = []
        
        cur_day.append(row)
    
    term_days.append(cur_day)

    return term_days


# ----- spreads -----


def get_spread_row(term_day: List, i: int, legs: List):

    date        = term_day[i][term.date]
    id          = tuple(
        ( 
            term_day[i + l[leg.idx]][term.month], 
            term_day[i + l[leg.idx]][term.year]
        )
        for l in legs
    )
    settle       = 0
    
    for l in legs:

        settle += term_day[i + l[leg.idx]][term.settle] * l[leg.ratio]

    dte     = term_day[i][term.dte]
    spread  = [ date, id, settle, dte ]

    return spread


def get_spread_ids(
    term_day:       List,
    legs:           tuple,
    total_width:    int
) -> dict[tuple : int]:

    ids = {}

    for i in range(len(term_day) - total_width):
            
        spread_id = tuple(
            (
                term_day[i + l[leg.idx]][term.month],
                term_day[i + l[leg.idx]][term.year]
            )
            for l in legs
        )

        ids[spread_id] = i

    return ids


# spread rules:
# 
# calendar:         https://www.cmegroup.com/confluence/display/EPICSANDBOX/Spreads+and+Combinations+Available+on+CME+Globex#SpreadsandCombinationsAvailableonCMEGlobex-SPStandardCalendarSpread
# reverse calendar: https://www.cmegroup.com/confluence/display/EPICSANDBOX/Spreads+and+Combinations+Available+on+CME+Globex#SpreadsandCombinationsAvailableonCMEGlobex-EQCalendarSpread
# butterfly:        https://www.cmegroup.com/confluence/display/EPICSANDBOX/Spreads+and+Combinations+Available+on+CME+Globex#SpreadsandCombinationsAvailableonCMEGlobex-BFButterfly
# double butterfly: https://www.cmegroup.com/confluence/display/EPICSANDBOX/Spreads+and+Combinations+Available+on+CME+Globex#SpreadsandCombinationsAvailableonCMEGlobex-DFDoubleButterfly
# condor:           https://www.cmegroup.com/confluence/display/EPICSANDBOX/Spreads+and+Combinations+Available+on+CME+Globex#SpreadsandCombinationsAvailableonCMEGlobex-CFCondor
#
# notes: 
#   
#   - condor follows the "strict" definition, in which all legs must be equidistant.
#   - broken butterfly not supported.

def get_legs(
    mode:   str, 
    width:  int
) -> tuple[int, int]:

    legs        = None

    if mode == "cal":

        legs = ( 
            ( 0, -1 ),
            ( width,  1 ) 
        )

    elif mode == "rcal":

        legs = (

            ( 0,  1 ),
            ( width, -1 )

        )

    elif mode == "fly":

        legs = ( 
            ( 0,  1 ), 
            ( width, -2 ),
            ( 2 * width,  1 ) 
        )

    elif mode == "dfly":

        legs = ( 
            ( 0,  1 ),
            ( width, -3 ),
            ( 2 * width,  3 ), 
            ( 3 * width, -1 ) 
        )

    elif mode == "cond":

        legs = (
            ( 0,  1 ),
            ( width, -1 ),
            ( 2 * width, -1),
            ( 3 * width,  1 )
        )

    return legs


def get_seasons(term_day: List, legs: List[tuple]):

    seasons = []

    for i in range(len(term_day) - len(legs) + 1):

        seasons.append(
            ( term_day[i + l[leg.idx]][term.month] )
            for l in legs
        )

    return set(seasons)


def by_season(
    term_days:      List, 
    legs:           List[tuple],
    total_width:    int, 
    seasons:        set
):

    latest  = term_days[-1]
    lim     = len(latest) - total_width

    res = { 
        season : {}
        for season in seasons
    }

    for day in term_days:

        for i in range(min(len(day) - total_width, lim)):

            if MAX_DTE >= day[i][term.dte] >= MIN_DTE:
            
                s       = get_spread_row(day, i, legs)
                s_id    = s[spread.id]
                season  = tuple( t[0] for t in s_id )

                if season in seasons:

                    if s_id not in res[season]:

                        res[season][s_id] = []
                    
                    res[season][s_id].append(s)

    return res


def by_sequence(
    term_days:      List,
    legs:           List[tuple],
    total_width:    int,
    sequences:      set
):

    res = {
        seq: {}
        for seq in sequences
    }

    for day in term_days:
    
        for i in sequences:

            if  i + total_width < len(day) and \
                MAX_DTE >= day[i][term.dte] >= MIN_DTE:
                
                    s       = get_spread_row(day, i, legs)
                    s_id    = s[spread.id]

                    if s_id not in res[i]:

                        res[i][s_id] = []
                    
                    res[i][s_id].append(s)

    return res


def all(
    term_days:  List,
    legs:       List[tuple],
    dte_min:    int,
    dte_max:    int
):

    res = {
        0: {}
    }

    for day in term_days:

        lim = len(day) - len(legs) + 1
    
        for i in range(lim):

            if dte_max >= day[i][term.dte] >= dte_min:
                
                    s       = get_spread_row(day, i, legs)
                    s_id    = s[spread.id]

                    if s_id not in res[0]:

                        res[0][s_id] = []
                    
                    res[0][s_id].append(s)

    return res


# keep only rows belonging to identified contracts
# contracts = [ (M, YYYY), ... ]
#
# note: allows duplicates

def filter_by_sea(term_days: List[List], contracts: Tuple):

    res = []

    for term_day in term_days:

        filtered = []

        for r in term_day:

            for contract in contracts:

                if r[term.month] == contract[0] and r[term.year] == contract[1]:

                    filtered.append(r)

        if len(filtered) == len(contracts):

            res.append(filtered)

    return res


def get_active_spread_groups(
    symbol:         str,
    mode:           str,
    width:          int,
    aggregate_by:   str,
    max_months:     int
):

    if symbol not in TERM_DAYS:

        TERM_DAYS[symbol] = get_term_days(symbol)

    term_days   = TERM_DAYS[symbol]
    today       = term_days[-1][:max_months]
    legs        = get_legs(mode, width)
    total_width = legs[-1][0]
    todays_ids  = get_spread_ids(today, legs, total_width)

    spread_group_source_data = None

    if aggregate_by == "sea":

        seasons = {
            tuple(
                t[0] 
                for t in spread_id
            )
            for spread_id in todays_ids
        }

        spread_group_source_data = by_season(term_days, legs, total_width, seasons)
    
    else:

        sequences = {
                i for i in range(len(today) - total_width)
            }

        spread_group_source_data = by_sequence(term_days, legs, total_width, sequences)

    spread_groups = []

    for group_id, group_data in spread_group_source_data.items():

        active_ids = [
            spread_id
            for spread_id, _ in group_data.items()
            if spread_id in todays_ids
        ]

        spread_rows = [
            row
            for _, rows in group_data.items()
            for row in rows
        ]

        spread_ids = [
            spread_id
            for spread_id, _ in group_data.items()
        ]

        spread_groups.append(
            spread_group(
                active_ids,
                group_id,
                spread_rows,
                spread_ids
            )
        )

    return spread_groups


# ----- plotting -----


def is_current(spread_month: str, spread_year: int):

    return MONTHS[spread_month] >= MONTH and spread_year == YEAR or spread_year > YEAR


# calculate mean and stdev for z-score

def z_stats(spreads: dict):

    mu      = 0
    sigma   = 1

    settles = [
        r[spread.settle]
        for id, rows in spreads.items()
        for r in rows
    ]

    try:

        mu      = mean(settles)
        sigma   = stdev(settles)
 
    except:

        # one data point, probably...
    
        pass

    return mu, sigma


def add_scatters(
    fig:        go.Figure,
    row:        int,
    spreads:    dict
):

    if not spreads:

        return

    traces  = {}
    opacity = MIN_OPACITY
    step    = (1 - MIN_OPACITY) / len(spreads)

    mu, sigma = z_stats(spreads)
    
    # traces

    for id, rows in spreads.items():

        spread_month    = id[0][0]
        spread_year     = int(id[0][1])
        current         = is_current(spread_month, spread_year)
        color           = None if current else "#0000FF"
        opacity         = min(opacity + step, 1)
        friendly_id     = "".join(
            t[0]
            for t in id
        ) + f" {id[0][1]}"

        traces[friendly_id] = {
            "x": [ r[spread.dte] for r in rows ],
            "y": [ r[spread.settle] for r in rows ],
            "text": [
                f"{r[spread.date]} z: {(r[spread.settle] - mu) / sigma: 0.2f}"
                for r in rows
            ],
            "name": friendly_id,
            "mode": "markers",
            "marker": {
                "color": color
            },
            "opacity": opacity
        }

    for id, trace in traces.items():

        fig.add_trace(
            go.Scatter(**trace),
            row = row,
            col = SCATTER_COL
        )


def add_pdfs(
    fig:        go.Figure,
    row:        int,
    spreads:    List
):
        
    fig.add_trace(
        go.Histogram(
            x = [ 
                r[spread.settle] 
                for _, rows in spreads.items()
                for r in rows
            ],
            name = "pdf",
            marker = {
                "color": "#0000FF"
            },
            histnorm    = "probability"
        ),
        row = row,
        col = PDF_COL
    )


# ----- printing -----


def print_spreads(symbol: str, mode: str, plots: dict):

    out = {}

    for _, spreads in plots.items():

        mu, sigma = z_stats(spreads)

        for spread_id, rows in spreads.items():

            spread_month    = spread_id[0][0]
            spread_year     = spread_id[0][1]

            if is_current(spread_month, int(spread_year)):

                friendly_id = "".join(
                    t[0]
                    for t in spread_id
                ) + f" {spread_year[2:]}"

                latest = rows[-HISTORY:]
                latest = list(reversed(latest))

                out[f"{symbol} {friendly_id} {mode}"] = [
                    [
                        f"{rec[spread.date]}".ljust(10),
                        f"{rec[spread.dte]}".rjust(5),
                        f"{(rec[spread.settle] - mu) / sigma: 0.2f}".rjust(8),
                        f"{rec[spread.settle]: 0.5f}".rjust(12)
                    ]
                    for rec in latest
                ]    

    # sort by dte

    sorted_spread_ids = sorted(out.keys(), key = lambda k: float(out[k][0][1]))
    
    # print spreads sequentially

    for spread_id in sorted_spread_ids:

        print("\n", spread_id.center(35), "\n")
        print("date".center(10), "dte".center(5), "sigma".center(8), "settle".center(12))
        print("-" * 10, "-" * 5, "-" * 8, "-" * 12, "\n")

        recs = out[spread_id]

        for rec in recs:
        
            print("".join(rec))

    print("\n")


# ----- continuous contracts -----
    

CACHE = {}

class r(IntEnum):

    id              = 0
    date            = 1
    month           = 2
    year            = 3
    settle          = 4
    dte             = 5


def get_groups(
    symbol: str,
    start: str,
    end: str
):
    
    series_id = (symbol, start, end)

    if series_id in CACHE:

        return CACHE[series_id]

    if not start:

        start = BEGIN

    if not end:

        end = END

    terms = cat_df(
                "futs",
                symbol,
                start,
                end
            ).sort(
                [ "date", "year", "month" ]
            ).select(
                [
                    "contract_id",
                    "date",
                    "month",
                    "year",
                    "settle",
                    "dte"
                ]
            )

    if LOG:

        terms = terms.with_columns(terms["settle"].apply(log))

    terms       = terms.rows()
    term_days   = []
    cur_date    = terms[0][r.date]
    cur_day     = []

    for row in terms:

        if row[r.date] != cur_date:

            term_days.append(cur_day)

            cur_date    = row[r.date]
            cur_day     = []
        
        cur_day.append(row)
    
    term_days.append(cur_day)

    CACHE[series_id] = term_days

    return term_days


def get_continuous(
    symbol: str,
    start:  str,
    end:    str,
    term:   int,
    mode:   str
):

    groups  = get_groups(symbol, start, end)
    series  = []

    if mode == "nearest":

        # schwager pg. 280

        series = [ group[term] for group in groups ]

    elif mode == "spread_adjusted":

        # schwager pg. 282; use ratio instead of difference

        cum_adj = 1.0

        for i in range(1, len(groups)):

            try:

                cur         = groups[i][term]
                prev        = groups[i - 1][term]
                prev_next   = groups[i - 1][term + 1]

                if cur[r.id] != prev[r.id]:

                    # contract expired yesterday, compute roll factor

                    cum_adj *= prev_next[r.settle] / prev[r.settle]

                rec             = [ field for field in cur ]
                rec[r.settle]   *= cum_adj

                series.append(rec)
                
            except Exception as e:

                # negative price or missing a term

                print(e)
        
        for rec in series:

            rec[r.settle] /= cum_adj

    return series