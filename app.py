from    json                    import  loads
import  plotly.graph_objects    as      go
from    plotly.subplots         import  make_subplots
from    sys                     import  argv
from    time                    import  time
from    typing                  import  List
from    util                    import  all, add_scatters, add_pdfs, BEGIN, by_season, \
                                        by_sequence, DB, END, get_legs, get_term_days, \
                                        get_spread_ids, print_spreads, spread, TERM_DAYS


PLOT_HEIGHT = 400

def render(
    symbol: str,
    mode:   str,
    width:  int,
    defs:   List,
    text:   bool
):

    if symbol not in TERM_DAYS:

        TERM_DAYS[symbol] = get_term_days(symbol)

    term_days           = TERM_DAYS[symbol]
    today               = term_days[-1]
    legs                = get_legs(mode, width)
    total_width         = legs[-1][0]
    todays_spread_ids   = get_spread_ids(today, legs, total_width)
    plots               = {}
    ret_plots           = []
    plot_count          = 0

    for d in defs:

        results     = None
        seasons     = None
        sequences   = None

        if d == "all_seq":

            sequences = {
                i for i in range(len(today) - total_width)
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

            results = by_season(term_days, legs, total_width, seasons)

        elif sequences:

            results = by_sequence(term_days, legs, total_width, sequences)
        
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

        # generate regression scatter

        for spread_def, data in results.items():

            ret_plots.append(
                (
                    spread_def,
                    [
                        ( recs[i][spread.settle], recs[i][spread.settle] - recs[i - 1][spread.settle] )
                        for _, recs in data.items()
                        for i in range(1, len(recs))
                    ]
                )
            )

    # generate figure

    if not text:
    
        fig = make_subplots(
                rows = plot_count, 
                cols = 3,
            )
        
        fig.update_layout(
            height  = PLOT_HEIGHT * plot_count,
            title   = f"{symbol} {mode}"
        )

        for i in range(plot_count):

            per_plot_spreads = plots[i]

            add_scatters(fig, i + 1, per_plot_spreads)
            add_pdfs(fig, i + 1, per_plot_spreads)

            fig.add_trace(
                go.Histogram(
                    {
                        "x": [ rec[1] for rec in ret_plots[i][1] ],
                        "name": "".join(ret_plots[i][0]) + " returns",
                        "marker": { "color": "blue" }
                    }
                ),
                row = i + 1,
                col = 3
            )

        fig.show()

    else:

        print_spreads(symbol, mode, plots)


if __name__ == "__main__":

    start   = time()

    text = False

    if "text" in argv:

        argv.remove("text")
        text = True

    if argv[1] == "watchlist":

        watchlist_name  = argv[2]
        watchlist       = loads(open("./watchlists.json", "r").read())

        for symbol, defs in watchlist[watchlist_name].items():

            for mode, defs in defs.items():

                mode_parts  = mode.split(":")
                mode        = mode_parts[0]
                width       = int(mode_parts[1])

                render(symbol, mode, width, defs, text)

    else:

        symbol      = argv[1]
        mode_parts  = argv[2].split(":")
        mode        = mode_parts[0]
        width       = int(mode_parts[1])
        defs        = argv[3:]

        render(symbol, mode, width, defs, text)

    print(f"elapsed: {time() - start:0.1f}")