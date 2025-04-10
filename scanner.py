from    json                    import  loads
import  numpy                   as      np
import  polars                  as      pl
import  plotly.graph_objects    as      go
from    statistics              import  mean, stdev
from    sys                     import  argv
from    time                    import  time
from    typing                  import  List
from    util                    import  get_active_spread_groups, spread


pl.Config.set_tbl_cols(-1)
pl.Config.set_tbl_rows(-1)


SCANS       = loads(open("./scans.json", "r").read())
DF          = None
CACHED      = {}


def moving_average(src, lag):

    res = [ None for i in range(len(src)) ]

    for i in range(lag - 1, len(src)):

        x = 0

        for j in range(0, lag):

            x += src[i - j] / lag

        res[i] = x
    
    return res


def dte(spread_id, spread_group, params = None):

    spread_rows = spread_group.get_spread_rows(spread_id)

    return [ row[spread.dte] for row in spread_rows]


def rng_score(spread_id, spread_group, lags):

    spread_rows = spread_group.get_spread_rows(spread_id)
    lags        = lags.split(",")
    short_lag   = int(lags[0])
    long_lag    = int(lags[1])
    settles     = [ row[spread.settle] for row in spread_rows ]
    sigmas      = [ None for _ in spread_rows ]
    res         = [ None for _ in spread_rows ]

    if len(settles) >= long_lag:

        '''
        for i in range(1, len(settles)):

            d_settles = [ 
                            settles[i] - settles[i - 1]
                            for i in range(len(settles))
                        ]'
        '''

        sigmas = sigma(spread_id, spread_group, short_lag)

        for i in range(long_lag, len(settles)):

            rng     = max(settles[i - long_lag:i]) - min(settles[i - long_lag:i])
            res[i]  = sigmas[i] / rng if rng != 0 else 0 
    
    return res


def range_pct(spread_id, spread_group, lag):

    spread_rows = spread_group.get_spread_rows(spread_id)
    lag         = int(lag)
    settles     = [ row[spread.settle] for row in spread_rows ]
    res         = [ 0 for _ in spread_rows ]

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

        d_settle[i] = spread_rows[i][spread.settle] - spread_rows[i - 1][spread.settle]
                    
    for i in range(lag, len(d_settle)):

        res[i] = stdev(d_settle[i - lag:i])

    return res


def z_chg(spread_id, spread_group, lag):

    rows    = spread_group.get_spread_rows(spread_id)
    latest  = rows[-1][spread.settle] - rows[-2][spread.settle]
    df      = spread_group.get_df()
    chgs    = df.with_columns((pl.col("settle").diff().alias("chg")))["chg"].drop_nulls().to_numpy()
    mu      = np.mean(chgs)
    sigma   = np.std(chgs)
    z       = (latest - mu) / sigma
    res     = [ z ]

    return res


def z_settle(spread_id, spread_group, params = None):

    spread_rows = spread_group.get_spread_rows(spread_id)
    mu          = spread_group.mu
    sigma       = spread_group.sigma

    res = [
        (row[spread.settle] - mu) / sigma
        for row in spread_rows
    ]
    
    return res


def forecast(spread_id, spread_group, horizon):

    horizon     = int(horizon)
    df          = spread_group.get_df()
    med         = df.group_by("dte").agg(median = pl.col("settle").median())
    spread_rows = spread_group.get_spread_rows(spread_id)
    cur_dte     = spread_rows[-1][spread.dte]
    hor_dte     = max(cur_dte - horizon, 0)
    med_i       = med.filter(pl.col("dte") == cur_dte).get_column("median").item()
    med_j       = med.filter(pl.col("dte") == hor_dte).get_column("median").item()
    f           = med_j - med_i

    return [ f ]


CRITERIA_FUNCS = {
    "dte":          dte,
    "rng_score":    rng_score,
    "sigma":        sigma,
    "z_chg":        z_chg,
    "z_settle":     z_settle,
    "forecast":     forecast
}


def passes(latest, func):

    # temporary solution

    if func == "z_settle":

        return abs(latest) > 2
    
    else:
        
        return True
    

