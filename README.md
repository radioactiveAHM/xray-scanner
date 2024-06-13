# xray-scanner

## آموزش Windows

1. نصب پایتون ورژن 3.12 یا 3.11
2. نصب ماژول‌های مورد نیاز با اجرای دستورات زیر:
    1. `pip install httpx`
    2. `pip install httpx[socks]`
    3. `pip install asyncio`
3. از کانفیگ خود در نرم‌افزار V2rayN خروجی JSON بگیرید و محتوای آن را در فایل `main.json` قرار دهید.
4. اسکریپت پایتون مورد نظر را با استفاده از دستورات زیر اجرا کنید:
    * `python cleanip.py`
    * `python useip.py`
    * `python host.py`
    * `python tls.py`

## نکات

* نرم افزار V2rayN غیرفعال باشد هنگام اجرای اسکریپت
