import  plotly.graph_objects    as      go
from    plotly.subplots         import  make_subplots
from    sys                     import  argv
from    time                    import  time
from    util                    import  get_term_days, term


HEIGHT          = 500
MAX_CONTRACTS   = 12
MAX_HISTORY     = 90


# python curve.py 12 CL HO RB NG HE LE VX ZR ZC ZW ZS ZL ZM


def render(sym: str, fig, row_idx = int):

    days        = get_term_days(sym)[-MAX_HISTORY:]
    latest      = days[-1]
    cur_date    = latest[0][term.date]
    prev_date   = days[-2][0][term.date]
    today       = []
    yesterday   = []
    high        = []
    low         = []
    X           = [ i for i in range(MAX_CONTRACTS) ]
    X_labels    = []

    for row in latest[:MAX_CONTRACTS]:

        month       = row[term.month]
        year        = row[term.year]
        contract    = [ 
                        rec
                        for day in days
                        for rec in day if rec[term.month] == month and rec[term.year] == year
                    ]
        
        today.append(contract[-1][term.settle])
        yesterday.append(contract[-2][term.settle])

        settles = [ rec[term.settle] for rec in contract ]

        high.append(max(settles))
        low.append(min(settles))

        X_labels.append(f"{month}{year[-1]}")

        pass

    traces = [
        ( high, f"{sym} high [{MAX_HISTORY}]", "#cccccc", 1.0 ),
        ( low, f"{sym} low [{MAX_HISTORY}]", "#cccccc", 1.0 ),
        ( today, f"{sym} {cur_date}", "#0000FF", 1.0 ),
        ( yesterday, f"{sym} {prev_date}", "#0000FF", 0.3 )
    ]

    for trace in traces:

        params = {
            "x":        X,
            "y":        trace[0],
            "name":     trace[1],
            "mode":     "lines+markers",
            "line":     { "color": trace[2] },
            "opacity":  trace[3]
        }

        if trace[0] == low:

            params["fill"] = "tonexty"

        fig.add_trace(
            go.Scatter(params),
            row = row_idx,
            col = 1
        )

    fig.update_xaxes(
        tickvals    = X,
        ticktext    = X_labels,
        row         = row_idx,
        col         = 1
    )


if __name__ == "__main__":

    t0              = time()
    MAX_CONTRACTS   = int(argv[1])
    syms            = argv[2:]
    n_syms          = len(syms)
    fig             = make_subplots(
                        rows                = n_syms, 
                        cols                = 1,
                        subplot_titles      = tuple( sym for sym in syms ),
                        vertical_spacing    = 0.01
                    )

    for i in range(n_syms):

        sym     = syms[i]
        trace   = render(sym, fig, i + 1)

    fig.update_layout(height = HEIGHT * n_syms)
    fig.show()

    print(f"{time() - t0:0.1f}s")