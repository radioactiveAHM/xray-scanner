from asyncio import create_subprocess_exec, run, sleep
from json import loads, dumps
from random import shuffle
from httpx import AsyncClient, Timeout
from time import perf_counter
from os import devnull, makedirs
import aiofiles
from datetime import datetime
import socketserver

# Script config
list_file="./domains.txt"
calc_jitter = True
shuffle_up = True
get_timeout = 1.0
connect_timeout = 1.0

#Result file naming
current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
result_filename = f"./results/result_{current_datetime}.csv"
# Ensure the results directory exists
makedirs("./results", exist_ok=True)

async def jitter_f(client):
    latencies = []
    try:
        for _ in range(5):
            stime = perf_counter()
            resp = await client.get("https://www.gstatic.com/generate_204")
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

async def configer(domain, port):
    async with aiofiles.open("./main.json", "rt") as main_config_file:
        main_config = loads(await main_config_file.read())

    # set domain
    for vnex in main_config["outbounds"][0]["settings"]["vnext"]:
        vnex["address"] = domain
    main_config["inbounds"][0]["port"] = port # Add the free port to the config

    async with aiofiles.open("./config.json", "wt") as config_file:
        await config_file.write(dumps(main_config))

def get_free_port() -> int:
    """returns a free port"""
    with socketserver.TCPServer(("localhost", 0), None) as s:
        return s.server_address[1]

async def main():
    port = get_free_port()
    async with aiofiles.open(list_file, "rt") as domains_file:
        domains = await domains_file.read()
    domains = domains.split("\n")
        
    if shuffle_up:
        shuffle(domains)
    
    try:
        async with aiofiles.open(result_filename, "a+") as result_file:
            if await result_file.tell() == 0:
                await result_file.write("Domain,Delay,Jitter\r")

        for domain in domains:
            # generate config file
            try:
                await configer(domain.strip(),port)
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
                    req = await client.get(url="https://www.gstatic.com/generate_204")
                    etime = perf_counter()
                    if req.status_code == 204 or req.status_code == 200:
                        jitter = ""
                        if calc_jitter:
                            jitter, fLatency = await jitter_f(client)
                            if jitter == 0.0:
                                jitter = "JAMMED"
                        latency = etime - stime
                        async with aiofiles.open(result_filename, "a") as result_file:
                            await result_file.write(f"{domain},{int(latency*1000)},{jitter}\n")
                        print(f"{domain} Latency:{int(latency*1000)} Jitter:{jitter}")
                        print("jitter latencies= ",fLatency)
            except:  # noqa: E722
                print(f"{domain} Timeout")
    
            if xray.returncode is None:  # Check if process is still running
                try:
                    xray.terminate()
                    await xray.wait()
                except ProcessLookupError:
                    print(f"Process already terminated or port is busy.")
                except Exception as e:
                    print(f"Failed to terminate process {e}")
                    xray.kill()  # Kill process if termination fail
    
            await sleep(0.1)
    except KeyboardInterrupt:
        print("\nScript interrupted! Saving progress...")

run(main())
