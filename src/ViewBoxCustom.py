from PyQt5.QtCore import QEvent
from pyqtgraph import ViewBox, Point, fn
import numpy as np
from PyQt5 import QtCore


class ViewBoxCustom(ViewBox):

    def __init__(self,
                 parent=None,
                 border=None,
                 lockAspect=False,
                 enableMouse=True,
                 invertY=False,
                 enableMenu=True,
                 name=None,
                 invertX=False):
        super().__init__(parent=parent,
                         border=border,
                         lockAspect=lockAspect,
                         enableMouse=enableMouse,
                         invertY=invertY,
                         enableMenu=enableMenu,
                         name=name,
                         invertX=invertX)

    def wheelEvent(self, ev: QEvent, axis: int = None) -> None:
        """
        Adjust wheel event.

        Y wheel event (vertical zoom) should only work over Y-axis.
        X wheel event (horizontal zoom) should work on both axis and chart area.

        Parameters
        ----------
        ev: QEvent
        axis: int

        Returns
        -------
        None
        """
        mask = [False, False]
        if axis in (0, 1):
            mask[axis] = self.state['mouseEnabled'][axis]
        else:
            mask[0] = self.state['mouseEnabled'][0]
        s = 1.02 ** (ev.delta() * self.state['wheelScaleFactor'])
        s = [(None if m is False else s) for m in mask]
        center = Point(fn.invertQTransform(
            self.childGroup.transform()).map(ev.pos()))

        self._resetTarget()
        self.scaleBy(s, center)
        ev.accept()
        self.sigRangeChangedManually.emit(mask)

    def mouseDragEvent(self, ev: QEvent, axis=None) -> None:
        """
        Adjust drag event.

        Y drag event (vertical movement) should work only on Y-axis.
        X drag event (horizontal movement)
        should work on both axis and chart area.

        Parameters
        ----------
        ev: QEvent
        axis: int

        Returns
        -------
        None
        """
        # if axis is specified, event will only affect that axis.
        ev.accept()  # we accept all buttons

        pos = ev.pos()
        lastPos = ev.lastPos()
        dif = pos - lastPos
        dif = dif * -1

        # Ignore axes if mouse is disabled
        mouseEnabled = np.array(self.state['mouseEnabled'], dtype=np.float)
        mask = mouseEnabled.copy()
        if axis is None:
            mask = [1.0, 0.0]
        if axis is not None:
            mask[1 - axis] = 0.0

        # Scale or translate based on mouse button
        if ev.button() & (QtCore.Qt.LeftButton | QtCore.Qt.MidButton):
            if self.state['mouseMode'] == ViewBox.RectMode and axis is None:
                if ev.isFinish():
                    # This is the final move in the drag;
                    # change the view scale now
                    self.rbScaleBox.hide()
                    ax = QtCore.QRectF(Point(ev.buttonDownPos(ev.button())),
                                       Point(pos))
                    ax = self.childGroup.mapRectFromParent(ax)
                    self.showAxRect(ax)
                    self.axHistoryPointer += 1
                    self.axHistory = \
                        self.axHistory[:self.axHistoryPointer] + [ax]
                else:
                    # update shape of scale box
                    self.updateScaleBox(ev.buttonDownPos(), ev.pos())
            else:
                tr = self.childGroup.transform()
                tr = fn.invertQTransform(tr)
                tr = tr.map(dif * mask) - tr.map(Point(0, 0))

                x = tr.x() if mask[0] == 1 else None
                y = tr.y() if mask[1] == 1 else None

                self._resetTarget()
                if x is not None or y is not None:
                    self.translateBy(x=x, y=y)
                self.sigRangeChangedManually.emit(self.state['mouseEnabled'])
        elif ev.button() & QtCore.Qt.RightButton:
            # print "vb.rightDrag"
            if self.state['aspectLocked'] is not False:
                mask[0] = 0

            dif = ev.screenPos() - ev.lastScreenPos()
            dif = np.array([dif.x(), dif.y()])
            dif[0] *= -1
            s = ((mask * 0.02) + 1) ** dif

            tr = self.childGroup.transform()
            tr = fn.invertQTransform(tr)

            x = s[0] if mouseEnabled[0] == 1 else None
            y = s[1] if mouseEnabled[1] == 1 else None

            center = Point(tr.map(ev.buttonDownPos(QtCore.Qt.RightButton)))
            self._resetTarget()
            self.scaleBy(x=x, y=y, center=center)
            self.sigRangeChangedManually.emit(self.state['mouseEnabled'])
