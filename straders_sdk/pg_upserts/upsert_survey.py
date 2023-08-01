from ..models import Survey

import logging
import datetime


def _upsert_survey(connection, survey: Survey):
    sql = """insert into survey (signature, waypoint, expiration, size)
    values (%s, %s, %s, %s) on conflict (signature) do nothing"""

    cur = connection.cursor()
    cur.execute(sql, (survey.signature, survey.symbol, survey.expiration, survey.size))

    sql = """insert into survey_deposit (signature, symbol, count) values (%s, %s, %s) on conflict (signature, symbol) do nothing"""
    deposits = survey.deposits
    deposits: list
    for deposit in survey.deposits:
        count = deposits.count(deposit)
        cur.execute(sql, (survey.signature, deposit.symbol, count))
