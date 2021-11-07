from typing import Tuple, Any, List, Optional


def hex2rgb(rgb: str, alpha: Optional[int] = 255) -> Tuple[int, int, int, int]:
    """
    Convert HTML colour notation to rgb notation.

    Parameters
    ----------
    rgb: str
        HTML representation of colour.
    alpha: int, optional
        Optional alpha channel value.

    Returns
    -------
    Tuple[int, int, int, int]
        Decimal values for red, green, blue and alpha.
    """
    rgb = rgb.lstrip('#')
    return tuple(int(rgb[i:i + 2], 16) for i in (0, 2, 4)) + tuple([alpha])


def extend_unique(list1: List[Any], list2: List[Any]) -> None:
    """
    Extend list with unique values of second lists.

    Parameters
    ----------
    list1: List[Any]
        List of values of any type.
    list2: List[Any]
        List of values of any type.

    Returns
    -------
    None
    """
    list1.extend([x for x in list2 if x not in list1])


def difference(list1: List[Any], list2: List[Any]) -> List:
    """
    Extend list with unique values of second lists.

    Parameters
    ----------
    list1: List[Any]
        List of values of any type.
    list2: List[Any]
        List of values of any type.

    Returns
    -------
    List
        The first list without elements from the second list.
    """
    return [x for x in list1 if x not in list2]
