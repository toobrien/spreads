from    json            import  loads
from    plotly.subplots import  make_subplots
from    sys             import  argv
from    time            import  time
from    typing          import  List
from    util            import  all, add_scatters, add_pdfs, by_season, by_sequence, \
                                get_db, get_legs, get_term_days, get_spread_ids


PLOT_HEIGHT = 400
BEGIN       = "1900-01-01"
END         = "2050-01-01"
TERM_DAYS   = {}
DB          = get_db()

def render(symbol: str, mode: str, defs: List):

    if symbol not in TERM_DAYS:

        TERM_DAYS[symbol] = get_term_days(DB, symbol, BEGIN, END)

    term_days           = TERM_DAYS[symbol]
    legs                = get_legs(mode)
    today               = term_days[-1]
    todays_spread_ids   = get_spread_ids(today, legs)
    plots               = {}
    plot_count          = 0

    for d in defs:

        results     = None
        seasons     = None
        sequences   = None

        if d == "all_seq":

            sequences = {
                i for i in range(len(today) - len(legs))
            }

        elif d == "all_sea":

            seasons = {
                tuple(
                    t[0] 
                    for t in spread_id
                )
                for spread_id in todays_spread_ids
            }

        elif d.isnumeric():

            sequences = { int(d) }

        elif len(d) == len(legs):

            seasons = {
                tuple( month for month in d )
            }

        if seasons:

            results = by_season(term_days, legs, seasons)

        elif sequences:

            results = by_sequence(term_days, legs, sequences)
        
        elif ":" in d:

            parts       = d.split("_")
            min_max_dte = parts[1].split(":")

            results = all(
                term_days,
                legs,
                int(min_max_dte[0]),
                int(min_max_dte[1])
            )

        for _, data in results.items():

            if data:
            
                plots[plot_count]   =   data
                plot_count          +=  1

    # generate figure

    fig = make_subplots(
            rows = plot_count, 
            cols = 2,
        )
    
    fig.update_layout(
        height  = PLOT_HEIGHT * plot_count,
        title   = f"{symbol} {mode}"
    )

    for i in range(plot_count):

        per_plot_spreads = plots[i]

        add_scatters(fig, i + 1, per_plot_spreads)
        add_pdfs(fig, i + 1, per_plot_spreads)

    fig.show()


if __name__ == "__main__":

    start   = time()

    if argv[1] == "watchlist":

        watchlist = loads(open("./watchlist.json", "r").read())

        for symbol, defs in watchlist.items():

            for mode, defs in defs.items():

                render(symbol, mode, defs)

    else:

        symbol  = argv[1]
        mode    = argv[2]
        defs    = argv[3:] 

        render(symbol, mode, defs)

    print(f"elapsed: {time() - start:0.1f}")