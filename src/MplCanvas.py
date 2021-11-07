import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

plt.style.use('dark_background')


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=10, height=6, dpi=100):
        self.figure, self.axes = plt.subplots(nrows=2,
                                              ncols=2,
                                              figsize=(width, height),
                                              dpi=dpi,
                                              tight_layout=True)
        super(MplCanvas, self).__init__(self.figure)
