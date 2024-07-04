from asyncio import create_subprocess_exec, run, sleep
from json import loads, dumps
from random import randint
from os.path import isfile
from httpx import AsyncClient, Timeout

# Script config
calc_jitter = True
count = 300
get_timeout = 0.7
connect_timeout = 0.7

async def jitter_f(port):
    latencies = []
    for _ in range(5):
        try:
            async with AsyncClient(proxy=f'socks5://127.0.0.1:{port}', timeout=Timeout(get_timeout, connect=connect_timeout)) as client:
                resp = await client.get("http://cp.cloudflare.com/")
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


def configer(ip):
    main_config = loads(open("./main.json", "rt").read())

    # set domain
    for vnex in main_config["outbounds"][0]["settings"]["vnext"]:
        vnex["address"] = ip

    open("./config.json", "wt").write(dumps(main_config))

def findport()->int:
    with open("./main.json", "rt") as config_file:
        for inbound in loads(config_file.read())["inbounds"]:
            if inbound["protocol"]=="socks":
                return inbound["port"]
    
    raise "Socks inbound required!"

async def main():
    port = findport()
    domains = open("./ipv6.txt", "rt").read().split("\n")
    
    if isfile("./result.csv"):
        result = open("./result.csv", "at")
    else:
        result = open("./result.csv", "at")
        result.write("IP,Delay,Jitter\r")

    for _ in range(count):
        # generate config file
        try:
            variant = ["","1","2","3","4","5","6","7","8","9","a","b","c","d","f"]
            n1 = variant[randint(0,len(variant))]
            n2 = variant[randint(0,len(variant))]
            n3 = variant[randint(0,len(variant))]
            n4 = variant[randint(0,len(variant))]
            ip = domains[randint(0, len(domains))].strip()+n1+n2+n3+n4
        except: # noqa: E722
            continue
        configer(ip)

        # run xray with config
        xray = await create_subprocess_exec("./xray.exe")

        try:
            # httpx client using proxy to xray socks
            async with AsyncClient(proxy=f'socks5://127.0.0.1:{port}', timeout=Timeout(get_timeout, connect=connect_timeout)) as client:
                req = await client.get(url="http://cp.cloudflare.com/")
                if req.status_code == 204 or req.status_code == 200:
                    jitter = ""
                    if calc_jitter:
                        jitter = await jitter_f(port)
                        if jitter == 0.0:
                            jitter = "JAMMED"
                    latency = req.elapsed.microseconds
                    result.write(f"{ip},{int(latency/1000)},{jitter}\n")
                    print(f"{ip},{int(latency/1000)},{jitter}")
        except:  # noqa: E722
            print(f"{ip},Timeout\n")

        # kill the xray
        xray.terminate()
        xray.kill()

        await sleep(1.0)


run(main())
