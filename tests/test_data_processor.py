from feed_filter import TimeFreqFilter
from constants import TimePeriod
from data_processor import DataProcessor

from pprint import pprint as pp
from functools import partial
from datetime import datetime
import pandas as pd
import numpy as np

from faker import Faker

fake = Faker()


def duplicate_col(source_col_name, target_col_name, df):
    df[[target_col_name]] = df[[source_col_name]]
    return df


def shift_colname(column_name, num_shifts, df):
    lag_char = 'F' if num_shifts < 0 else 'L'
    new_column_name = f'{column_name}_{lag_char}{str(np.abs(num_shifts))}'
    df[new_column_name] = df[[column_name]].shift(num_shifts)
    return df


def rolling_mean(x, col_name, n):
    return pd.DataFrame(x[col_name].shift(1).rolling(window=n).mean(), index=x.index)


def test_data_processor():
    num_obs = 2000
    data = pd.DataFrame(np.random.randn(num_obs).tolist(), columns=["Return"], index=[fake.date_time_between_dates(
        datetime_start=datetime(2020, 3, 13, 14, 58, 57), datetime_end=datetime(2020, 3, 20, 14, 58, 57), tzinfo=None)
        for x in range(num_obs)])
    # pp(data.Return['2020-03-13 19:55:49.743080':'2020-03-15 13:00:00.866140'])
    
    z = DataProcessor(data)(TimeFreqFilter(TimePeriod.MINUTE, 15))(rolling_mean, col_name="Return", n=5).data
    # pp(z.Return['2020-03-13 19:55:49.743080':'2020-03-15 13:00:00.866140'])
    
    z2 = DataProcessor(data)(TimeFreqFilter(TimePeriod.HOUR, 1))("between_time", '08:30', '16:30')(
        lambda x: x.rename(columns={"Return": "RETURN"})).data
    # pp(z2.head(5))
    # pp(z2.tail(5))
    
    z3 = DataProcessor(data)("between_time", '15:59', '16:30')(TimeFreqFilter(TimePeriod.BUSINESS_DAY))(
        lambda x: x[x.Return > 0.0])
    # pp(z3.head(5))
    # pp(z3.tail(5))
    
    z2 = DataProcessor(data).time_freq(TimePeriod.HOUR, 1). \
        between_time('08:30', '16:30').data
    # pp(z2.Return['2020-03-13 19:55:49.743080':'2020-03-15 13:00:00.866140'])
    
    z2 = DataProcessor(data) \
        (partial(lambda x, y, z: z.loc[x:y], '2020-03-13 08:00', '2020-03-17 08:00')) \
        ("between_time", '08:15', '16:30') \
        (lambda x: x[x.Return > 0.0]) \
        [TimeFreqFilter(TimePeriod.MINUTE, 5, starting=datetime(2017, 6, 1, 8, 15, 0)),
         [DataProcessor.first, np.max, np.min, DataProcessor.last, np.median, np.mean, np.std], "Return"] \
        (lambda x: x.rename(columns={'amax': 'HIGH', 'amin': 'LOW', 'mean': 'MEAN',
                                     'median': 'MEDIAN', 'first': 'OPEN', 'last': 'CLOSE', 'std': 'STD'})).data

    # pp(z2['2020-03-13 12:00':'2020-03-16 13:00'])
    # pp(z2.head(5).HIGH - z2.head(5).LOW)
    # pp(z2.columns.values)
    
    z3 = DataProcessor(data).between_time('11:30', '14:00').shift_to_new_column("L1_LOG_RET", "Return", 1).data
    # pp(z3.tail(5))
    
    z3 = DataProcessor(data).between_time('08:01', '18:30').time_freq(TimePeriod.BUSINESS_DAY).positive_column(
        value_column="Return").data
    # pp(z3.tail(5))
    
    z3 = DataProcessor(data).index('2020-03-13 19:55:49.743080', '2020-03-15 13:00:00.866140'). \
        between_time('08:15', '16:30').positive_column(value_column="Return"). \
        summarize_intervals(TimeFreqFilter(TimePeriod.MINUTE, 5, starting=datetime(2020, 3, 13, 19, 0, 0)),
                            [DataProcessor.first, np.max, np.min, DataProcessor.last, np.median, np.mean, np.std],
                            "Return"). \
        rename_columns(['amax', 'amin', 'mean', 'median', 'first', 'last', 'std'],
                       ['HIGH', 'LOW', 'MEAN', 'MEDIAN', 'OPEN', 'CLOSE', 'STD']).data
    
    # pp(z3.HIGH - z3.LOW)
    # pp(z3.tail(5))
    
    z2 = DataProcessor(data).index('2020-03-13 19:55', '2020-03-15 13:00'). \
        between_time('08:15', '16:30').positive_column(value_column="Return"). \
        summarize_intervals(TimeFreqFilter(TimePeriod.MINUTE, 30, starting=datetime(2020, 3, 14, 8, 0, 0)),
                            [DataProcessor.first, np.max, np.min, DataProcessor.last, np.median, np.mean, np.std],
                            "Return"). \
        rename_columns(['amax', 'amin', 'mean', 'median', 'first', 'last', 'std'],
                       ['HIGH', 'LOW', 'MEAN', 'MEDIAN', 'OPEN', 'CLOSE', 'STD'])(lambda x: x[~np.isnan(x.STD)]).data
    # pp(z2.tail(5))

    z2 = DataProcessor(data) \
        (partial(lambda x, y, z: z.loc[x:y], '2020-03-13 19:55', '2020-03-15 13:00')) \
        ("between_time", '08:15', '16:30') \
        (lambda x: x[x.Return > 0.0]) \
        [TimeFreqFilter(TimePeriod.MINUTE, 30, starting=datetime(2020, 3, 14, 8, 0, 0)),
         [DataProcessor.first, np.max, np.min, DataProcessor.last, np.median, np.mean, np.std], "Return"] \
        (lambda x: x.rename(columns={'amax': 'HIGH', 'amin': 'LOW', 'mean': 'MEAN',
                                     'median': 'MEDIAN', 'first': 'OPEN', 'last': 'CLOSE', 'std': 'STD'})) \
        (partial(duplicate_col, "MEAN", "LogReturn_MEAN")) \
        (partial(duplicate_col, "STD", "LogReturn_STD")) \
        (partial(shift_colname, 'LogReturn_MEAN', -1)) \
        (partial(shift_colname, 'LogReturn_STD', -1)) \
        (lambda x: x[~np.isnan(x.LogReturn_STD) & ~np.isnan(x.STD) & ~np.isnan(x.LogReturn_STD_F1)]).data

    # pp(z2.columns.values)
    # pp(z2.head(10))

