import time

def get_time():
    time_str = time.strftime("%Y{}%m{}%d %X")
    return time_str.format("/","/")
    pass

if __name__=="__main__":
    print(get_time())