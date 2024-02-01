import  plotly.graph_objects    as      go
from    re                      import  compile
from    sys                     import  argv
from    typing                  import  List
from    util                    import  get_continuous, r


# python continuous.py RB:0:1 HO:0:-1 log
# python continuous.py HO:0:1 HO:3:-2 HO:6:1:1 nearest


def continuous_spread(
    symbols:    List[str],
    terms:      List[int],
    quantities: List[int],
    start:      str,
    end:        str,
    mode:       str     = "spread_adjusted",
    log:        bool    = False
):

    series = [
        get_continuous(symbols[i], start, end, terms[i], mode, log)
        for i in range(len(symbols))
    ]

    series = [
        {
            rec[r.date]: rec
            for rec in recs
        }
        for recs in series
    ]

    date_idx = set.intersection(*[ set(idx.keys()) for idx in series ])
    date_idx = sorted(list(date_idx))
    
    spread = {}

    for idx in series:

        for date in date_idx:

            if date not in spread:
            
                spread[date] = []

            spread[date].append(idx[date][r.settle])

    spread = [
                [ date, *settles ]
                for date, settles in spread.items()
            ]

    for rec in spread:

        for i in range(1, len(rec)):

            rec[i] = rec[i] * quantities[i - 1]
    
    spread = [
        [ rec[0], sum(rec[1:]) ]
        for rec in spread
    ]

    return spread


if __name__ == "__main__":


    log     = "log" in argv
    mode    = "nearest" if "nearest" in argv else "spread_adjusted"
    pattern = compile("\d{4}-\d{2}-\d{2}")
    dates   = [ date for date in argv if pattern.match(date) ]
    start   = dates[0] if dates else "1900-01-01"
    end     = dates[1] if len(dates) > 1 else "2100-01-01"
    dfns    = [ arg.split(":") for arg in argv if ":" in arg ]
    symbols = [ dfn[0] for dfn in dfns ]
    terms   = [ int(dfn[1]) for dfn in dfns ]
    qtys    = [ int(dfn[2]) for dfn in dfns ]
    spread  = continuous_spread(symbols, terms, qtys, start, end)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            {
                "x": [ rec[0] for rec in spread ],
                "y": [ rec[1] for rec in spread ]
            }
        )
    )

    fig.show()