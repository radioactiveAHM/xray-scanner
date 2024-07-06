from asyncio import create_subprocess_exec, run, sleep
from json import loads, dumps
from random import randint
from os.path import isfile
from httpx import AsyncClient, Timeout
from time import perf_counter
from os import system

# Script config
calc_jitter = True
scan = 50
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


def configer(ip):
    main_config = loads(open("./main.json", "rt").read())

    # set ip
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
    ips = open("./ipv4.txt", "rt").read().split("\n")
    
    if isfile("./result.csv"):
        result = open("./result.csv", "at")
    else:
        result = open("./result.csv", "at")
        result.write("IP,Delay,Jitter\r")

    found = 0
    timeout = 0
    for _ in range(scan):
        system("cls")
        print(f"Found= {found}\tTimeout= {timeout}\n\n")
        # generate config file
        try:
            ip = ips[randint(0,len(ips))].strip().replace("0/24", str(randint(0,255)))
            configer(ip)
        except:  # noqa: E722
            continue

        # run xray with config
        xray = await create_subprocess_exec("./xray.exe")

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
                    result.write(f"{ip},{int(latency*1000)},{jitter}\n")
                    print(f"{ip},{int(latency*1000)},{jitter}")
                    found += 1
        except:  # noqa: E722
            timeout += 1
            print(f"{ip},Timeout\n")

        # kill the xray
        xray.terminate()
        xray.kill()

        await sleep(0.1)


run(main())
