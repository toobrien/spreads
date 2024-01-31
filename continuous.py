import  plotly.graph_objects    as      go
from    re                      import  compile
from    sys                     import  argv
from    typing                  import  List
from    util                    import  get_continuous, r


# python continuous.py RB:0:1 HO:0:-1
# python continuous.py HO:0:1 HO:3:-2 HO:6:1:1


def continuous_spread(
    symbols:        List[str],
    terms:          List[int],
    quantitites:    List[int],
    start:          str,
    end:            str
):

    series = [
        get_continuous(symbols[i], start, end, terms[i], "spread_adjusted")
        for i in range(len(symbols))
    ]

    dates = sorted(
                list(
                    set(
                        [ 
                            rec[r.date]
                            for recs in series 
                            for rec in recs
                        ]
                    )
                )
            )
    
    pass


if __name__ == "__main__":

    pattern = compile("\d{4}-\d{2}-\d{2}")
    dates   = [ date for date in argv if pattern.match(date) ]
    start   = dates[0] if dates else "1900-01-01"
    end     = dates[1] if len(dates) > 1 else "2100-01-01"
    dfns    = [ arg.split(":") for arg in argv if ":" in arg ]
    symbols = [ dfn[0] for dfn in dfns ]
    terms   = [ int(dfn[1]) for dfn in dfns ]
    qtys    = [ int(dfn[2]) for dfn in dfns ]
    spread  = continuous_spread(symbols, terms, qtys, start, end)