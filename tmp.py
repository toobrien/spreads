import  plotly.graph_objects    as go
from    polars                  import col
from    sys                     import argv, path

path.append("..")

from    data.cat_df             import get_futc


# python [ date | dte ] KT:H:2025 KT:H:2026


if __name__ == "__main__":

    mode    = argv[1]
    futcs   = {}
    cons    = {}
    con_ids = [ tuple(arg.split(":")) for arg in argv[2:] ]
    fig     = go.Figure()

    for con_id in con_ids:

        sym = con_id[0]

        if sym not in futcs:

            futcs[sym] = get_futc(sym)

        cons[con_id] = futcs[sym].filter(
                            (col("name")     == sym) &
                            (col("month")    == con_id[1]) &
                            (col("year")     == con_id[2])
                        )
        
        con = cons[con_id]

        fig.add_trace(
            go.Scattergl(
                {
                    "x":    con["date"] if mode == "date" else con["dte"],
                    "y":    con["settle"],
                    "name": "".join(con_id)
                }
            )
        )

    fig.show()