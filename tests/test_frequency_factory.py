import pytest

from src.frequency import Frequency
from src.frequency_filter import (FilterFactory, GammaFilter, BetaFilter,
                                  AlphaFilter, ThetaFilter, DeltaFilter)


@pytest.mark.parametrize("test_input,expected,low,high", [
    (FilterFactory(Frequency.GAMMA), GammaFilter, 35, 70),
    (FilterFactory(Frequency.BETA), BetaFilter, 12, 35),
    (FilterFactory(Frequency.ALPHA), AlphaFilter, 8, 12),
    (FilterFactory(Frequency.THETA), ThetaFilter, 4, 8),
    (FilterFactory(Frequency.DELTA), DeltaFilter, 0.5, 4),
])
def test_filter_factory_gamma(test_input, expected, low, high):
    filter_object = test_input.get_filter(50)
    assert isinstance(filter_object, expected)
    assert filter_object.low == low
    assert filter_object.high == high
