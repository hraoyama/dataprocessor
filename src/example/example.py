import pandas as pd
import numpy as np
from datetime import datetime
from functools import partial
from dataprocessor.feed_filter import TimeFreqFilter
from dataprocessor.constants import TimePeriod
from dataprocessor.data_processor import DataProcessor
from faker import Faker

def main():
    fake = Faker()
    num_obs = 20000
    data = pd.DataFrame(np.random.randn(num_obs * 2).reshape(num_obs, 2), columns=["Return", "Px"],
                        index=[fake.date_time_between_dates(
                            datetime_start=datetime(2020, 3, 13, 14, 58, 57),
                            datetime_end=datetime(2020, 3, 20, 14, 58, 57),
                            tzinfo=None)
                            for x in range(num_obs)]).sort_index()
    data.Px = np.abs(data.Px) + 10.0
    z2 = DataProcessor(data)[
        TimeFreqFilter(TimePeriod.MINUTE, 5, starting=datetime(2020, 3, 15, 8, 15, 0)),
        [DataProcessor.first, np.max, np.min, DataProcessor.last, np.median, np.mean, np.std],
        "Return"](
        lambda x: x.rename(columns={'amax': 'HIGH', 'amin': 'LOW', 'mean': 'MEAN',
                                    'median': 'MEDIAN', 'first': 'OPEN',
                                    'last': 'CLOSE', 'std': 'STD'}))(
        lambda x: x[~np.isnan(x.MEAN)]).data
    print(z2.describe())
    pass

if __name__ == "__main__":
    main()