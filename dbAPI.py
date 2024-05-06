import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import pickle
from datetime import datetime, timedelta

"""
This interaction will be exclusive to learning hebrew frequency list.
"""
my_database = "my_database.db"
hebrew_list_table = 'hebrew_list'
study_progress_table = 'study_progress'
date_string_col_name = "DATE_STR"
new_material_col_name = "NEW_MATERIAL"  # this column records what new materials are studied today
recited_material_col_name = "RECITED_MATERIALS"  # this column records which materials are recited today
being_recited_on_date_col_name = "BEING_RECITED"  # this column records on which dates was new_material_today recited


#######################################################################################################################
#######################################################################################################################
############################################ Table: hebrew_list #######################################################
#######################################################################################################################
#######################################################################################################################

def _download_hebrew_list_to_db():
    """
    This function get a 10000 Hebrew frequency list from the internet.
    :return:
    """
    url = 'https://www.teachmehebrew.com/hebrew-frequency-list.html'
    response = requests.get(url)

    db_conn = sqlite3.connect("my_database.db")
    db_table_name = "hebrew_list"
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table', {'id': 'words'})
        for table in tables:
            table_rows = table.find_all('tr')
            csv_rows_list = []
            for row in table_rows:
                cells = row.find_all(['th', 'td'])
                csv_row = [cell.get_text(strip=True) for cell in cells]
                csv_rows_list.append(csv_row)
            df = pd.DataFrame(csv_rows_list[1:], columns=csv_rows_list[0])
            df['Hebrew'] = df['Hebrew'].replace("", None).ffill()
            df['Rank'] = df['Rank'].replace("", None).ffill()
            df['Rank'] = pd.to_numeric(df['Rank'], errors='coerce')
            df.to_sql(db_table_name, db_conn, index=False, if_exists="append")
    db_conn.close()


def get_vocabs(begin_rank, end_rank):
    """
    Begin and end rank are inclusive
    :param begin_rank:
    :param end_rank:
    :return:
    """
    conn = sqlite3.connect(my_database)
    query = f"SELECT * FROM {hebrew_list_table} WHERE rank BETWEEN ? AND ?"
    df = pd.read_sql_query(query, conn, params=(begin_rank, end_rank))
    conn.close()
    return df


#######################################################################################################################
#######################################################################################################################
############################################ Table: study_progress ####################################################
#######################################################################################################################
#######################################################################################################################

def _initialize_tables():
    """
    Note "DATE" is a keyword in sqlite3....
    :return:
    """
    conn = sqlite3.connect(my_database)
    conn.cursor().execute(f"""
        CREATE TABLE IF NOT EXISTS {study_progress_table}(
            {date_string_col_name} TEXT PRIMARY KEY,
            {new_material_col_name} BLOB,
            {recited_material_col_name} BLOB,
            {being_recited_on_date_col_name} BLOB
        )
    """)
    # commit the change
    conn.commit()
    conn.close()


def _clear_table(table_name):
    """
    Note "DATE" is a keyword in sqlite3....
    :return:
    """
    conn = sqlite3.connect(my_database)
    conn.cursor().execute(f"""DROP TABLE {table_name};""")
    _initialize_tables()
    # commit the change
    conn.commit()
    conn.close()


