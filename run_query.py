import pandas as pd
from index import datetimeToIndex, dayToIndexRatio
from datetime_modifications import correct_datetime, getIndexList, getDateList, joinDict

def get_pressure(cursor, site_id):
    indexList = getIndexList()
    dateList = getDateList(indexList)

    sql_query = "SELECT *, MAX(batch_id) FROM (hobo_pressure_logs_1 INNER JOIN hobo_pressure_batches_1 USING(batch_id)) WHERE site_id = ? GROUP BY logging_date, logging_time;"
    site_tuple = (site_id,)
    cursor.execute(sql_query, site_tuple)
    result = cursor.fetchall()
    pressure_data = {
        "index": indexList,
        "datetime": dateList
    }
    pressure_dict = {"batch_id": [], "datetime": [], "pressure_hobo": [], "index": []}

    for item in result:
        batch_id = item[4]
        date = item[0]
        time = item[1]
        pressure = item[2]
        date = date.split(" ")[0]
        datetime = date + " " + time

        year, month, day, hour, minute, second = correct_datetime(datetime)

        datetime = day + "/" + month + "/" + year + " " + hour + ":" + minute + ":" + second

        index = datetimeToIndex(year, month, day, hour, minute, second)
        index = round(index / dayToIndexRatio) * dayToIndexRatio

        pressure_dict["batch_id"].append(batch_id)
        pressure_dict["datetime"].append(datetime)
        pressure_dict["pressure_hobo"].append(pressure)
        pressure_dict["index"].append(index)


    # pressure_data = joinDict(pressure_dict, pressure_data)
    # pressure_data = pd.DataFrame.from_dict(pressure_data)
    #pressure_data = pd.to_datetime(pressure_data.datetime)

    pressure_data = pd.DataFrame(pressure_dict)
    pressure_data['datetime'] = pd.to_datetime(pressure_data.datetime, format="%d/%m/%y %H:%M:%S")
    pressure_data = pressure_data.sort_values(by=['datetime'])
    return pressure_data


def get_discharge(cursor, site_id):
    indexList = getIndexList()
    dateList = getDateList(indexList)

    sql_query = "SELECT *, MAX(q_batch_id) FROM q_reads INNER JOIN q_batches USING (q_batch_id) where site_id = ? group by date_sampled, time_sampled order by (date_sampled);"
    site_tuple = (site_id,)
    cursor.execute(sql_query, site_tuple)
    result = cursor.fetchall()
    discharge_data = {
        'index': indexList,
        'datetime': dateList
    }
    discharge_dict = {
        "batch_id": [],
        "datetime": [],
        "discharge_measured": [],
        "index": []
    }

    for item in result:
        batch_id = item[0]
        date = item[2]
        time = item[3]
        date = date.split(" ")[0]
        datetime = date + " " + time
        discharge = item[4]

        year, month, day, hour, minute, second = correct_datetime(datetime)

        datetime = day + "/" + month + "/" + year + " " + hour + ":" + minute + ":" + second

        index = datetimeToIndex(year, month, day, hour, minute, second)
        index = round(index / dayToIndexRatio) * dayToIndexRatio

        discharge_dict["batch_id"].append(batch_id)
        discharge_dict["datetime"].append(datetime)
        discharge_dict["discharge_measured"].append(discharge)
        discharge_dict["index"].append(index)


    discharge_data = pd.DataFrame(discharge_dict)
    discharge_data['datetime'] = pd.to_datetime(discharge_data.datetime, format="%d/%m/%y %H:%M:%S")
    discharge_data = discharge_data.sort_values(by=['datetime'])

    return discharge_data
