from typing import Any, Type
import numpy as np
import pandas as pd
EPS = 1e-8


# these functions are here just so they have a name...
def first(x):
    return x[0]


def last(x):
    return x[-1]


# https://stackoverflow.com/questions/30399534/shift-elements-in-a-numpy-array
# preallocate empty array and assign slice by chrisaycock
def fast_shift(arr, num, fill_value=np.nan):
    result = np.empty_like(arr)
    if num > 0:
        result[:num] = fill_value
        result[num:] = arr[:-num]
    elif num < 0:
        result[num:] = fill_value
        result[:num] = arr[-num:]
    else:
        result[:] = arr
    return result


def apply_func(data, func, *args, **kwargs):
    member_func = getattr(data, str(func), None) if not isinstance(data, list) else None
    return member_func(*args, **kwargs) if member_func is not None else func(data, *args, **kwargs)


def summarize(data, funcs, **kwargs):
    column_names = None
    if kwargs:
        if 'column_names' in kwargs.keys():
            column_names = [str(x) for x in kwargs['column_names']]
    if column_names is None:
        column_names = [x.__name__ for x in funcs]
    if not column_names or not funcs:
        raise ValueError(
            f'Number of functions ({len(funcs)}) must be >0 and match the number of function names {len(column_names)}')
    
    if len(data) < 1:
        summary_dict = dict([(key, [np.nan]) for key, func in zip(column_names, funcs)])
    else:
        # the functions are independent from each other so do not need to be executed in a loop!
        summary_dict = dict([(key, [apply_func(data, func)]) for key, func in zip(column_names, funcs)])
    
    return pd.DataFrame.from_dict(summary_dict)


def isclose(value1, value2):
    t = float
    return abs(t(value1) - t(value2)) < t(EPS)


def try_parse(to_type: Type, s: Any) -> Any:
    try:
        return to_type(s)
    except BaseException:
        return None


def percentage(value, digits=3) -> str:
    return "{0:.{digits}f}%".format(value * 100, digits=digits)


def array_shift(arr, shift):
    """
    Ugly implementation of array shift through pandas
    :param arr: array to shift
    :param shift: shift value
    :return: shifted array
    """
    return pd.DataFrame(arr).shift(shift).values
