from pfaas import gfaas

@gfaas
def hello(msg):
    return msg.upper()

if __name__ == '__main__':
    msg = "hey there, yagna!"
    resp = hello(msg)
    print("in={}, out={}".format(msg, resp))

