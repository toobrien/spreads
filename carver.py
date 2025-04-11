from    json                    import  loads
import  numpy                   as      np
import  plotly.graph_objects    as      go
from    plotly.subplots         import  make_subplots
from    re                      import  compile
from    scipy.stats             import  kurtosis, skew
from    sys                     import  argv
from    typing                  import  List
from    util                    import  get_continuous, r


# python carver.py EMD:0:1 YM:0:-2
# python carver.py RB:0:1 HO:0:-1 
# python carver.py HO:0:1 HO:3:-2 HO:6:1


CONFIG = loads(open("./config.json").read())


def carver_continuous_spread(
    symbols:    List[str],
    terms:      List[int],
    quantities: List[int],
    start:      str,
    end:        str,
):

    multipliers =   [ CONFIG["multipliers"][sym] for sym in symbols ]
    ratios      =   np.array([ quantities[i] * multipliers[i] for i in range(len(quantities)) ])
    base        =   np.max(np.abs(ratios))
    mult        =   multipliers[int(np.where(np.abs(ratios) == base)[0][0])]
    ratios      /=  base

    series = [
        get_continuous(symbols[i], start, end, terms[i], "sum_adjusted")
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

            rec[i] = rec[i] * ratios[i - 1]
    
    spread = [
        [ rec[0], *rec[1:], sum(rec[1:]) ]
        for rec in spread
    ]

    return spread, mult


if __name__ == "__main__":

    pattern         = compile("\d{4}-\d{2}-\d{2}")
    dates           = [ date for date in argv if pattern.match(date) ]
    start           = dates[0] if dates else "1900-01-01"
    end             = dates[1] if len(dates) > 1 else "2100-01-01"
    dfns            = [ arg.split(":") for arg in argv if ":" in arg ]
    symbols         = [ dfn[0] for dfn in dfns ]
    terms           = [ int(dfn[1]) for dfn in dfns ]
    qtys            = [ float(dfn[2]) for dfn in dfns ]
    spread, mult    = carver_continuous_spread(symbols, terms, qtys, start, end)

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

    returns = np.diff(np.array([x[-1] for x in spread]))
    returns = [
                (spread[i][-1] - spread[i - 1][-1])
                for i in range(1, len(spread))
            ]
    
    mu      = np.mean(returns) * 256
    sigma   = np.std(returns) * 16
    kur     = kurtosis(returns) / 256
    ske     = skew(returns) / 16
    sharpe  = mu / sigma

    print(f"\n{'annualized':10}{'pts':>15}{'$':>10}\n")
    print(f"{'mu:':10}{mu:>15.4f}{mu * mult:>10.2f}")
    print(f"{'sigma:':10}{sigma:>15.4f}{sigma * mult:>10.2f}")
    print(f"{'kurtosis:':10}{kur:>15.4f}")
    print(f"{'skew:':10}{ske:>15.4f}")
    print(f"{'sharpe:':10}{sharpe:>15.4f}\n")

    fig.show()