def update_study_progress(date_str, new_material=None, recited_material=None, being_recited_on_date=None,
                          override=False):
    """
    The problem here is that should I map study progress to date, or date to study progress?
    If I map date to study progress, I would know what to review each day.
    If I map study progress to date, for each study progress I would be able to assess how well is it studied.
    Also, what's the precision of time? to hours? to minutes? first do until day. If later we want to include a
    Ebbinghaus we can create another table.
    Note: for inserting binary BLOB into table, must use ? with parameters, not f-string, else it would be syntax error
    Note: also for queries, must use ? instead of f-strings....
    Note: sql date time only understand %Y-%m-%d format
    Conclusion is: map date to progress is essential. First realize this.
    Map progress to date is also essential, but each progress's identifier will be its date, so it can be in the same
    table.
    :param date_time: should be a datetime object that is obtained by e.g. datetime.now().
    :param new_material: should be a list [begin_rank, end_rank], if nothing is studied, then empty list [],
            if a new new_material is provided (from a second call of this function), it will append to the old one
            according to _rules_for_adding_new_material()
    :param recited_material: should be a set {date_str_1, date_str_2, },
            if a new recited_material is provided (from a second call of this function), it will append to the old one
    :param being_recited_on_date: should be a set {date_str}
    :param override: If True, then we will take the given value as new value, if not provide new value, then it will
    not change the old value.
    :return:
    """
    # connect to db
    conn = sqlite3.connect(my_database)
    cursor = conn.cursor()
    # check if the date already exist in the table
    query = f'SELECT * FROM {study_progress_table} WHERE {date_string_col_name} = ?'
    cursor.execute(query, (date_str,))
    existing_row = cursor.fetchone()
    if not existing_row:  # insert the new row
        # parameter check: regardless override or not
        if new_material is None:
            new_material = []
        if recited_material is None:
            recited_material = set()
        if being_recited_on_date is None:
            being_recited_on_date = set()
        # convert dictionary to BLOB
        row_values = _serialized_rows(date_str, new_material, recited_material, being_recited_on_date)
        # insert the new row
        query = f'''INSERT INTO {study_progress_table} 
                    VALUES (?, ?, ?, ?);'''
        cursor.execute(query, row_values)
    else:  # update the row according to some rules
        # deserialize the information
        date_str, exist_new_material, exist_recited_material, exist_being_recited_on_date = _deserialize_rows_sqlite(
            existing_row)
        new_material, recited_material, being_recited_on_date = _rules_for_updating_tables(new_material,
                                                                                           exist_new_material,
                                                                                           recited_material,
                                                                                           exist_recited_material,
                                                                                           being_recited_on_date,
                                                                                           exist_being_recited_on_date,
                                                                                           override)
        # serialize: convert to BLOB
        date_str, new_material_BLOB, recited_material_BLOB, being_recited_on_date_BLOB = _serialized_rows(date_str,
                                                                                                          new_material,
                                                                                                          recited_material,
                                                                                                          being_recited_on_date)
        # update table
        query = f'''UPDATE {study_progress_table}
                    SET {new_material_col_name} = ?, {recited_material_col_name} = ?, {being_recited_on_date_col_name} = ?
                    WHERE {date_string_col_name} = ?;'''
        cursor.execute(query, (new_material_BLOB, recited_material_BLOB, being_recited_on_date_BLOB, date_str))
    # commit the change
    conn.commit()
    conn.close()


def get_next_new_material(num_new_words_to_learn):
    """
    Assume all study material before are consecutively selected, then the next new materials will be the last date's
    new material + 1 until last date's new material + n
    :param num_new_words_to_learn:
    :return: the begin rank and end rank for the new materials
    """
    BLOB_of_empty_list = pickle.dumps([])
    query = f"""SELECT *
                FROM {study_progress_table}
                WHERE NOT {new_material_col_name} = ?
                ORDER BY unixepoch({date_string_col_name}) DESC
                LIMIT 1;
            """
    conn = sqlite3.connect(my_database)
    cursor = conn.cursor()
    cursor.execute(query, (BLOB_of_empty_list,))
    row_latest_progress = cursor.fetchone()
    if row_latest_progress:
        new_material = _deserialize_rows_sqlite(row_latest_progress)[1]
        last_studied_rank = new_material[1]
        return last_studied_rank + 1, last_studied_rank + num_new_words_to_learn
    # in the extreme cases where there is no studied list
    return 1, num_new_words_to_learn


def recited_material_of_date(recited_material_date_string):
    """
    You can recite material on day that doesn't have materials, it will still record it in the database.
    :param recited_material_date_string: The date string must be in form %Y-%m-%d
    :return:
    """
    update_study_progress(recited_material_date_string, being_recited_on_date={datetime.now().strftime("%Y-%m-%d")})
    update_study_progress(datetime.now().strftime("%Y-%m-%d"), recited_material={recited_material_date_string})


