# run -c config

from asyncio import create_subprocess_exec, sleep, run
from requests import get
from json import loads, dumps


def configer(domain):
    main_config = loads(open("./main.json", "rt").read())
    outbound = loads(open("./outbound.json", "rt").read())

    # set domain
    for vnex in outbound["settings"]["vnext"]:
        vnex["address"] = domain

    # add outbound in main config
    main_config["outbounds"].append(outbound)

    open("./config.json", "wt").write(dumps(main_config))


async def main():
    domains = open("./domains.csv", "rt").read().split("\n")
    result = open("./result", "at")

    for d in domains:
        # generate config file
        domain = d.strip()
        configer(domain)

        # run xray with config
        xray = await create_subprocess_exec("./xray.exe")

        try:
            req = get(
                "http://cp.cloudflare.com/",
                proxies={"http": "http://127.0.0.1:10809"},
                timeout=3,
            )
            if req.status_code == 204:
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
