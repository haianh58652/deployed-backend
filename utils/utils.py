from datetime import datetime, timedelta

def get_n_nearest_workdays(reference_date=None, n=1):
    if n <= 0:
        raise ValueError("n phải là số nguyên dương")
    if reference_date is None:
        reference_date = datetime.now()

    reference_date = reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
    workdays = []
    current_date = reference_date
    count = 1
    while len(workdays) < n and count <= 30:
        if current_date.weekday() < 5:
            workdays.append(current_date.strftime('%d/%m/%Y'))
        current_date = current_date - timedelta(days=1)
        count += 1
    return workdays

def generate_intervals(n):
    current_date = datetime.now()
    intervals = []
    
    for i in range(n):
        end_date = current_date - timedelta(days=i*30)
        start_date = end_date - timedelta(days=29)
        interval = [start_date.strftime('%d/%m/%Y'), end_date.strftime('%d/%m/%Y')]
        intervals.insert(0, interval)
    
    return intervals

def ratioChange(start, end):
    ratio = (end - start) / start * 100
    return round(ratio, 2)

def convertTradingTimeTotimestamp(tradingDate, time):
    day, month, year = tradingDate.split("/")
    hour, minute, second = time.split(":")
    dt = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
    return dt.timestamp()

def convertTradingTimeToString(tradingDate, time):
    day, month, year = tradingDate.split("/")
    hour, minute, second = time.split(":")
    return f"{year}-{month}-{day} {hour}:{minute}:{second}"