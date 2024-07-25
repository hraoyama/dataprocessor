from dataprocessor.utils import apply_func, summarize
from dataprocessor.feed_filter import TimeFreqFilter, FilterInterface
from functools import partial

import pandas as pd
import functools


class DataProcessor(object):
    RETURN_INDEX = 'ret'
    ADV_INDEX = 'adv'
    
    def __init__(self, *args):
        if isinstance(args[0], pd.DataFrame):
            self._data = args[0].sort_index()
        else:
            raise ValueError(f'Unable to interpret DataProcessor arguments: {str(args)}')
        pass
    
    def __getattr__(self, item):
        return getattr(self._data, item, None)
    
    def __call__(self, func, *args, **kwargs):
        if isinstance(func, FilterInterface):
            return DataProcessor(self._data.loc[func.apply(self._data)])
        else:
            ret_value = apply_func(self._data, func, *args, **kwargs)
            if not isinstance(ret_value, type(self._data)):
                raise TypeError(
                    f'Call to DataProcessor should return type {type(self._data)} but returned {type(ret_value)}')
            return DataProcessor(ret_value)
    
    def __getitem__(self, tuple_of_arguments):
        filter_applied = tuple_of_arguments[0]
        funcs = tuple_of_arguments[1]
        
        old_return_fixed_indices = filter_applied.return_fixed_indices
        filter_applied.return_fixed_indices = True
        indices_that_exist, fixed_indices = filter_applied.apply(self._data)
        filter_applied.return_fixed_indices = old_return_fixed_indices
        
        column_names = tuple_of_arguments[2] if len(tuple_of_arguments) > 2 else None
        if column_names is None:
            column_names = list(self._data.columns.values)
        
        summaries = [summarize(self._data.loc[x[0]:x[1]][column_names], funcs) for
                     x in zip(fixed_indices[:-1], fixed_indices[1:])]
        
        summary = functools.reduce(lambda df1, df2: pd.concat([df1, df2], ignore_index=False), summaries)
        summary["End_Period"] = fixed_indices[:-1]
        summary["Start_Period"] = fixed_indices[1:]
        
        summary.set_index('Start_Period', inplace=True)
        
        if not isinstance(summary, type(self._data)):
            raise TypeError(
                f'Interval Call to DataProcessor should return type {type(self._data)} but returned {type(summary)}')
        
        # if one wishes to rename the column names that can be done through another __call__
        return DataProcessor(summary)
    
    @property
    def data(self):
        return self._data.copy()
    
    @staticmethod
    def _shift(new_column_name, source_column_name, shift_count, df):
        df[[new_column_name]] = df[[source_column_name]].shift(shift_count)
        return df
    
    @staticmethod
    def first(x):
        return x.iloc[0]
    
    @staticmethod
    def last(x):
        return x.iloc[-1]
    
    # this group of functions are nothing more than convenience functions!!
    # I know, breaks the single interface principle...
    def summarize_intervals(self, time_freq_filter, funcs_list, column_name):
        return self.__getitem__((time_freq_filter, funcs_list, column_name))
    
    def time_freq(self, *args, **kwargs):
        return self.__call__(TimeFreqFilter(*args, **kwargs))
    
    def between_time(self, start_time, end_time):
        return self.__call__("between_time", start_time, end_time)
    
    def filter_on_column(self, func, column_name):
        return self.__call__(partial(func, column_name))
    
    def positive_column(self, value_column="Value"):
        return self.filter_on_column(lambda cn, d: d[d[cn] > 0.0], value_column)
    
    def index(self, start_index, end_index):
        return self.__call__(partial(lambda x, y, z: z.loc[x:y], start_index, end_index))
    
    def rename_columns(self, old_names_list, new_names_list):
        return self.__call__(lambda x: x.rename(columns=dict(zip(old_names_list, new_names_list))))
    
    def shift_to_new_column(self, new_column_name, source_column_name, shift_count):
        return self.__call__(partial(DataProcessor._shift, new_column_name, source_column_name, shift_count))
