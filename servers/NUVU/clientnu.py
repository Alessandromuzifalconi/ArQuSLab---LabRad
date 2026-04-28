from labrad import connect

cxn = connect()

cam = cxn.emccd

print(cxn.servers)