def format_date_string(datetime_obj):
    return datetime_obj.strftime("%Y-%m-%d")


def get_study_progress_df():
    conn = sqlite3.connect(my_database)
    query = f"SELECT * FROM {study_progress_table} ORDER BY unixepoch({date_string_col_name});"
    df = pd.read_sql_query(query, conn)
    df.apply(_deserialize_rows_pandas, axis=1)
    conn.close()
    return df


#######################################################################################################################
#######################################################################################################################
########################################################## helpers ####################################################
#######################################################################################################################
#######################################################################################################################
def _deserialize_rows_sqlite(row):
    """
    This function deserialize a row of table study_progress, the row is obtained from sqlite3
    :param row: a tuple of (date_str, new_material_BLOB, recited_material_BLOB, being_recited_on_date_BLOB)
    :return:
    """
    date_str = row[0]
    new_material = pickle.loads(row[1])
    recited_material = pickle.loads(row[2])
    being_recited_on_date = pickle.loads(row[3])
    return date_str, new_material, recited_material, being_recited_on_date


def _deserialize_rows_pandas(row):
    """
    This function deserialize a row of table study_progress, the row is obtained from pandas

    :param row:
    :return:
    """
    row.iloc[1] = pickle.loads(row.iloc[1])
    row.iloc[2] = pickle.loads(row.iloc[2])
    row.iloc[3] = pickle.loads(row.iloc[3])
    return row


def _serialized_rows(date_str, new_material, recited_material, being_recited_on_date):
    """
    This function serialize a row of table study_progress
    :param date_str:
    :param new_material:
    :param recited_material:
    :param being_recited_on_date:
    :return:
    """
    new_material_BLOB = pickle.dumps(new_material)
    recited_material_BLOB = pickle.dumps(recited_material)
    being_recited_on_date_BLOB = pickle.dumps(being_recited_on_date)
    return date_str, new_material_BLOB, recited_material_BLOB, being_recited_on_date_BLOB


def _rules_for_updating_tables(new_material, exist_new_material,
                               recited_material, exist_recited_material,
                               being_recited_on_date, exist_being_recited_on_date,
                               override):
    if not override:
        # parameter check: existed ones will not be None
        if new_material is None:
            new_material = []
        if recited_material is None:
            recited_material = set()
        if being_recited_on_date is None:
            being_recited_on_date = set()
        # add to new/recited_material
        new_material = _combine_new_material(exist_new_material, new_material)
        recited_material = recited_material | exist_recited_material
        being_recited_on_date = being_recited_on_date | exist_being_recited_on_date
    else:  # override
        if new_material is None:  # else new material
            new_material = exist_new_material
        if recited_material is None:
            recited_material = exist_recited_material
        if being_recited_on_date is None:
            being_recited_on_date = exist_being_recited_on_date
    return new_material, recited_material, being_recited_on_date


def _combine_new_material(exist_new_material, new_material):
    """
    the new new_material must be consecutive to the old one, else the result will be unpredicted!!!
    e.g. if the old one is [20, 30] then the new one must be [20<=x<30, y] or [x, 20<=y<30] or [20<=x<30, 20<=y<30]
    and the resulting new list will be [1, x]
    if the old one is [], then the new one will replace the old one.
    :param exist_new_material: a list of [begin_rank, end_rank] or []
    :param new_material: a list of [begin_rank, end_rank] or []
    :return:
    """
    if not exist_new_material:  # if they are empty set or empty list
        return new_material
    if not new_material:
        return exist_new_material
    new_begin = min(exist_new_material[0], new_material[0])
    new_end = max(exist_new_material[1], new_material[1])
    # useless fool safe
    if new_end <= 0:
        new_end = 1
    if new_begin <= 0:
        new_begin = 1
    return [new_begin, new_end]


