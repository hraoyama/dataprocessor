# dataprocessor

## Introduction

_dataprocessor_ extends the piping abilities for a pandas `DataFrame` when the index is a `DateTimeIndex`[^1] by wrapping it in a `DataProcessor` class. In order to retrieve the piping result, we access the `data` member on the `DataProcessor` instance. 
Operations on the dataframe are chained using `()` and/or `[]` operators, each with a different meaning. Arguments to `()` will operate on the entire data frame, arguments to `[]` will seek to summarize the data by distinct, non-overlapping blocks of time[^2]. 

The argument to the `()` operator can be either:
* A function taking the data frame as its argument and returning a new data frame[^3]
   The function can be any function including:
    - lambdas
    - user defined functions 
    - member functions[^4]
* An instance of a class derived from `FilterInterface` which implements an `apply` function returning a subset on the index of the data frame[^5]

In the case of the latter, the library provides a `TimeFreqFilter` with necessary implementation details[^6] as a convenience. 
For the former, the nature of the functions is usually to extract, filter, summarize, transform, etc. but any functionality is allowed provided the function returns a pandas `DataFrame`[^7].

The `[]` operator takes 3 arguments
* `TimeFreqFilter` indicating the interval length to summarize over
* `list` of functions to apply within each interval on a column of the data frame 
* the column in the data frame to apply the functions to

## Installation

_dataprocessor_ was built using python `3.9`. It is available as a [package on pypi](https://pypi.org/project/dataprocessor/) and can be installed through pip:

```
pip install dataprocessor
```
Should you require an installation of pip, follow the instructions on the [pip website](https://pip.pypa.io/en/stable/installation/).


## Examples

The easiest way to understand is to dive in with a series of examples.
First let us set up an example DataFrame with the [Faker](https://faker.readthedocs.io/en/master/) library:

```python
import pandas as pd
import numpy as np
from datetime import datetime
from functools import partial
from dataprocessor.feed_filter import TimeFreqFilter
from dataprocessor.constants import TimePeriod
from dataprocessor.data_processor import DataProcessor
from faker import Faker

fake = Faker()

num_obs = 20000
data = pd.DataFrame(np.random.randn(num_obs*2).reshape(num_obs,2), columns=["Return","Px"], index=[fake.date_time_between_dates(
    datetime_start=datetime(2020, 3, 13, 14, 58, 57), 
    datetime_end=datetime(2020, 3, 20, 14, 58, 57), 
    tzinfo=None)
    for x in range(num_obs)]).sort_index()
data.Px = np.abs(data.Px)+10.0
```

Assume we have a rolling mean function, but now we wish to apply it to the last observations of a column right before 15 minute intervals:   
```python
def rolling_mean(x, col_name, n):
    return pd.DataFrame(x[col_name].shift(1).rolling(window=n).mean(), index=x.index)

z = DataProcessor(data)(TimeFreqFilter(TimePeriod.MINUTE, 15))(rolling_mean, col_name="Return", n=5).data
# pp(z.Return['2020-03-13 19:55:49.743080':'2020-03-15 13:00:00.866140'])
```
Get the observations between 8:30 AM and 4:30 PM at every hour and rename a column 
```python
z2 = DataProcessor(data)("between_time", '08:30', '16:30')(TimeFreqFilter(TimePeriod.HOUR, 1))(
    lambda x: x.rename(columns={"Return": "RETURN"})).data
```
On all business days get the difference in price from 15:59 to 16:30.
```python
z3 = DataProcessor(data)("between_time", '15:59', '16:30')(TimeFreqFilter(TimePeriod.BUSINESS_DAY))(
    lambda x: x.iloc[-1,x.columns.get_loc("Px")]-x.iloc[0,x.columns.get_loc("Px")])
```
As an illustration, here are some methods of filtering between two times: 
```python
z2 = DataProcessor(data). \
    between_time('08:30', '16:30'). \
    ("between_time", '09:15', '15:30'). \
    (partial(lambda x, y, z: z.loc[x:y], '2020-03-13 08:00', '2020-03-17 08:00')).data
```
Next, starting at 8:15 AM on 15 Mar 2020, we take summary data for 5 minute intervals consisting of first, max, min, last, median, mean and standard deviation of the Return column. We then rename the columns and keep the intervals with observations.
```python
z2 = DataProcessor(data) \
    [TimeFreqFilter(TimePeriod.MINUTE, 5, starting=datetime(2020, 3, 15, 8, 15, 0)),
     [DataProcessor.first, np.max, np.min, DataProcessor.last, np.median, np.mean, np.std], "Return"] \
    (lambda x: x.rename(columns={'amax': 'HIGH', 'amin': 'LOW', 'mean': 'MEAN',
                                 'median': 'MEDIAN', 'first': 'OPEN', 'last': 'CLOSE', 'std': 'STD'}))(lambda x: x[~np.isnan(x.MEAN)]).data
```

[^1]: Even though the library focuses on a DateTimeIndex, there is nothing stopping users from using the functionality on pandas DataFrames with different indices; including providing their own classes as filters provided they implement an `apply` method.

[^2]: The convenience member function `summarize_intervals` as syntactic sugar for a call to `[]`

[^3]: The returned data frame will then be the input of any subsequent chaining

[^4]: A member function of the pandas DataFrame can be called by specifying it as a string in order to distinguish it from other functions in the local or global namespace

[^5]: The input frame of any subsequent chaining will be the subset matching the returned indices

[^6]: Such as starting index, whether the indices returned should be the ones right before/after the time intervals or both, etc.

[^7]: The `DataProcessor` provides convenience functions for some commonly used operations, but all are syntactic devices.


License
----

MIT

