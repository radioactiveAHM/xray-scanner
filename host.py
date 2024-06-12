# run -c config

from asyncio import create_subprocess_exec, sleep, run
from requests import get
from json import loads, dumps
from random import randint


def configer(domain):
    main_config = loads(open("./main.json", "rt").read())
    outbound = loads(open("./outbound.json", "rt").read())

    # set domain
    # types: tcp, ws, http-upgrade
    match outbound["streamSettings"]["network"]:
        case "tcp":
            outbound["streamSettings"]["tcpSettings"]["header"]["request"]["headers"][
                "Host"
            ] = domain
        case "ws":
            outbound["streamSettings"]["wsSettings"]["headers"]["Host"] = domain
        case "httpupgrade":
            outbound["streamSettings"]["httpupgradeSettings"]["host"] = domain

    # add outbound in main config
    main_config["outbounds"].append(outbound)

    open("./config.json", "wt").write(dumps(main_config))


async def main():
    domains = open("./domains.csv", "rt").read().split("\n")
    result = open("./result", "at")

    for _ in range(50):
        # generate config file
        domain = domains[randint(0,len(domains))].strip()
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
