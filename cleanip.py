from asyncio import create_subprocess_exec, run, sleep
from json import loads, dumps
from random import shuffle
from os.path import isfile
from httpx import AsyncClient, Timeout
from time import perf_counter

# Script config
calc_jitter = True
get_timeout = 1.0
connect_timeout = 1.0

async def jitter_f(client):
    latencies = []
    try:
        for _ in range(5):
            stime = perf_counter()
            resp = await client.get("http://cp.cloudflare.com/")
            etime = perf_counter()
            if resp.status_code == 204 or resp.status_code == 200:
                latencies.append(int((etime - stime)*1000))
    except:  # noqa: E722
        return 0.0
    print("jitter latencies= ",latencies)

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

def findport()->int:
    with open("./main.json", "rt") as config_file:
        for inbound in loads(config_file.read())["inbounds"]:
            if inbound["protocol"]=="socks":
                return inbound["port"]
    
    raise "Socks inbound required!"

async def main():
    port = findport()
    domains = open("./domains.txt", "rt").read().split("\n")
    shuffle(domains)
    
    if isfile("./result.csv"):
        result = open("./result.csv", "at")
    else:
        result = open("./result.csv", "at")
        result.write("Domain,Delay,Jitter\r")

    for domain in domains:
        # generate config file
        try:
            configer(domain.strip())
        except: # noqa: E722
            continue

        # run xray with config
        xray = await create_subprocess_exec(
            "./xray.exe",
            stdout=open(devnull, 'wb'),
            stderr=open(devnull, 'wb')
        )

        try:
            # httpx client using proxy to xray socks
            async with AsyncClient(proxy=f'socks5://127.0.0.1:{port}', timeout=Timeout(get_timeout, connect=connect_timeout)) as client:
                stime = perf_counter()
                req = await client.get(url="http://cp.cloudflare.com/")
                etime = perf_counter()
                if req.status_code == 204 or req.status_code == 200:
                    jitter = ""
                    if calc_jitter:
                        jitter = await jitter_f(client)
                        if jitter == 0.0:
                            jitter = "JAMMED"
                    latency = etime - stime
                    result.write(f"{domain},{int(latency*1000)},{jitter}\n")
                    print(f"{domain},{int(latency*1000)},{jitter}")
        except:  # noqa: E722
            print(f"{domain},Timeout\n")

        # kill the xray
        xray.terminate()
        xray.kill()

        await sleep(0.1)


run(main())