def plot(idx):

    id              = DF.filter(pl.col("idx") == idx).get_column("id").item()
    spread_group    = CACHED[id]
    group_id        = "".join(spread_group.group_id)
    df              = spread_group.get_df()
    features        = df.group_by("dte").agg(
                        pl.col("settle").median().alias("med"),
                        pl.col("settle").quantile(0.05).alias("lo"),
                        pl.col("settle").quantile(0.95).alias("hi")
                    ).sort("dte", descending = True)
    
    traces = [
        ( features["dte"],  features["med"], "med", "#FF00FF",  "lines" ),
        ( features["dte"],  features["lo"],  "lo",  "#CCCCCC",  "lines" ),
        ( features["dte"],  features["hi"],  "hi",  "#CCCCCC",  "lines" )
    ]

    for id_ in spread_group.active_ids:

        rows    = spread_group.get_spread_rows(id_)
        dte     = [ r[spread.dte] for r in rows ]
        settle  = [ r[spread.settle] for r in rows ]
        title   = f"{group_id} {id_[0][1][2:]}"
        
        traces.append(( dte, settle, title, None, "markers" ))
    
    fig = go.Figure()

    for trace in traces:

        t = {
            "x":    trace[0],
            "y":    trace[1],
            "name": trace[2],
            "mode": trace[4]
        }

        if trace[3]:

            t[trace[4][:-1]] = { "color": trace[3] }

        fig.add_trace(go.Scattergl(t))

    fig.show()


def run(definition, criteria):

    point_value     = definition["point_value"]
    
    del definition["point_value"]

    spread_groups   = sorted(get_active_spread_groups(**definition), key = lambda g: g.group_id[0])
    symbol          = definition["symbol"]
    mode            = definition["mode"]
    width           = definition["width"]
    rows            = []
    
    for spread_group in spread_groups:

        active_ids = sorted(spread_group.active_ids, key = lambda i: (i[0][1], i[0][0]))

        for spread_id in active_ids:

            display = True
            row     = [ 
                        symbol,
                        " ".join([ 
                            "".join([ leg[0] for leg in spread_id ]),   # months
                            f"{spread_id[0][1][2:]}",                   # year
                            f"{mode}:{width}"
                        ])
                    ]

            for crit in criteria:

                params          = None
                func            = crit
                output_dollars  = False

                if ":" in crit:

                    parts   = crit.split(":")
                    func    = parts[0]
                    params  = parts[1]

                    if "$" in parts:

                        output_dollars = True

                res = CRITERIA_FUNCS[func](spread_id, spread_group, params)

                if res:

                    latest = res[-1]

                    if not passes(latest, func):

                        display = False

                        break

                    if isinstance(latest, float):

                        if output_dollars:

                            latest = int(f"{latest * point_value:0.0f}")

                        else:

                            latest = float(f"{latest:0.3f}")

                    row.append(latest)
                
                else:

                    row.append(None)

            if display:
                
                rows.append(row)
                
                CACHED[row[1]] = spread_group
            
            else:

                display = True

    data = {
            "symbol":   [ row[0] for row in rows ],
            "id":       [ row[1] for row in rows ]
        }
    
    for i in range(len(criteria)):

        data[criteria[i]] = [ row[i + 2] for row in rows ]

    df = pl.DataFrame(data)

    return df


def scan(years: int, definitions: List[dict] = None):

    criteria    = SCANS["criteria"]
    symbols     = SCANS["symbols"]
    dfs         = []

    if definitions:

        for definition in definitions:

            parts = definition.split(":")

            symbol          = parts[0]
            mode            = parts[1]
            width           = int(parts[2])
            aggregate_by    = parts[3]
            max_months      = int(parts[4])
            point_value     = float(parts[5])

            definition = {
                "symbol":       symbol,
                "mode":         mode,
                "width":        width,
                "aggregate_by": aggregate_by,
                "max_months":   max_months,
                "point_value":  point_value,
                "years":        years
            }

            df = run(definition, criteria)

            if df.height != 0:

                dfs.append(df)
    
    else:    

        for symbol, params in symbols.items():

            for mode, widths in params["modes"].items():

                for width in widths:

                    definition = {
                        "symbol":       symbol,
                        "mode":         mode,
                        "width":        width,
                        "aggregate_by": params["aggregate_by"],
                        "max_months":   params["max_months"],
                        "point_value":  params["point_value"],
                        "years":        years
                    }

                    df = run(definition, criteria)

                    if df.height != 0:

                        dfs.append(df)
    
    DF = pl.concat(dfs).with_row_index("idx")

    return DF


if __name__ == "__main__":

    t0          = time()
    years       = int(argv[1])
    definitions = argv[2:]
    DF          = scan(years, definitions)

    print(f"{time() - t0:0.1f}s\n")

    while True:

        next    = input("> ").split()
        cmd     = next[0]

        if cmd == "plot":

            plot(int(next[1]))

        elif cmd == "sort":

            DF = DF.sort(next[1], descending = "desc" in next)

        elif cmd == "print":

            if len(next) > 1:

                print(DF.filter(pl.col("symbol") == next[1]))
            
            else:
            
                print(DF)

        elif cmd == "exit":

            break