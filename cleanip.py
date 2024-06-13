# run -c config

from asyncio import create_subprocess_exec, sleep, run
from json import loads, dumps
from random import randint
from os.path import isfile
from httpx import Client

def jitter_f():
    latencies = []
    for _ in range(5):
        try:
            client = Client(proxy='socks5://127.0.0.1:10808')
            resp = client.get(url="https://www.google.com/generate_204")
            latencies.append(resp.elapsed.microseconds / 1000)
        except:  # noqa: E722
            return 0.0

    # all request success
    sum = 0.0
    for latency in latencies:
        sum += latency
    average = sum / len(latencies)
    zigma = 0.0
    for latency in latencies:
        zigma += abs(latency - average)

    return int(zigma / len(latencies))


def configer(domain):
    main_config = loads(open("./main.json", "rt").read())

    # set domain
    for vnex in main_config["outbounds"][0]["settings"]["vnext"]:
        vnex["address"] = domain

    open("./config.json", "wt").write(dumps(main_config))


async def main():
    calc_jitter = True
    domains = open("./domains.txt", "rt").read().split("\n")

    if isfile("./result.csv"):
        result = open("./result.csv", "at")
    else:
        result = open("./result.csv", "at")
        result.write("Domain,Delay,Jitter\r")

    for _ in range(50):
        # generate config file
        try:
            domain = domains[randint(0, len(domains))].strip()
        except: # noqa: E722
            continue
        configer(domain)

        # run xray with config
        xray = await create_subprocess_exec("./xray.exe")

        try:
            # httpx client using proxy to xray socks
            client = Client(proxy='socks5://127.0.0.1:10808')
            req = client.get(url="https://www.google.com/generate_204")
            if req.status_code == 204 or req.status_code == 200:
                jitter = ""
                if calc_jitter:
                    jitter = jitter_f()
                    if jitter == 0.0:
                        jitter = "JAMMED"
                latency = req.elapsed.microseconds
                result.write(f"{domain},{int(latency/1000)},{jitter}\n")
                print(f"{domain},{int(latency/1000)},{jitter}")
        except:  # noqa: E722
            print(f"{domain},Timeout\n")

        # kill the xray
        xray.terminate()
        xray.kill()

        await sleep(1.0)


run(main())
