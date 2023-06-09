from typing import List
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2 as pg
import re


app = FastAPI()

conn = pg.connect(
    database="db",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)


class Converted(BaseModel):
    code: str
    rate: float


class RequestBody(BaseModel):
    baseCurrency: str
    rates: List[Converted]


def select_one_currency(currency_name):
    cur = conn.cursor()
    cur.execute("""SELECT id FROM currency_rates 
                WHERE base_currency = %s""", (currency_name,))
    data_id = cur.fetchall()
    data_id = re.sub(r"[^0-9]", r"", str(data_id))
    print(data_id)
    return(data_id)


def select_only_rate(currency_code):
    id = select_one_currency(currency_code)
    cur = conn.cursor()
    cur.execute("""SELECT rate FROM currency_rates_values 
                WHERE currency_rate_id = %s""", (id,))
    data_id = cur.fetchall()
    data_id = re.sub(r"[^0-9]", r"", str(data_id))
    return(data_id)


@app.post("/load")
async def load_post(RequestBody: RequestBody):
    currency_name = RequestBody.baseCurrency
    rates = RequestBody.rates
    print(currency_name)
    print(rates)
    one_cur = select_one_currency(currency_name)

    try:
        one_cur == []
        cur = conn.cursor()
        cur.execute("""INSERT INTO currency_rates (base_currency) 
                    VALUES (%s)""", (currency_name,))
        one_cur = select_one_currency(currency_name)
        print(one_cur)
        for i in rates:
            cur = conn.cursor()
            cur.execute("""INSERT INTO currency_rates_values (currency_code, rate, currency_rate_id) 
                            VALUES (%s, %s, %s)""", (i.code, i.rate, one_cur,))
        conn.commit()
        raise HTTPException(200)
    except:
        raise HTTPException(500)


if __name__ == '__main__':
    uvicorn.run(app, port=10640, host='localhost')