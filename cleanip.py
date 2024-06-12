# run -c config

from asyncio import create_subprocess_exec, sleep, run
from requests import get
from json import loads, dumps
from random import randint


def jitter_f():
    latencies = []

    for _ in range(5):
        try:
            resp = get(
                "https://www.google.com/generate_204",
                proxies={"http": "http://127.0.0.1:10809"},
                timeout=3,
            )
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

    return zigma / len(latencies)


def configer(domain):
    main_config = loads(open("./main.json", "rt").read())

    # set domain
    for vnex in main_config["outbounds"][0]["settings"]["vnext"]:
        vnex["address"] = domain

    open("./config.json", "wt").write(dumps(main_config))


async def main():
    calc_jitter = True
    domains = open("./domains.csv", "rt").read().split("\n")
    result = open("./result", "at")

    for _ in range(50):
        # generate config file
        domain = domains[randint(0, len(domains))].strip()
        configer(domain)

        # run xray with config
        xray = await create_subprocess_exec("./xray.exe")

        try:
            req = get(
                "https://www.google.com/generate_204",
                proxies={"http": "http://127.0.0.1:10809"},
                timeout=3,
            )
            if req.status_code == 204 or req.status_code == 200:
                jitter = ""
                if calc_jitter:
                    jitter = jitter_f()
                    if jitter == 0.0:
                        jitter = "JAMMED"
                    else:
                        str(jitter)
                latency = req.elapsed.microseconds
                result.write(f"{domain}\t{latency/1000}\t{jitter}\n")
                print(f"{domain}\t{latency/1000}\t{jitter}")
        except:  # noqa: E722
            result.write(f"{domain}\tTimeout\n")
            print(f"{domain}\tTimeout\n")

        # kill the xray
        xray.terminate()
        xray.kill()

        await sleep(1.0)


run(main())
