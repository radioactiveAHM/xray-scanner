csv = open("result.csv", "rt").readlines()
# remove first "IP,Delay,Jitter"
csv.pop(0)

# list[[ip,latency,jitter]]
rows = list(map(lambda r: r.strip().split(","), csv))

# if using domain or ipv6 find longest string
longest = 0
for q1 in rows:
    if len(q1[0]) > longest:
        longest = len(q1[0])

# sort by latency: [1]
# to sort by jitter use                  [2]
rows = sorted(rows, key=lambda x: x[1])

# push space
formatted = ("_"*longest)+"__________________\n|IP"+(" "*(longest-1))+"Delay    Jitter|\n"
for row in rows:
    ip = row[0]+((longest-len(row[0]))*" ")
    latency = row[1]+((8-len(row[1]))*" ")
    jitter = row[2]+((6-len(row[2]))*" ")
    formatted += f"|{ip} {latency} {jitter}|\n"
formatted += ("_"*longest) +"__________________"

print(formatted)