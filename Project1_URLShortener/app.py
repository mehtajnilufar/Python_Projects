import pyshorteners

def shorten_url():
    print(" Simple URL Shortener ")
    long_url = input("Enter the URL you want to shorten: ")
    
    shortener = pyshorteners.Shortener()
    short_url = shortener.tinyurl.short(long_url)
    
    print(f"\n Shortened URL: {short_url}")

if __name__ == "__main__":
    shorten_url()

