from src.helpers import hex2rgb


def test_hex2rgb():
    assert hex2rgb('#ff00ff') == tuple([255, 0, 255, 255])
    assert hex2rgb('#ff0000', 1) == tuple([255, 0, 0, 1])
