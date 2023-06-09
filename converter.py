import uvicorn
from fastapi import FastAPI, HTTPException
import psycopg2


app = FastAPI()

conn = psycopg2.connect(
    database="db",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)


def convert_rate(source: str, target: str, sum: int):
    cur = conn.cursor()
    cur.execute("""
                    select %(sum)s * crv.rate 
                    from currency_rates cr 
                    join currency_rates_values crv on cr.id = crv.currency_rate_id
                    where 
                        cr.base_currency = %(source)s 
                        and crv.currency_code = %(target)s
                """, {"sum": sum, "target": target, "source": source})
    return cur.fetchone()


@app.get("/convert")
async def convert_get(baseCurrency: str, convertedCurrncy: str, sum: float):
    try:
        return {"converted": convert_rate(source=baseCurrency, target=convertedCurrncy, sum=sum)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Не удалось сконвертировать валюты")


if __name__ == '__main__':
    uvicorn.run(app, port=10604, host='localhost')