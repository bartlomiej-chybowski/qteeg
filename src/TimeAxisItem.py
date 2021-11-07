import pyqtgraph as pg
import pandas as pd


class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [pd.Timestamp(value).to_pydatetime(warn=False)
                for value in values]
