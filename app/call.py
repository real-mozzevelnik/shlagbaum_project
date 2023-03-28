import requests
# from app.config import PHONE_NUM
PHONE_NUM = "(967) 513-34-20"
def c():
    return requests.post('https://zvonok.com/api/v1/callback-form/',
    params={"to": PHONE_NUM}
    )

