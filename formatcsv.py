csv = open("result.csv", "rt").readlines()
# remove first "IP,Delay,Jitter"
csv.pop(0)

# list[[ip,latency,jitter]]
rows = map(lambda r: r.strip().split(","), csv)

# sort by latency: [1]
# to sort by jitter use                  [2]
rows = sorted(list(rows), key=lambda x: x[1])

# push space
formatted = "____________________________________\n|IP                 Delay    Jitter|\n"
for row in rows:
    ip = row[0]+((18-len(row[0]))*" ")
    latency = row[1]+((8-len(row[1]))*" ")
    jitter = row[2]+"    "
    formatted += f"|{ip} {latency} {jitter}|\n"
formatted += "____________________________________"

print(formatted)