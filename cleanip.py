from asyncio import create_subprocess_exec, run, sleep
from json import loads, dumps
from random import shuffle
from httpx import AsyncClient, Timeout
from time import perf_counter
from os import devnull, makedirs
import aiofiles
from datetime import datetime

# Script config
calc_jitter = True
get_timeout = 1.0
connect_timeout = 1.0
#Result file naming
current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
result_filename = f"./results/result_{current_datetime}.csv"

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
    fLatency=latencies

    # all request success
    sum = 0.0
    for latency in latencies:
        sum += latency
    average = sum / len(latencies)
    zigma = 0.0
    for latency in latencies:
        zigma += abs(latency - average)

    return int(zigma / len(latencies)),fLatency

async def configer(domain):
    async with aiofiles.open("./main.json", "rt") as main_config_file:
        main_config = loads(await main_config_file.read())

    # set domain
    for vnex in main_config["outbounds"][0]["settings"]["vnext"]:
        vnex["address"] = domain

    async with aiofiles.open("./config.json", "wt") as config_file:
        await config_file.write(dumps(main_config))

def findport()->int:
    with open("./main.json", "rt") as config_file:
        for inbound in loads(config_file.read())["inbounds"]:
            if inbound["protocol"]=="socks":
                return inbound["port"]
    
    raise "Socks inbound required!"

async def main():
    port = findport()
    async with aiofiles.open("./domains.txt", "rt") as domains_file:
        domains = await domains_file.read()
    domains = domains.split("\n")
    shuffle(domains)
    
    try:
        async with aiofiles.open(result_filename, "a+") as result_file:
            if await result_file.tell() == 0:
                await result_file.write("Domain,Delay,Jitter\r")

        for domain in domains:
            # generate config file
            try:
                await configer(domain.strip())
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
                            jitter, fLatency = await jitter_f(client)
                            if jitter == 0.0:
                                jitter = "JAMMED"
                        latency = etime - stime
                        async with aiofiles.open("./result.csv", "a") as result_file:
                            await result_file.write(f"{domain},{int(latency*1000)},{jitter}\n")
                        print(f"{domain} Latency:{int(latency*1000)} Jitter:{jitter}")
                        print("jitter latencies= ",fLatency)
            except:  # noqa: E722
                print(f"{domain} Timeout")
    
            # kill the xray
            xray.terminate()
            xray.kill()
    
            await sleep(0.1)
    except KeyboardInterrupt:
        print("\nScript interrupted! Saving progress...")

run(main())
