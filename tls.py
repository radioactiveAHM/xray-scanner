# run -c config

from asyncio import create_subprocess_exec, sleep, run
from json import loads, dumps
from random import randint
from httpx import Client

def configer(domain):
    main_config = loads(open("./main.json", "rt").read())

    # set sni
    main_config["outbounds"][0]["streamSettings"]["tlsSettings"]["allowInsecure"] = True
    main_config["outbounds"][0]["streamSettings"]["tlsSettings"]["serverName"] = domain

    open("./config.json", "wt").write(dumps(main_config))


async def main():
    domains = open("./domains.txt", "rt").read().split("\n")
    result = open("./result", "at")

    for _ in range(50):
        # generate config file
        try:
            domain = domains[randint(0,len(domains))].strip()
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
                latency = req.elapsed.microseconds
                result.write(f"{domain}\t{latency/1000}\n")
                print(f"{domain}\t{latency/1000}")
        except:  # noqa: E722
            result.write(f"{domain}\tTimeout\n")
            print(f"{domain}\tTimeout\n")

        # kill the xray
        xray.terminate()
        xray.kill()

        await sleep(1.0)


run(main())
