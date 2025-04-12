from    numpy                   import  absolute, arange, array, mean, std
import  plotly.graph_objects    as      go
from    plotly.subplots         import  make_subplots
from    re                      import  compile
from    scipy.stats             import  kurtosis, skew
from    sklearn.linear_model    import  LinearRegression
from    sys                     import  argv
from    typing                  import  List
from    util                    import  get_continuous, r


# python continuous.py RB:0:1 HO:0:-1 log
# python continuous.py HO:0:1 HO:3:-2 HO:6:1:1 nearest
# python continuous.py ZM:0:1 ZM:1:-1 reg 50


def continuous_spread(
    symbols:    List[str],
    terms:      List[int],
    quantities: List[int],
    start:      str,
    end:        str,
    mode:       str     = "prod_adjusted",
    logs:       bool    = False
):

    series = [
        get_continuous(symbols[i], start, end, terms[i], mode, logs)
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
        [ rec[0], *rec[1:], sum(rec[1:]) ]
        for rec in spread
    ]

    return spread


if __name__ == "__main__":


    log     = "log" in argv
    reg     = "reg" in argv
    mode    = "nearest" if "nearest" in argv else "sum_adjusted" if "sum_adjusted" in argv else "prod_adjusted"
    pattern = compile(r"\d{4}-\d{2}-\d{2}")
    dates   = [ date for date in argv if pattern.match(date) ]
    start   = dates[0] if dates else "1900-01-01"
    end     = dates[1] if len(dates) > 1 else "2100-01-01"
    dfns    = [ arg.split(":") for arg in argv if ":" in arg ]
    symbols = [ dfn[0] for dfn in dfns ]
    terms   = [ int(dfn[1]) for dfn in dfns ]
    qtys    = [ float(dfn[2]) for dfn in dfns ]
    spread  = continuous_spread(symbols, terms, qtys, start, end, mode, log)

    fig = make_subplots(2, 1)

    x = [ rec[0] for rec in spread ]

    fig.add_trace(
        go.Scatter(
            {
                "x":    x,
                "y":    [ rec[-1] for rec in spread ],
                "name": "spread"
            }
        ),
        row = 1,
        col = 1
    )

    for i in range(len(symbols)):

        symbol = symbols[i]

        fig.add_trace(
            go.Scatter(
                {
                    "x":    x,
                    "y":    [ rec[i + 1] / qtys[i] for rec in spread ],
                    "name": f"{symbol}[{terms[i]}]"
                }
            ),
            row = 2,
            col = 1
        )

    x       = x[1:]
    gross   = [ sum(absolute(rec[1:-1]))for rec in spread ]
    returns = [
                (spread[i][-1] - spread[i - 1][-1]) / gross[i - 1]
                for i in range(1, len(spread))
            ]
    
    mu      = mean(returns)
    sigma   = std(returns)
    kur     = kurtosis(returns)
    ske     = skew(returns)
    sharpe  = mu / sigma * 16

    print("\narithmetic, annual\n")
    print(f"{'mu:':10}{mu * 256:<10.4f}")
    print(f"{'sigma:':10}{sigma * 16:<10.4f}")
    print(f"{'kurtosis:':10}{kur / 256:<10.4f}")
    print(f"{'skew:':10}{ske / 16:<10.4f}")
    print(f"{'sharpe:':10}{sharpe:<10.4f}\n")

    fig.show()

    if reg:

        # regress spread change, expressed as arithmetic return on front month, on front month return

        fig     = make_subplots(rows = 2, cols = 1, vertical_spacing = 0.025)
        reg_len = int(argv[argv.index("reg") + 1])
        spread  = spread[-reg_len:]
        m0      = [ abs(rec[1]) for rec in spread ]
        s_ret   = [ 
                    (m0[i - 1] + spread[i][-1] - spread[i - 1][-1]) / m0[i - 1] - 1 
                    for i in range(1, len(spread)) 
                ]
        m0_ret  = [ m0[i] / m0[i - 1] - 1 for i in range(1, len(spread)) ]
        model   = LinearRegression()

        model.fit(array(m0_ret).reshape(-1, 1), s_ret)

        x_mod   = arange(min(m0_ret), max(m0_ret), step = 0.0001)
        y_mod   = model.predict(array(x_mod).reshape(-1, 1))
        beta    = model.coef_[0]
        alpha   = model.intercept_

        text    = x[-reg_len + 1:]

        traces  = [
            ( "reg", m0_ret, s_ret, "markers", text ),
            ( "model", x_mod, y_mod, "lines", None )
        ]

        for trace in traces:

            fig.add_trace(
                go.Scattergl(
                    {
                        "name": trace[0],
                        "x":    trace[1],
                        "y":    trace[2],
                        "mode": trace[3],
                        "text": trace[4]
                    }
                ),
                row = 1, 
                col = 1
            )

        traces = [
            ( "m0_ret", m0_ret, "#FF0000" ),
            ( "s_ret", s_ret, "#0000FF" )
        ]

        for trace in traces:

            fig.add_trace(
                go.Bar(
                    {
                        "name":         trace[0],
                        "y":            trace[1],
                        "marker":       { 'color': trace[2] },
                        "hovertext":    text
                    }
                ),
                row = 2, 
                col = 1
            )

        print(f"{'alpha':10}{alpha:<10.04f}")
        print(f"{'beta':10}{beta:<10.04f}")
        print(f"{'r^2':10}{beta**2:<10.04f}\n")

        fig.show()