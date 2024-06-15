from asyncio import create_subprocess_exec, run, sleep, create_task, Lock
from json import loads, dumps
from random import randint
from os.path import isfile
from httpx import AsyncClient, Timeout

# Script config
calc_jitter = True
count = 50
get_timeout = 2.0
connect_timeout = 5.0
tasks = 3

# global result file handling with mutex(Lock)
if isfile("./result.csv"):
    result = open("./result.csv", "at")
else:
    result = open("./result.csv", "at")
    result.write("IP,Delay,Jitter\r")

# mutex lock
lock = Lock()

async def jitter_f(port):
    latencies = []
    for _ in range(5):
        try:
            async with AsyncClient(proxy=f'socks5://127.0.0.1:{port}', timeout=Timeout(get_timeout, connect=connect_timeout)) as client:
                resp = await client.get("https://www.google.com/generate_204")
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


def configer(ip, id, socks_port, http_port):
    main_config = loads(open("./main.json", "rt").read())

    # set port
    main_config["inbounds"][0]["port"] = socks_port
    main_config["inbounds"][1]["port"] = http_port


    # set domain
    for vnex in main_config["outbounds"][0]["settings"]["vnext"]:
        vnex["address"] = ip

    open(f"./config{id}.json", "wt").write(dumps(main_config))

async def scan(id):

    socks_port = randint(4000, 5000)
    http_port = randint(4000, 5000)
    domains = open("./ipv4.txt", "rt").read().split("\n")

    for _ in range(count):
        # generate config file
        try:
            ip = domains[randint(0, len(domains))].strip().replace("0/24", str(randint(0,255)))
        except: # noqa: E722
            continue
        configer(ip, id, socks_port, http_port)

        # run xray with config
        xray = await create_subprocess_exec("./xray.exe", "run", "-c", f"config{id}.json")

        try:
            # httpx client using proxy to xray socks
            async with AsyncClient(proxy=f'socks5://127.0.0.1:{socks_port}', timeout=Timeout(get_timeout, connect=connect_timeout)) as client:
                req = await client.get(url="https://www.google.com/generate_204")
                if req.status_code == 204 or req.status_code == 200:
                    jitter = ""
                    if calc_jitter:
                        jitter = await jitter_f(socks_port)
                        if jitter == 0.0:
                            jitter = "JAMMED"
                    latency = req.elapsed.microseconds
                    # lock to write to result file
                    async with lock:
                        result.write(f"{ip},{int(latency/1000)},{jitter}\n")
                    print(f"{ip},{int(latency/1000)},{jitter}")
        except:  # noqa: E722
            print(f"{ip},Timeout\n")

        # kill the xray
        xray.terminate()
        xray.kill()

        await sleep(1.0)

async def main():
    tasks_holder = []
    for id in range(tasks):
        tasks_holder.append(create_task(scan(id)))
    
    for task in tasks_holder:
        await task


run(main())
