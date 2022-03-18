from    plotly.subplots import  make_subplots
from    sys             import  argv
from    time            import  time
from    typing          import  List
from    util            import  add_scatters, add_pdfs, by_season, by_sequence, get_db, \
                                get_legs, get_term_days, get_spread_ids


PLOT_HEIGHT = 400
BEGIN       = "2000-01-01"
END         = "2050-01-01"


def main(symbol: str, mode: str, defs: List):

    db                  = get_db()
    term_days           = get_term_days(db, symbol, BEGIN, END)
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

    symbol  = argv[1]
    mode    = argv[2]
    defs    = argv[3:] 

    main(symbol, mode, defs)

    print(f"elapsed: {time() - start:0.1f}")