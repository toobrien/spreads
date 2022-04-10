from calendar import month
from    datetime                import  datetime
from    enum                    import  IntEnum
from    json                    import  loads
import  plotly.graph_objects    as      go
from    sqlite3                 import  connect, Connection
from    statistics              import  mean, stdev
from    typing                  import  List


CONFIG      = loads(open("./config.json").read())
MIN_DTE     = CONFIG["min_dte"]
MAX_DTE     = CONFIG["max_dte"]
YEAR        = datetime.now().year
MONTH       = datetime.now().month
MIN_OPACITY = 0.2
SCATTER_COL = 1
PDF_COL     = 2
HISTORY     = 10

MONTHS = {
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


# ----- db -----

def get_db() -> Connection:

    db = None

    with open("./config.json") as fd:

        db_path = loads(fd.read())["db_path"]
        db = connect(db_path)

    return db


def get_term_days(
    db:     Connection, 
    symbol: str, 
    begin:  str, 
    end:    str
) -> List[List]:

    cur = db.cursor()

    terms = cur.execute(f'''
        SELECT DISTINCT
            date,
            month,
            year,
            settle,
            CAST(julianday(to_date) - julianday(date) AS INT)
        FROM ohlc INNER JOIN metadata USING(contract_id)
        WHERE name = "{symbol}"
        AND date BETWEEN "{begin}" AND "{end}"
        ORDER BY date ASC, year ASC, month ASC;
    ''').fetchall()

    # group by day

    term_days = []
    
    cur_date    = terms[0][term.date]
    cur_day     = []

    for r in terms:

        if r[term.date] != cur_date:
        
            term_days.append(cur_day)

            cur_date    = r[term.date]
            cur_day     = []

        cur_day.append(r)

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
    
    settle  = 0
    
    for l in legs:

        settle += term_day[i + l[leg.idx]][term.settle] * l[leg.ratio] 

    dte     = term_day[i][term.dte]
    spread     = [ date, id, settle, dte ]

    return spread


def get_spread_ids(
    term_day:   List, 
    legs:    tuple
) -> dict[tuple : int]:

    ids = {}

    for i in range(len(term_day) - len(legs)):
            
        spread_id = tuple(
            (
                term_day[i + l[leg.idx]][term.month],
                term_day[i + l[leg.idx]][term.year]
            )
            for l in legs
        )

        ids[spread_id] = i

    return ids


def get_legs(mode: str):

    legs = None

    if mode == "cal":

        legs = ( 
            ( 0, -1 ),
            ( 1,  1 ) 
        )

    elif mode == "fly":

        legs = ( 
            ( 0,  1 ), 
            ( 1, -2 ),
            ( 2,  1 ) 
        )

    elif mode == "dfly":

        legs = ( 
            ( 0,  1 ),
            ( 1, -3 ),
            ( 2,  3 ), 
            ( 3, -1 ) 
        )

    elif mode == "cond":

        legs = (
            ( 0,  1 ),
            ( 1, -1 ),
            ( 2, -1),
            ( 3,  1 )
        )

    return legs


def get_seasons(term_day: List, legs: List[tuple]):

    seasons = []

    for i in range(len(term_day) - len(legs)):

        seasons.append(
            ( term_day[i + l[leg.idx]][term.month] )
            for l in legs
        )

    return set(seasons)


def by_season(
    term_days: List, 
    legs: List[tuple], 
    seasons: set
):

    latest  = term_days[-1]
    lim     = len(latest) - len(legs)

    res = { 
        season : {}
        for season in seasons
    }

    for day in term_days:

        for i in range(min(len(day) - len(legs), lim)):

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
    term_days:  List,
    legs:       List[tuple],
    sequences:  set
):

    res = {
        seq: {}
        for seq in sequences
    }

    for day in term_days:
    
        for i in sequences:

            if  i + len(legs) < len(day) and \
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

        lim = len(day) - len(legs)
    
        for i in range(lim):

            if dte_max >= day[i][term.dte] >= dte_min:
                
                    s       = get_spread_row(day, i, legs)
                    s_id    = s[spread.id]

                    if s_id not in res[0]:

                        res[0][s_id] = []
                    
                    res[0][s_id].append(s)

    return res


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
        color           = "#FF0000" if current else "#0000FF"
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

    out = []

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

                out.append(
                    [
                        f"{symbol} {friendly_id} {mode}\t".ljust(15),
                        f"{latest[0][spread.date]}\t".ljust(10),
                        f"{latest[0][spread.dte]}\t".rjust(5),
                        f"{(latest[0][spread.settle] - mu) / sigma: 0.2f}".rjust(8),
                        "".join([ f"{r[spread.settle]: 0.5f}".rjust(12) for r in latest ])
                    ]
                )

    # sort by dte

    out = sorted(out, key = lambda r: int(r[2]))
    
    for line in out:

        print("".join(line))

    print("\n")